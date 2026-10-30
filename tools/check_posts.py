#!/usr/bin/env python3
"""投稿チェック(毎回の確認と、失敗した投稿の手動補填)。

使い方:  python3 -I tools/check_posts.py [--fix] [--date YYYY-MM-DD]
- トークンは環境変数 THREADS_TOKEN_R / THREADS_TOKEN_Y から読む(ファイル・出力には書かない)。
- 今日(JST)の予定枠のうち、時刻が過ぎたものについて、Threadsに投稿されたかを確認する。
- --fix のとき、承認済みドラフトがあるのに未投稿の枠を投稿する(PRはリンクのリプライも)。
  朝あいさつは、予定時刻から4時間以内のみ補填。それ以外の枠は、枠の終了から6時間以内のみ補填。
- 投稿済みなのに approved に残っているファイルは、posted へ git mv する(コミットは呼び出し側)。
"""
import os,sys,json,re,time,subprocess,urllib.request,urllib.parse,datetime as dt
R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
B='https://graph.threads.com/v1.0'
BOTS={'一般':('rakuten-threads-bot','THREADS_TOKEN_R'),'ゆず':('shibainu-yuzu-bot','THREADS_TOKEN_Y')}
# (枠名, ファイル種別, 予定開始, 窓の終わり, 補填できる期限(窓の終わりからの時間))
SLOTS=[('朝','greeting',(6,0),(6,40),4),('昼','noon',(11,45),(12,45),6),('15時台','tweet',(15,0),(15,15),6),
       ('夕方','evening',(18,0),(18,15),6),('20時台','late',(20,15),(20,45),6),('夜','night',(21,15),(22,45),6)]
def call(method,path,tok,**p):
    p['access_token']=tok
    req=urllib.request.Request(B+path+'?'+urllib.parse.urlencode(p)) if method=='GET' else urllib.request.Request(B+path,data=urllib.parse.urlencode(p).encode(),method='POST')
    for _ in range(3):
        try:return json.load(urllib.request.urlopen(req,timeout=30))
        except urllib.error.HTTPError as e:return {'error':e.read().decode()[:200]}
        except Exception:time.sleep(2)
    return {'error':'fail'}
def body_of(kind,s):
    if kind=='greeting':
        for k in ('## 本文\n\n','---\n\n'):
            if k in s:return s.split(k,1)[1].strip(),None
    if kind in('tweet','late'):
        return s.split('### 本文\n',1)[1].strip(),None
    p1=s.split('### 1件目(本体)\n',1)[1].split('\n### 2件目',1)[0].strip()
    p2=s.split('### 2件目(リプライ)\n',1)[1].strip() if '### 2件目' in s else None
    return p1,p2
def find_file(bot,kind,date):
    sub=lambda d:f'{R}/{bot}/state/{d}'
    if kind=='greeting':
        cands=[(sub('morning_greeting/approved')+f'/{date}.md','approved'),(sub('morning_greeting/posted')+f'/{date}.md','posted')]
    else:
        cands=[(sub('approved_drafts')+f'/{date}-{kind}.md','approved'),(sub('posted_drafts')+f'/{date}-{kind}.md','posted')]
    for fp,st in cands:
        if os.path.exists(fp):return fp,st
    return None,None
def main():
    fix='--fix' in sys.argv
    now=dt.datetime.utcnow()+dt.timedelta(hours=9)
    date=now.strftime('%Y-%m-%d')
    if '--date' in sys.argv:date=sys.argv[sys.argv.index('--date')+1]
    out=[];moved=[]
    for name,(bot,env) in BOTS.items():
        tok=os.environ.get(env)
        if not tok:out.append(f'{name}: トークン未設定({env})');continue
        uid=call('GET','/me',tok,fields='id').get('id')
        posts=call('GET',f'/{uid}/threads',tok,fields='id,text,timestamp',limit=50).get('data',[])
        for slot,kind,(sh,sm),(eh,em),grace in SLOTS:
            start=dt.datetime.strptime(f'{date} {sh:02d}:{sm:02d}','%Y-%m-%d %H:%M')
            end=dt.datetime.strptime(f'{date} {eh:02d}:{em:02d}','%Y-%m-%d %H:%M')
            if now<end+dt.timedelta(minutes=10):continue   # まだ窓が終わっていない
            fp,st=find_file(bot,kind,date)
            if not fp:out.append(f'{name} {slot}: ドラフトなし(予定なし)');continue
            body,reply=body_of(kind,open(fp,encoding='utf-8').read())
            head=body[:20]
            match=[x for x in posts if (x.get('text') or '').strip().startswith(head)]
            if match:
                msg=f'{name} {slot}: 投稿済み'
                if reply:
                    rep=call('GET',f"/{match[0]['id']}/replies",tok,fields='id,text').get('data',[])
                    if not [y for y in rep if 'hb.afl.rakuten.co.jp' in (y.get('text') or '')]:
                        msg+=' / リンクのリプライなし!'
                        if fix:
                            c=call('POST',f'/{uid}/threads',tok,media_type='TEXT',text=reply,reply_to_id=match[0]['id'])
                            if 'id' in c:
                                time.sleep(3);p=call('POST',f'/{uid}/threads_publish',tok,creation_id=c['id']);msg+=' → 補填:'+('OK' if 'id' in p else str(p))
                            else:msg+=' → 補填失敗:'+str(c)
                out.append(msg)
                if st=='approved':moved.append((fp,kind,bot))
                continue
            # 未投稿
            if st=='posted':out.append(f'{name} {slot}: postedにあるがThreadsに見つからない(要確認)');continue
            limit=end+dt.timedelta(hours=grace)
            if kind=='greeting':limit=start+dt.timedelta(hours=4)
            if now>limit:out.append(f'{name} {slot}: 未投稿(補填期限を過ぎた。報告のみ)');continue
            if not fix:out.append(f'{name} {slot}: 未投稿!(--fixで補填可)');continue
            c=call('POST',f'/{uid}/threads',tok,media_type='TEXT',text=body)
            if 'id' not in c:out.append(f'{name} {slot}: 未投稿→補填失敗 {c}');continue
            time.sleep(3);p=call('POST',f'/{uid}/threads_publish',tok,creation_id=c['id'])
            if 'id' not in p:out.append(f'{name} {slot}: 補填の公開に失敗 {p}');continue
            m=f'{name} {slot}: 未投稿→手動で投稿しました'
            if reply:
                time.sleep(3);c2=call('POST',f'/{uid}/threads',tok,media_type='TEXT',text=reply,reply_to_id=p['id'])
                if 'id' in c2:
                    time.sleep(3);p2=call('POST',f'/{uid}/threads_publish',tok,creation_id=c2['id']);m+=' +リンク返信'+('OK' if 'id' in p2 else '失敗')
                else:m+=' +リンク返信失敗'
            out.append(m);moved.append((fp,kind,bot))
    for fp,kind,bot in moved:
        if '/approved' in fp:
            dst=fp.replace('/approved_drafts/','/posted_drafts/').replace('/morning_greeting/approved/','/morning_greeting/posted/')
            subprocess.run(['git','-C',R,'mv',fp,dst],capture_output=True)
            out.append(f'整理: {os.path.basename(fp)} → posted')
    print('\n'.join(out))
main()

# Threads(@shibainu_yuzu__) × 楽天アフィリエイト自動化

黒柴ゆず🍋のThreadsアカウント専用の自動投稿パイプライン。`rakuten-threads-bot` と同じ仕組みを、このアカウント向けに調整したもの(ジャンルはペット固定、ペルソナはゆずの飼い主)。

1日3つの時間帯(朝6時・昼12時・夕方18時)に自動投稿します。朝はあいさつ専用、昼と夕方は「PR型」(楽天のペット用品を紹介)または「つぶやき型」(商品紹介を含まない雑談・日常投稿)を自動で選んで投稿します。

**内容の確認は仕事中の時間帯に行い、実際の投稿だけがそれぞれの決まった時刻に自動で行われます。** ドラフトは投稿の何時間か前(あいさつは前日15:00、昼・夕方は当日9:00)に作成されます。**リマインドタスクは無し**(未承認のまま投稿時刻を迎えると静かにスキップされます)。

## セットアップ

1. `.env` は既に作成済み(`RAKUTEN_APP_ID` 等は `rakuten-threads-bot` と共通のものを使用)。**`THREADS_ACCESS_TOKEN` と `THREADS_USER_ID` はこのアカウント専用に取得して入力する必要がある**(下記参照)
2. `.env` は絶対にgit管理・共有しないこと(`.gitignore` 済み)
3. パイプラインの中身は `PIPELINE.md`(昼夕枠)と `MORNING_GREETING.md`(あいさつ枠)に全て記載

### Threadsアクセストークンの取得(このアカウント専用)

既存のMeta for Developersアプリを使って、`@shibainu_yuzu__` アカウント用の新しいトークンを発行する:

1. https://developers.facebook.com/apps/ にログインし、`rakuten-threads-bot` で使っているアプリを開く
2. Threads APIの設定画面で、新しいThreadsアカウント(`@shibainu_yuzu__`)としてログイン・認可する(既存アカウントとは別のThreadsアカウントでログインする必要がある)
3. 短期アクセストークンを取得後、長期アクセストークン(60日)に交換する
4. 交換したトークンで `GET https://graph.threads.com/v1.0/me?fields=id&access_token={トークン}` を叩き、返ってきた `id` が `THREADS_USER_ID`
5. `.env` の `THREADS_ACCESS_TOKEN` と `THREADS_USER_ID` に入力する

## 使い方

### スケジュールタスク(登録済み、`list_scheduled_tasks` で確認可能)

| taskId | 実行時刻 | 内容 |
|---|---|---|
| `yuzu-draft-noon` | 毎日9:00頃 | 当日12:00投稿の昼枠ドラフトを作成し提示(投稿はしない) |
| `yuzu-draft-evening` | 毎日9:05頃 | 当日18:00投稿の夕方枠ドラフトを作成し提示(投稿はしない) |
| `yuzu-greeting-draft` | 毎日15:00頃 | 翌朝6:00投稿のあいさつドラフトを作成し提示(投稿はしない) |
| `yuzu-greeting-post` | 毎朝6:00頃 | 承認済みのあいさつドラフトがあれば投稿 |
| `yuzu-post-noon` | 毎日12:00頃 | 承認済みの昼枠ドラフトがあれば投稿 |
| `yuzu-post-evening` | 毎日18:00頃 | 承認済みの夕方枠ドラフトがあれば投稿 |

**`THREADS_ACCESS_TOKEN` を入力するまでは、ドラフト作成・提示はできますが、実際の投稿(post系タスク)は失敗します。**

## 状態管理ファイル(`state/`)

`rakuten-threads-bot` と同じ構成(`pending_drafts/` `approved_drafts/` `posted_drafts/` `morning_greeting/pending,approved,posted/` `post_type_rotation.json` `posted_items.json`)。ジャンルが固定のため `genre_rotation.json` は無し。

## 既知の制約

- スケジュールタスクはClaude Codeアプリが開いている・PCがスリープしていない時しか実行されない。`.claude/settings.local.json` で `bypassPermissions` を設定済みなので許可ポップアップでは止まらないが、**PCのスリープ自体は防げない**ので、投稿時刻の前後はPCを起こしておくこと
- Threadsアクセストークンは60日で失効。自動更新は未実装
- レビュー本文の自動取得はできない(楽天公式APIに機能がないため)

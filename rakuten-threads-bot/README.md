# Threads × 楽天アフィリエイト自動化

1日3つの時間帯(朝6時・昼12時・夕方18時)にThreadsへ自動投稿します。朝はあいさつ専用、昼と夕方は「PR型」(楽天の売れ筋商品を紹介)または「つぶやき型」(商品紹介を含まない雑談・日常投稿)を自動で選んで投稿します。

PRばかりだと「宣伝アカウント」化して表示が抑制されたり規約違反リスクが上がるため、昼・夕方それぞれの枠でPR型とつぶやき型を自動で織り交ぜる設計になっています(デフォルトはPR型 40%程度、`state/post_type_rotation.json` の `target_pr_ratio` で調整可能)。詳細は `PIPELINE.md` の「3. 投稿タイプの決定」を参照。

朝6時のあいさつ投稿(`MORNING_GREETING.md`)は完全に別枠で、商品紹介やPRは一切含めません。「おはよう」+前向きな一言をベースに、たまに小さなTipsを添えます。

**内容の確認は仕事中の時間帯に行い、実際の投稿だけがそれぞれの決まった時刻(6:00/12:00/18:00)に自動で行われます。** ドラフトは投稿の何時間か前(あいさつは前日15:00、昼・夕方は当日9:00)に作成され、投稿直前(あいさつは前日23:00、昼は11:00、夕方は17:00)に未承認ならリマインドが来ます。

## セットアップ

1. `.env.example` を `.env` にコピーし、値を入力する
   ```bash
   cp .env.example .env
   ```
   - `RAKUTEN_APP_ID` / `RAKUTEN_ACCESS_KEY`: https://webservice.rakuten.co.jp/app/list で確認
   - `RAKUTEN_AFFILIATE_ID`: https://webservice.rakuten.co.jp/app/account_affiliate_id で確認
   - `THREADS_ACCESS_TOKEN`: 長期アクセストークン(60日で失効、切れたら再取得が必要)
   - `THREADS_USER_ID`: Threadsユーザーの数値ID

2. `.env` は絶対にgit管理・共有しないこと(`.gitignore` 済み)

3. パイプラインの中身は `PIPELINE.md`(昼・夕方枠、PR型/つぶやき型)と `MORNING_GREETING.md`(朝のあいさつ投稿、および夜のリマインド統合タスク)に全て記載。ロジックを変えたい場合はこれらのファイルを編集する

## 使い方

### スケジュールタスク(登録済み、`list_scheduled_tasks` で確認可能)

| taskId | 実行時刻 | 内容 |
|---|---|---|
| `threads-morning-greeting-draft` | 毎日15:00頃 | 翌朝6:00投稿のあいさつドラフトを作成し提示(投稿はしない) |
| `rakuten-threads-draft` | 毎日9:00頃 | 当日12:00投稿の昼枠ドラフト(PR型/つぶやき型)を作成し提示(投稿はしない) |
| `rakuten-threads-draft-evening` | 毎日9:05頃 | 当日18:00投稿の夕方枠ドラフト(PR型/つぶやき型)を作成し提示(投稿はしない) |
| `threads-morning-greeting-reminder` | 毎晩23:00頃 | あいさつドラフトが未承認なら、寝る前に一度だけ内容を再掲してリマインドする |
| `rakuten-threads-reminder-noon` | 毎日11:00頃 | 昼枠ドラフトが未承認なら、内容を再掲してリマインドする |
| `rakuten-threads-reminder-evening` | 毎日17:00頃 | 夕方枠ドラフトが未承認なら、内容を再掲してリマインドする |
| `threads-morning-greeting-post` | 毎朝6:00頃 | 承認済みのあいさつドラフトがあれば投稿。未承認なら見送った旨を知らせる |
| `rakuten-threads-post-noon` | 毎日12:00頃 | 承認済みの昼枠ドラフトがあれば投稿。未承認なら見送った旨を知らせる |
| `rakuten-threads-post-evening` | 毎日18:00頃 | 承認済みの夕方枠ドラフトがあれば投稿。未承認なら見送った旨を知らせる |

### 承認・投稿の流れ

- **あいさつ投稿(朝6時)**: 前日15:00にドラフトが提示される→「OK」で `state/morning_greeting/approved/` にキュー登録(まだ投稿しない)→ 前日23:00までに未承認ならリマインド→ 当日6:00に承認済みなら自動投稿
- **昼枠(12時)**: 当日9:00にドラフトが提示される→「OK」で `state/approved_drafts/` にキュー登録(まだ投稿しない)→ 11:00までに未承認ならリマインド→ 12:00に承認済みなら自動投稿
- **夕方枠(18時)**: 当日9:05にドラフトが提示される→「OK」で `state/approved_drafts/` にキュー登録(まだ投稿しない)→ 17:00までに未承認ならリマインド→ 18:00に承認済みなら自動投稿

いずれの枠も、投稿時刻までに承認が間に合わなかった場合はその回はスキップされ、その旨がチャットで報告されます。

## 状態管理ファイル(`state/`)

- `genre_rotation.json`: 直近使用したジャンルの記録(連続で同じジャンルにならないようにする)
- `posted_items.json`: 投稿済み商品コードの台帳(重複紹介を防ぐ)
- `post_type_rotation.json`: 昼・夕方枠のPR型/つぶやき型の投稿履歴と目標比率(`target_pr_ratio`)。3連続で同じタイプにならないよう調整しつつ、目標比率に近づける
- `pending_drafts/` / `approved_drafts/` / `posted_drafts/`: 昼・夕方枠(PR型/つぶやき型)の承認待ち・投稿待ちキュー・投稿済みドラフト(ファイル名は `{日付}-noon.md` / `{日付}-evening.md`)
- `morning_greeting/pending/` `/approved/` `/posted/`: 朝のあいさつ投稿の承認待ち・投稿待ちキュー・投稿済みアーカイブ

## 既知の制約

- スケジュールタスクはClaude Codeアプリが開いている時しか実行されない(閉じていた場合は次回起動時に実行)。投稿タスクも同様に、アプリが閉じていれば投稿が遅れる
- Threadsアクセストークンは60日で失効。自動更新は未実装(v2で検討)
- レビュー本文の自動取得はできない(楽天公式APIに機能がないため)。`reviewCount`/`reviewAverage` の集計値のみ使用
- 不安定な場合はGitHub Actions方式への切り替えを検討する(設計は別途相談済み)

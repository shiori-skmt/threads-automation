# threads-automation

Threads自動投稿パイプライン(クラウドroutine実行用)。2アカウント分を格納:

- `rakuten-threads-bot/`: 楽天アフィリエイト × Threads(30代・子育て中・犬を飼っている女性ペルソナ)
- `shibainu-yuzu-bot/`: `@shibainu_yuzu__`(黒柴ゆず)専用、ペットジャンル固定

各フォルダの `PIPELINE.md`(昼・夕方枠)と `MORNING_GREETING.md`(朝のあいさつ枠)が、クラウドのスケジュールroutineから読まれる実行指示書。`state/` 配下がroutineの実行結果(ドラフト・承認状況・投稿履歴)を保持し、routineの実行のたびに `git pull`/`git push` で読み書きする。

**このリポジトリに認証情報(APIキー・アクセストークン)は一切含まれていない。** 各routineの起動プロンプト自体に埋め込まれている(Claudeのアカウント設定内で管理)。

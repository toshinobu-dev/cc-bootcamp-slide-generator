# CCブートキャンプ スライド自動生成システム

自然言語の指示だけで、セールス用プレゼンテーションを自動生成するシステム。  
**Claude API** でスライド原稿を生成し、**GAMMA API** でプレゼンテーションを作成する。

---

## システム構成

```
input.json           # スライド生成パラメータ（サービス情報・価格・講師など）
    ↓
agent.py             # 自然言語でinput.jsonを更新するAIエージェント（オプション）
    ↓
generate_slides_v2.py
    ├─ Claude API    # スライド原稿（JSON）を生成
    └─ GAMMA API     # プレゼンテーションを生成（非同期ポーリング）
            ↓
    gamma.app の URL を出力
    generation_result.json に結果を保存
```

### ファイル一覧

| ファイル | 役割 |
|---------|------|
| `input.json` | サービス情報・価格・講師名などのパラメータ |
| `generate_slides_v2.py` | メイン生成スクリプト |
| `agent.py` | 自然言語でinput.jsonを更新するAIエージェント |
| `.env` | APIキー（Git管理外） |

---

## セットアップ

### 1. 依存ライブラリのインストール

```bash
pip3 install anthropic requests python-dotenv
```

### 2. .env ファイルの作成

デスクトップに `.env` ファイルを作成し、以下を記述する。

```
ANTHROPIC_API_KEY=sk-ant-...
GAMMA_API_KEY=sk-gamma-...
```

- **Anthropic API キー**：https://console.anthropic.com でPro以上のプランで取得
- **GAMMA API キー**：https://gamma.app の Settings → API で取得（Pro以上のプランが必要）

---

## 使い方

### パターン① 直接実行（スタンダード）

`input.json` を編集してからスクリプトを実行する。

```bash
python3 ~/Desktop/generate_slides_v2.py
```

実行すると以下の順で処理される。

1. `input.json` を読み込む
2. Claude API でスライド原稿（JSON）を生成
3. GAMMA API にプレゼンテーション生成を依頼
4. 完了までポーリング（約30〜60秒）
5. gamma.app の URL を表示

```
=== CCブートキャンプ スライド自動生成システム ===
入力データ読み込み完了: 本質のClaude Code 完全攻略 7dayブートキャンプ
Claude API でスライド内容を生成中...
13枚分のコンテンツ生成完了
GAMMA API にプレゼンテーション生成を依頼中...
generationId: xxxxxxxxxx
生成完了を待機中...
  ステータス: pending
  ステータス: completed

==================================================
生成完了！
URL: https://gamma.app/docs/xxxxxxxxxx
==================================================
```

### パターン② AIエージェント経由（自然言語で指示）

```bash
python3 ~/Desktop/agent.py
```

起動後、日本語で指示するだけで `input.json` が自動更新され、スライドが生成される。

```
=== スライド生成エージェント ===

指示を入力 > 副業したい会社員向けに13枚作って
指示を入力 > サービス名をAI副業スクールに変えて価格は98000円で
指示を入力 > ターゲットを主婦にして訴求は時短・在宅ワーク
指示を入力 > quit
```

指示に含まれていないフィールドは現在の値を引き継ぐ（差分更新）。  
更新内容の確認画面が表示され、`y` で生成が始まる。

---

## input.json パラメータ一覧

```json
{
  "service_name": "サービス・講座名",
  "concept":      "スライドのコンセプト・訴求軸",
  "target":       "ターゲット層",
  "appeal":       "訴求ポイント",
  "price":        "定価（税抜・数字のみ）",
  "discount_prime":    "プライム向け割引価格（数字のみ）",
  "discount_standard": "スタンダード向け割引価格（数字のみ）",
  "slides_count": 13,
  "instructor1":  "講師1の名前",
  "instructor2":  "講師2の名前"
}
```

---

## スライド構成（13枚固定）

| # | スライド |
|---|---------|
| 1 | 表紙（キャッチコピー） |
| 2 | 問題提起 |
| 3 | 市場機会 |
| 4 | 解決策 |
| 5 | 講師実績①（みかみ） |
| 6 | 講師実績②（佐藤将司） |
| 7 | 1期生の実績・社会的証明 |
| 8 | サービス内容 |
| 9 | 講義一覧 |
| 10 | 特典 |
| 11 | 価格 |
| 12 | 反論つぶし |
| 13 | クロージング |

---

## GAMMA テーマ

現在の設定：`canaveral`（ダーク × オレンジ系、16:9）

テーマを変更したい場合は `generate_slides_v2.py` の `themeId` を変更する。

```python
"themeId": "canaveral"   # 変更箇所
```

利用可能なテーマは GAMMA API で確認できる。

```bash
python3 -c "
from dotenv import load_dotenv; import os, requests, json
load_dotenv(os.path.expanduser('~/Desktop/.env'), override=True)
r = requests.get('https://public-api.gamma.app/v1.0/themes',
    headers={'X-API-KEY': os.environ.get('GAMMA_API_KEY')})
for t in r.json()['data']: print(t['id'], '-', t['name'])
"
```

---

## リトライ処理

Claude API・GAMMA API のリクエスト失敗時に自動でリトライする。

| 設定 | 値 |
|------|---|
| 最大リトライ回数 | 3回 |
| リトライ間隔 | 5秒 |

失敗時は以下のように表示される。

```
[Claude API] エラー（1/3回目）: <エラー内容>
  5秒後にリトライします...
[Claude API] エラー（2/3回目）: <エラー内容>
  5秒後にリトライします...
[Claude API] 失敗（3回試行）: <エラー内容>
```

リトライ回数・間隔を変更したい場合は `generate_slides_v2.py` 冒頭の定数を編集する。

```python
RETRY_MAX = 3       # 最大リトライ回数
RETRY_INTERVAL = 5  # リトライ間隔（秒）
```

---

## 生成ログ

実行のたびに `~/Desktop/logs.json` に自動で追記される。

```json
[
  {
    "datetime": "2026-05-14 16:40:16",
    "service_name": "本質のClaude Code 完全攻略 7dayブートキャンプ",
    "target": "AIに興味があるが、実用化できていないビジネスパーソン",
    "concept": "信頼性・安心感・実績",
    "slides_count": 13,
    "url": "https://gamma.app/docs/xxxxxxxxxx"
  }
]
```

`logs.json` は `.gitignore` で除外済みのためGitには保存されない。

---

## 注意事項

- `.env` は `.gitignore` で除外済み。APIキーをコミットしないこと
- GAMMA API は非同期処理。生成完了まで30〜60秒かかる
- Claude API の生成コスト：1回あたり約 $0.01〜0.03（claude-sonnet-4-6 使用）
- GAMMA API のクレジット消費：1回あたり約 55クレジット

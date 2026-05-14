# -*- coding: utf-8 -*-
import json
import os
import time
import sys
import anthropic
import requests

from dotenv import load_dotenv
load_dotenv(os.path.expanduser("~/Desktop/.env"), override=True)

CLAUDE_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
GAMMA_API_KEY = os.environ.get("GAMMA_API_KEY", "")
GAMMA_BASE = "https://public-api.gamma.app/v1.0"
RETRY_MAX = 3
RETRY_INTERVAL = 5


def retry(func, label):
    for attempt in range(1, RETRY_MAX + 1):
        try:
            return func()
        except Exception as e:
            if attempt == RETRY_MAX:
                print("")
                print("[" + label + "] 失敗（" + str(RETRY_MAX) + "回試行）: " + str(e))
                sys.exit(1)
            print("[" + label + "] エラー（" + str(attempt) + "/" + str(RETRY_MAX) + "回目）: " + str(e))
            print("  " + str(RETRY_INTERVAL) + "秒後にリトライします...")
            time.sleep(RETRY_INTERVAL)


def load_input(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def generate_slide_content(data):
    client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)

    slide_structure = (
        "1. 表紙（キャッチコピー）\n"
        "2. 問題提起\n"
        "3. 市場機会\n"
        "4. 解決策\n"
        "5. 講師実績①（みかみ）\n"
        "6. 講師実績②（佐藤将司）\n"
        "7. 1期生の実績・社会的証明\n"
        "8. サービス内容\n"
        "9. 講義一覧\n"
        "10. 特典\n"
        "11. 価格\n"
        "12. 反論つぶし\n"
        "13. クロージング"
    )

    prompt = (
        "あなたはトップセールスライターです。以下の情報をもとに、今すぐ購入したくなる販売スライドをJSON形式で生成してください。\n\n"
        "【サービス情報】\n"
        "サービス名：" + data['service_name'] + "\n"
        "コンセプト：" + data.get('concept', '') + "\n"
        "ターゲット：" + data['target'] + "\n"
        "訴求軸：" + data['appeal'] + "\n"
        "定価：" + data['price'] + "円\n"
        "割引価格（プライム）：" + data.get('discount_prime', '') + "円\n"
        "割引価格（スタンダード）：" + data.get('discount_standard', '') + "円\n"
        "講師①：" + data.get('instructor1', '') + "\n"
        "講師②：" + data.get('instructor2', '') + "\n\n"
        "【スライド構成】必ずこの13枚の順番で作成すること：\n"
        + slide_structure + "\n\n"
        "【表紙タイトル厳守】スライド1のtitleは必ず以下の文字列をそのまま使うこと：\n"
        "本質のClaude Code\\n完全攻略\\n7dayブートキャンプ\n\n"
        "【ライティングルール】\n"
        "・1スライド1メッセージ。タイトルは15字以内で体言止め\n"
        "・月10万円・7日間・3,000円など具体的な数字を必ず入れる\n"
        "・今すぐ買いたくなるセールスコピー。感情を動かす言葉を使う\n"
        "・bodyは箇条書き3〜5行。各行を「・」で始める\n"
        "・体言止めで力強く締める\n\n"
        "【厳守事項】\n"
        "・提供されたサービス情報以外の事実・実績・数字を捏造しないこと\n"
        "・不明な情報は使わず、提供された情報のみ使用すること\n"
        "・断定的な収入保証表現（〜稼げます）は使わず可能性の表現（〜を目指せる）にすること\n"
        "・メイン価格は198,000円（税抜）で訴求すること\n"
        "・割引価格（98,000円・148,000円）はクロージングスライドのみで触れること\n"
        "・割引を前面に押し出さないこと\n\n"
        "【出力形式】JSON配列のみを返す。他の文章は一切不要。\n"
        "例：[{\"title\": \"タイトル\", \"body\": \"・行1\\n・行2\\n・行3\"}]"
    )

    def call_claude():
        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4000,
            messages=[{"role": "user", "content": prompt}]
        )
        content = message.content[0].text
        start = content.find('[')
        end = content.rfind(']') + 1
        if start == -1 or end == 0:
            raise ValueError("レスポンスから JSON を取得できませんでした。内容: " + content[:200])
        return json.loads(content[start:end])

    return retry(call_claude, "Claude API")


def start_gamma_generation(slides, data):
    text = data['service_name'] + "\n\n"
    for s in slides:
        text += "## " + s['title'] + "\n" + s['body'] + "\n\n"

    def call_gamma():
        response = requests.post(
            GAMMA_BASE + "/generations",
            headers={"Content-Type": "application/json", "X-API-KEY": GAMMA_API_KEY},
            json={
                "inputText": text,
                "textMode": "preserve",
                "format": "presentation",
                "numCards": data['slides_count'],
                "textOptions": {"language": "ja"},
                "cardOptions": {"dimensions": "16x9"},
                "themeId": "canaveral"
            }
        )
        response.raise_for_status()
        result = response.json()
        generation_id = result.get("generationId") or result.get("id")
        if not generation_id:
            raise ValueError("generationId が取得できませんでした。レスポンス: " + str(result))
        return generation_id

    return retry(call_gamma, "GAMMA API")


def poll_gamma(generation_id, interval=5, timeout=300):
    print("生成完了を待機中...")
    deadline = time.time() + timeout
    while time.time() < deadline:
        response = requests.get(
            GAMMA_BASE + "/generations/" + generation_id,
            headers={"X-API-KEY": GAMMA_API_KEY}
        )
        response.raise_for_status()
        result = response.json()
        status = result.get("status", "")
        print("  ステータス: " + status)
        if status == "completed":
            return result
        if status == "failed":
            print("エラー: GAMMA の生成に失敗しました。" + str(result))
            sys.exit(1)
        time.sleep(interval)
    print("エラー: タイムアウト（" + str(timeout) + "秒）")
    sys.exit(1)


def extract_url(result):
    url = (result.get("url")
           or result.get("deckUrl")
           or result.get("gammaUrl")
           or result.get("deck", {}).get("url", "")
           or result.get("output", {}).get("url", ""))
    return url


def main():
    print("=== CCブートキャンプ スライド自動生成システム ===")
    input_path = os.path.expanduser("~/Desktop/input.json")
    data = load_input(input_path)
    print("入力データ読み込み完了: " + data['service_name'])

    print("Claude API でスライド内容を生成中...")
    slides = generate_slide_content(data)
    print(str(len(slides)) + "枚分のコンテンツ生成完了")

    print("GAMMA API にプレゼンテーション生成を依頼中...")
    generation_id = start_gamma_generation(slides, data)
    print("generationId: " + generation_id)

    result = poll_gamma(generation_id)

    url = extract_url(result)
    print("")
    print("=" * 50)
    print("生成完了！")
    if url:
        print("URL: " + url)
    else:
        print("URL が取得できませんでした。GAMMA ダッシュボードを確認してください。")
        print("レスポンス全体: " + str(result))
    print("=" * 50)

    out_path = os.path.expanduser("~/Desktop/generation_result.json")
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print("結果を保存: " + out_path)


if __name__ == '__main__':
    main()

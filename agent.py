# -*- coding: utf-8 -*-
import json
import os
import subprocess
import anthropic
from dotenv import load_dotenv

load_dotenv(os.path.expanduser("~/Desktop/.env"))

CLAUDE_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

INPUT_JSON_PATH = os.path.expanduser("~/Desktop/input.json")
GENERATE_SCRIPT = os.path.expanduser("~/Desktop/generate_slides_v2.py")

# input.json の各フィールドを埋めるツール定義
UPDATE_TOOL = {
    "name": "update_input_json",
    "description": "スライド生成に必要なパラメータをinput.jsonに書き込む。ユーザーの指示から読み取れる項目だけ更新し、不明な項目は現在の値を維持する。",
    "input_schema": {
        "type": "object",
        "properties": {
            "service_name": {
                "type": "string",
                "description": "サービス・講座・商品名"
            },
            "target": {
                "type": "string",
                "description": "ターゲット層（例：副業したい会社員・個人事業主）"
            },
            "appeal": {
                "type": "string",
                "description": "訴求軸・メリット（例：収入アップ・AI活用）"
            },
            "slides_count": {
                "type": "integer",
                "description": "生成するスライドの枚数"
            },
            "price": {
                "type": "string",
                "description": "定価（税抜、数字のみ）"
            },
            "discount_prime": {
                "type": "string",
                "description": "プライム向け割引価格（数字のみ）"
            },
            "discount_standard": {
                "type": "string",
                "description": "スタンダード向け割引価格（数字のみ）"
            },
            "instructor1": {
                "type": "string",
                "description": "講師1の名前"
            },
            "instructor2": {
                "type": "string",
                "description": "講師2の名前"
            }
        },
        "required": ["service_name", "target", "appeal", "slides_count"]
    }
}

SYSTEM_PROMPT = (
    "あなたはスライド生成AIエージェントです。\n"
    "ユーザーの自然言語の指示を解釈して、update_input_jsonツールを呼び出してください。\n"
    "指示に含まれていない項目は、現在のinput.jsonの値をそのまま使ってください。\n"
    "ツールを呼び出す前に、解釈した内容を1〜2行で確認してください。"
)


def load_current_input():
    try:
        with open(INPUT_JSON_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_input(data):
    with open(INPUT_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def run_generate():
    print("")
    print("generate_slides_v2.py を実行中...")
    print("-" * 40)
    result = subprocess.run(
        ["python3", GENERATE_SCRIPT],
        capture_output=False
    )
    print("-" * 40)
    if result.returncode != 0:
        print("エラーが発生しました。")
    else:
        print("完了！")


def call_agent(user_message, current_data):
    client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)

    context = "現在のinput.json:\n" + json.dumps(current_data, ensure_ascii=False, indent=2)
    full_message = context + "\n\nユーザーの指示: " + user_message

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        tools=[UPDATE_TOOL],
        messages=[{"role": "user", "content": full_message}]
    )

    # テキスト部分を表示
    for block in response.content:
        if block.type == "text" and block.text.strip():
            print("\nエージェント: " + block.text.strip())

    # ツール呼び出しを処理
    for block in response.content:
        if block.type == "tool_use" and block.name == "update_input_json":
            return block.input

    return None


def apply_updates(current_data, updates):
    merged = dict(current_data)
    for key, value in updates.items():
        merged[key] = value
    return merged


def confirm_and_run(updated_data):
    print("")
    print("=== 更新後の input.json ===")
    print(json.dumps(updated_data, ensure_ascii=False, indent=2))
    print("")
    answer = input("この内容でスライドを生成しますか？ [y/n]: ").strip().lower()
    if answer in ("y", "yes", ""):
        save_input(updated_data)
        print("input.json を保存しました。")
        run_generate()
        return True
    else:
        print("キャンセルしました。")
        return False


def main():
    print("=== スライド生成エージェント ===")
    print("例：「副業したい会社員向けに13枚作って」")
    print("    「サービス名をAI副業スクールに変えて価格は98000円で」")
    print("終了するには「quit」と入力してください。")
    print("")

    while True:
        try:
            user_input = input("指示を入力 > ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n終了します。")
            break

        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit", "終了"):
            print("終了します。")
            break

        current_data = load_current_input()
        updates = call_agent(user_input, current_data)

        if updates is None:
            print("パラメータを読み取れませんでした。もう少し具体的に指示してください。")
            continue

        updated_data = apply_updates(current_data, updates)
        confirm_and_run(updated_data)
        print("")


if __name__ == "__main__":
    main()

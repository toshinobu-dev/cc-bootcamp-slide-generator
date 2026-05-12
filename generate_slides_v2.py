# -*- coding: utf-8 -*-
import json
import os
import anthropic
import requests

from dotenv import load_dotenv
load_dotenv(os.path.expanduser("~/Desktop/.env"))

CLAUDE_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
GAMMA_API_KEY = os.environ.get("GAMMA_API_KEY", "")

def load_input(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def generate_slide_content(data):
    client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)
    prompt = "以下のサービス情報をもとに販売スライドの内容をJSON形式で" + str(data['slides_count']) + "枚分生成してください。\n"
    prompt += "サービス名：" + data['service_name'] + "\n"
    prompt += "ターゲット：" + data['target'] + "\n"
    prompt += "訴求軸：" + data['appeal'] + "\n"
    prompt += "価格：" + data['price'] + "円\n"
    prompt += "必ずJSON配列のみで返してください。例：[{\"title\": \"タイトル\", \"body\": \"本文\"}]"
    
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4000,
        messages=[{"role": "user", "content": prompt}]
    )
    content = message.content[0].text
    start = content.find('[')
    end = content.rfind(']') + 1
    return json.loads(content[start:end])

def generate_gamma(slides, data):
    text = data['service_name'] + "\n\n"
    for s in slides:
        text += "## " + s['title'] + "\n" + s['body'] + "\n\n"
    
    response = requests.post(
        "https://public-api.gamma.app/v1.0/generations",
        headers={
            "Content-Type": "application/json",
            "X-API-KEY": GAMMA_API_KEY
        },
        json={
            "inputText": text,
            "textMode": "preserve",
            "format": "presentation",
            "numCards": data['slides_count'],
            "textOptions": {"language": "ja"},
            "cardOptions": {"dimensions": "16x9"}
        }
    )
    return response.json()

def main():
    print("=== CCブートキャンプ スライド自動生成システム ===")
    input_path = os.path.expanduser("~/Desktop/input.json")
    data = load_input(input_path)
    print("入力データ読み込み完了: " + data['service_name'])
    
    print("Claude APIでスライド内容を生成中...")
    slides = generate_slide_content(data)
    print(str(len(slides)) + "枚分のコンテンツ生成完了")
    
    print("GAMMA APIでスライドを生成中...")
    result = generate_gamma(slides, data)
    print("生成完了！")
    print(result)

if __name__ == '__main__':
    main()

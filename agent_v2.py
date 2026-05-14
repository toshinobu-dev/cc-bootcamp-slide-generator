# -*- coding: utf-8 -*-
import json
import os
import sys
import anthropic
from dotenv import load_dotenv

load_dotenv(os.path.expanduser("~/Desktop/.env"), override=True)

# generate_slides_v2 をモジュールとして読み込む（input.json は一切触らない）
sys.path.insert(0, os.path.expanduser("~/Desktop"))
import generate_slides_v2 as gen

CLAUDE_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
INPUT_PATH = os.path.expanduser("~/Desktop/input.json")

GENERATE_TARGETS_TOOL = {
    "name": "set_targets",
    "description": "サービスに対して効果的なターゲット層を3つ提案する",
    "input_schema": {
        "type": "object",
        "properties": {
            "targets": {
                "type": "array",
                "items": {"type": "string"},
                "description": "ターゲット層の説明（3つ）"
            }
        },
        "required": ["targets"]
    }
}

SELECT_BEST_TOOL = {
    "name": "select_best",
    "description": "3つのスライドセットを評価して最良の1つを選ぶ",
    "input_schema": {
        "type": "object",
        "properties": {
            "best_index": {
                "type": "integer",
                "description": "最良の結果のインデックス（0〜2）"
            },
            "reason": {
                "type": "string",
                "description": "選んだ理由（2〜3文）"
            }
        },
        "required": ["best_index", "reason"]
    }
}


def generate_targets(base_data):
    client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)

    prompt = (
        "あなたはセールスマーケターです。以下のサービス情報をもとに、"
        "このブートキャンプに最も響くターゲット層を3パターン考えてください。\n\n"
        "【サービス情報】\n"
        "サービス名：" + base_data["service_name"] + "\n"
        "コンセプト：" + base_data.get("concept", "") + "\n"
        "訴求軸：" + base_data.get("appeal", "") + "\n"
        "定価：" + base_data.get("price", "") + "円\n"
        "講師①：" + base_data.get("instructor1", "") + "\n"
        "講師②：" + base_data.get("instructor2", "") + "\n\n"
        "【ターゲット設定の条件】\n"
        "・このサービス（Claude Code × 7日間ブートキャンプ）に最も響く人物像にすること\n"
        "・年齢・職業・具体的な悩みを必ず明記すること\n"
        "・3パターンはそれぞれ異なる属性・職種・課題感を持つこと\n"
        "・現在のターゲット「" + base_data.get("target", "") + "」も参考にしつつ、"
        "より解像度の高い3パターンを提案すること\n\n"
        "【厳守事項】\n"
        "・捏造情報・根拠のない統計・架空の実績は使わないこと\n"
        "・「必ず稼げる」「確実に収入が上がる」などの断定的な収入保証表現は使わないこと\n"
        "・可能性の表現（〜を目指せる・〜につながりやすい）にすること"
    )

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        tools=[GENERATE_TARGETS_TOOL],
        messages=[{"role": "user", "content": prompt}]
    )

    for block in response.content:
        if block.type == "tool_use" and block.name == "set_targets":
            targets = block.input["targets"]
            # 文字列で返ってきた場合はJSONとしてパース
            if isinstance(targets, str):
                targets = json.loads(targets)
            if isinstance(targets, list) and len(targets) >= 3:
                return targets[:3]

    # フォールバック: テキストレスポンスからJSON配列を抽出
    for block in response.content:
        if block.type == "text":
            start = block.text.find('[')
            end = block.text.rfind(']') + 1
            if start != -1 and end > 0:
                targets = json.loads(block.text[start:end])
                if isinstance(targets, list) and len(targets) >= 3:
                    return targets[:3]

    print("エラー: ターゲットを生成できませんでした。")
    sys.exit(1)


def generate_for_target(base_data, target, index):
    print("")
    print("--- ターゲット " + str(index + 1) + "/3 ---")
    print("ターゲット: " + target)

    data = dict(base_data)
    data["target"] = target

    print("Claude API でスライド原稿を生成中...")
    slides = gen.generate_slide_content(data)
    print(str(len(slides)) + "枚分のコンテンツ生成完了")

    print("GAMMA API にプレゼンテーション生成を依頼中...")
    generation_id = gen.start_gamma_generation(slides, data)
    print("generationId: " + generation_id)

    result = gen.poll_gamma(generation_id)
    url = gen.extract_url(result)

    gen.save_log(data, url)

    print("URL: " + url)
    return {"target": target, "url": url}


def evaluate_and_pick(base_data, results):
    client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)

    candidates = ""
    for i, r in enumerate(results):
        candidates += "パターン" + str(i + 1) + ": " + r["target"] + "\n"

    prompt = (
        "以下のサービスの販売スライドを3パターンのターゲット向けに生成しました。\n"
        "どのターゲットへのアプローチが最も効果的か評価し、最良の1つを選んでください。\n\n"
        "サービス名：" + base_data["service_name"] + "\n"
        "訴求軸：" + base_data.get("appeal", "") + "\n"
        "価格：" + base_data.get("price", "") + "円\n\n"
        "【3つのターゲット】\n" + candidates + "\n"
        "評価基準：\n"
        "・購買意欲の高さ（課題感と価格帯のマッチ）\n"
        "・ターゲットの具体性（刺さりやすさ）\n"
        "・サービスの強みとの一致度"
    )

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        tools=[SELECT_BEST_TOOL],
        messages=[{"role": "user", "content": prompt}]
    )

    for block in response.content:
        if block.type == "tool_use" and block.name == "select_best":
            best_index = block.input["best_index"]
            reason = block.input["reason"]
            return results[best_index], reason

    print("エラー: 評価結果を取得できませんでした。")
    sys.exit(1)


def main():
    print("=== スライド最適化エージェント (agent_v2) ===")
    print("Claude が自律的にターゲットを3つ考え、最良のスライドを選びます。")
    print("")

    base_data = gen.load_input(INPUT_PATH)
    print("ベースデータ読み込み完了: " + base_data["service_name"])

    print("")
    print("[Step 1] ターゲット候補を3つ生成中...")
    targets = generate_targets(base_data)
    for i, t in enumerate(targets):
        print("  " + str(i + 1) + ". " + t)

    print("")
    print("[Step 2] 各ターゲットでスライドを生成中...")
    results = []
    for i, target in enumerate(targets):
        result = generate_for_target(base_data, target, i)
        results.append(result)

    print("")
    print("[Step 3] 品質を評価して最良のスライドを選定中...")
    best, reason = evaluate_and_pick(base_data, results)

    print("")
    print("=" * 50)
    print("最適化完了！")
    print("")
    print("【選定ターゲット】")
    print(best["target"])
    print("")
    print("【選定理由】")
    print(reason)
    print("")
    print("【最終URL】")
    print(best["url"])
    print("=" * 50)


if __name__ == "__main__":
    main()

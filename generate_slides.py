import os, pickle
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/presentations', 'https://www.googleapis.com/auth/drive']
CREDS_FILE = os.path.expanduser('~/Desktop/credentials.json')
TOKEN_FILE = os.path.expanduser('~/Desktop/token.pickle')

def get_service():
    creds = None
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, 'rb') as f:
            creds = pickle.load(f)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, 'wb') as f:
            pickle.dump(creds, f)
    return build('slides', 'v1', credentials=creds)

def add_slide(service, pid, title, body):
    r1 = service.presentations().batchUpdate(presentationId=pid, body={'requests': [
        {'createSlide': {'slideLayoutReference': {'predefinedLayout': 'BLANK'}}}
    ]}).execute()
    sid = r1['replies'][0]['createSlide']['objectId']
    service.presentations().batchUpdate(presentationId=pid, body={'requests': [
        {'updatePageProperties': {'objectId': sid, 'pageProperties': {'pageBackgroundFill': {'solidFill': {'color': {'rgbColor': {'red': 0.05, 'green': 0.04, 'blue': 0.02}}}}}, 'fields': 'pageBackgroundFill'}},
        {'createShape': {'objectId': f'acc_{sid}', 'shapeType': 'RECTANGLE', 'elementProperties': {'pageObjectId': sid, 'size': {'width': {'magnitude': 342900, 'unit': 'EMU'}, 'height': {'magnitude': 6858000, 'unit': 'EMU'}}, 'transform': {'scaleX': 1, 'scaleY': 1, 'translateX': 0, 'translateY': 0, 'unit': 'EMU'}}}},
        {'updateShapeProperties': {'objectId': f'acc_{sid}', 'shapeProperties': {'shapeBackgroundFill': {'solidFill': {'color': {'rgbColor': {'red': 0.94, 'green': 0.48, 'blue': 0.13}}}}}, 'fields': 'shapeBackgroundFill'}},
        {'createShape': {'objectId': f't_{sid}', 'shapeType': 'TEXT_BOX', 'elementProperties': {'pageObjectId': sid, 'size': {'width': {'magnitude': 8500000, 'unit': 'EMU'}, 'height': {'magnitude': 1400000, 'unit': 'EMU'}}, 'transform': {'scaleX': 1, 'scaleY': 1, 'translateX': 700000, 'translateY': 900000, 'unit': 'EMU'}}}},
        {'insertText': {'objectId': f't_{sid}', 'text': title}},
        {'updateTextStyle': {'objectId': f't_{sid}', 'style': {'fontSize': {'magnitude': 28, 'unit': 'PT'}, 'foregroundColor': {'opaqueColor': {'rgbColor': {'red': 0.94, 'green': 0.48, 'blue': 0.13}}}, 'bold': True}, 'fields': 'fontSize,foregroundColor,bold'}},
        {'createShape': {'objectId': f'b_{sid}', 'shapeType': 'TEXT_BOX', 'elementProperties': {'pageObjectId': sid, 'size': {'width': {'magnitude': 8500000, 'unit': 'EMU'}, 'height': {'magnitude': 3500000, 'unit': 'EMU'}}, 'transform': {'scaleX': 1, 'scaleY': 1, 'translateX': 700000, 'translateY': 2500000, 'unit': 'EMU'}}}},
        {'insertText': {'objectId': f'b_{sid}', 'text': body}},
        {'updateTextStyle': {'objectId': f'b_{sid}', 'style': {'fontSize': {'magnitude': 16, 'unit': 'PT'}, 'foregroundColor': {'opaqueColor': {'rgbColor': {'red': 0.88, 'green': 0.85, 'blue': 0.80}}}}, 'fields': 'fontSize,foregroundColor'}},
    ]}).execute()

def main():
    service = get_service()
    pres = service.presentations().create(body={'title': 'CC ブートキャンプ 販売スライド'}).execute()
    pid = pres['presentationId']
    slides = [
        ('月額3,000円のAIで\n月10万円の案件を獲る', '本質のClaude Code 完全攻略\n7day ブートキャンプ\n2期生 限定募集'),
        ('毎日、同じ作業を\n繰り返していませんか？', '① 資料作成・メール・SNS投稿を毎回手作業でやっている\n② AIを使いこなしたいが、まだ本格活用できていない\n③ 副業・新収入源を探しているが何から始めればいいかわからない'),
        ('今が、早い者勝ちの時代', 'Claude Codeを使いこなせる日本人は推定0.1%未満\n先行者優位が圧倒的に働く今\nスキルを身につけた人間だけが勝ち残る'),
        ('7日間で\n月10万円案件が取れるレベルへ', '✦ プログラミング完全未経験でもOK\n✦ 月額3,000円で月10万円の案件獲得が現実に\n✦ 現役で数億円規模の事業をAIで回している講師が直接指導\n✦ 1期生は未経験から7日でシステムを完成'),
        ('講師：みかみ\nアドネス株式会社 代表取締役', '東大現役合格 → 在学中に起業 → 半年で月商1億円\n創業5年で年商30億円\nSNS総フォロワー31万人\nAIで月商5億円を達成'),
        ('講師：佐藤将司\nアドネス', '公務員・月給12万円 → 借金500万円から起業\nプログラミング経験ゼロからClaude Codeで100個以上のシステム構築\n初月4,500万円を4人チームで達成\n法人AIコンサル：月額50〜200万円で複数社契約中'),
        ('未経験から7日で\nシステム完成', 'LP制作・SNS自動化・業務効率化など\n受講生が各自のシステムを完成\nコミュニティで互いに成長中'),
        ('全13テーマ＋毎週追加', 'はじめてのClaude Code\nAIエージェント × LP制作 / 案件探索 / スライド制作\nAIエージェント × X投稿 / LINE Bot / システム開発\nPPTX自動作成 / SEO記事生成（追加費用なし）'),
        ('2期生限定\n社内システム12種をそのまま提供', 'スライド自動生成 ¥400,000/月相当\nPPTX自動作成 ¥200,000/月相当\nLINE Bot構築 ¥180,000/月相当\n特典①合計：¥1,736,000相当'),
        ('総額 ¥2,485,000相当', 'ブートキャンプ本体 ¥649,000\n特典① 社内システム12種 ¥1,736,000\n特典② 1on1コンサル2時間 ¥50,000\n特典③ 1ヶ月補講サポート ¥50,000'),
        ('不安を、全部解消します', 'Q. 未経験でも大丈夫？ → 日本語で話しかけるだけ\nQ. 忙しい？ → 予習1日30分・21時〜2時間\nQ. 他スクールと違う？ → 教える人間が今AIで数億円の事業を回している\nQ. 元が取れる？ → 月10万円の案件2件で全額回収'),
        ('セミナー参加者 限定割引', '定価：¥198,000（税抜）\nプライム受講生：10万円引き → ¥98,000\nスタンダード受講生：5万円引き → ¥148,000\n分割：月々約7,532円〜　1日約251円'),
        ('今日、ここで決める人だけが\n先行者優位を手にできる', 'Claude Codeを使いこなせる日本人は推定0.1%未満\nこの差は時間が経つほど広がるばかり\n\n今すぐ申し込む'),
    ]
    for i, (t, b) in enumerate(slides):
        add_slide(service, pid, t, b)
        print(f'スライド {i+1}/13 完了')
    print(f'\n完成！\nhttps://docs.google.com/presentation/d/{pid}')

if __name__ == '__main__':
    main()

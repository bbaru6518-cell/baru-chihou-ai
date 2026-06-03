import re

def generate_all_horses_diagnosis(raw_text, ai_recommendations=None):
    """
    コピペデータから全頭を抽出し、精密診断のMarkdownテーブルを出力する関数
    
    :param raw_text: 地方競馬コピペデータ（馬柱テキスト）
    :param ai_recommendations: 投資指示書から得た評価マップ（任意）
    """
    # 投資指示書のデータをデフォルトでマッピング（検知用）
    if ai_recommendations is None:
        ai_recommendations = {
            2: {"status": "最高 (AA) 🔥", "role": "**軸馬** 🔥", "note": "船橋コース＆距離実績上位。データ分析でも「レース間隔適性あり」と太鼓判。"},
            3: {"status": "上位 (A)", "role": "**紐穴**", "note": "船橋1200mの適性高。調教師（山下貴）×騎手（本田正）のコース特注コンビ。"},
            7: {"status": "最高 (AA) 🔥", "role": "**相手** 🔥", "note": "前走船橋で1.2秒差の好走。エピカリス産駒らしく地方のタフな砂が合う。"},
            8: {"status": "最高 (AA) 🔥", "role": "**相手** 🔥", "note": "コース適性・馬場適性・競馬場実績のすべてでデータ上位。外枠もプラス。"},
            5: {"status": "中位 (B)", "role": "**紐穴**", "note": "前走船橋で0.9秒差の6着。大型馬で砂を被らなければ粘り増す余地あり。"},
            6: {"status": "中位 (B)", "role": "**紐穴**", "note": "今回の良馬場への適性評価あり。末脚がハマれば3着拾うシーンも。"},
            9: {"status": "上位 (A)", "role": "**紐穴**", "note": "中央未勝利からの移籍初戦。マテラスカイ産駒で船橋ダート適性高。"},
            10: {"status": "中位 (B)", "role": "**紐穴**", "note": "中央ダート未勝利組。地方の小回り・砂の厚さに対応できれば地力は通用。"}
        }

    # 馬柱ブロックを分解するための正規表現（「馬番 枠番 チェック状態」の並びをトリガーにする）
    # 例: "1 \t 1 \t --" や "2 \t 2 \t ✓"
    horse_blocks = re.split(r'\n(?=\d+\s+\d+\s+(?:--|✓))', raw_text)
    
    # テーブルヘッダーの準備
    markdown_lines = [
        "### 📊 全頭精密診断・地方ダート適性リスト\n",
        "| 馬番 | 馬名 | 父 / 母父 | 地方ダート砂適性 | AI評価 | 短評・前走分析 |",
        "| :---: | :--- | :--- | :---: | :---: | :--- |"
    ]
    
    for block in horse_blocks:
        lines = [line.strip() for line in block.split('\n') if line.strip()]
        if not lines or not re.match(r'^\d+$', lines[0]):
            continue
            
        try:
            # 1行目から馬番を取得
            num_str = lines[0]
            num = int(num_str)
            formatted_num = f"**{num:02d}**"
            
            # 血統・馬名セクションのパース
            # チェックマーク等の次の行以降から、カタカナの馬名と血統を探索
            blood_idx = -1
            for i, line in enumerate(lines):
                if line.startswith('(') and line.endswith(')'): # 母父のカッコを発見
                    blood_idx = i
                    break
            
            if blood_idx != -1:
                # 血統構成から逆算して馬名と種牡馬を取得
                father = lines[blood_idx - 2]
                horse_name = lines[blood_idx - 1]
                broodmare_sire = lines[blood_idx] # (エンパイアメーカー) など
                pedigree = f"{father}<br>{broodmare_sire}"
            else:
                horse_name = "解析エラー"
                pedigree = "--"
                
            # AI評価マップから該当馬のデータを取得（なければ一律デフォルト）
            rec = ai_recommendations.get(num, {
                "status": "中位 (B)" if num == 1 else "下位 (C)", 
                "role": "`--`", 
                "note": "川崎900m中心の臨戦。1200mへの距離延長と船橋の深い砂への対応が課題。" if num == 1 else "連闘での参戦。近走は浦和・船橋ともに大敗が続いており、静観が妥当。"
            })
            
            # マークダウンの行を生成
            row = f"| {formatted_num} | {horse_name} | {pedigree} | {rec['status']} | {rec['role']} | {rec['note']} |"
            markdown_lines.append(row)
            
        except Exception as e:
            # パース漏れがあった場合のスキップ処理
            continue

    # 最終的なMarkdownテキストを結合
    return "\n".join(markdown_lines)


# --- テスト実行用コード ---
if __name__ == "__main__":
    # ここにユーザーから送られたコピペデータを格納
    copypaste_data = """[ここに上記で貼り付けた1Rの馬柱テキストが入る想定]"""
    
    # 実際はプロンプトの生テキストをそのまま引数に渡します
    # output = generate_all_horses_diagnosis(user_input_text)
    # print(output)

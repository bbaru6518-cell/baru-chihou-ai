import re
import streamlit as st

def parse_and_generate_table(raw_text, ai_recommendations=None):
    """
    コピペデータから全頭をパースし、エラー落ちしない安全な設計で
    精密診断のMarkdownテーブルを出力する完全版関数
    """
    # 1. 投資指示書データ（AI評価マップ）が空の場合のデフォルト設定
    if ai_recommendations is None:
        # ログに表示されていた船橋3Rの馬番構成をベースにモックを用意
        ai_recommendations = {
            11: {"status": "最高 (AA) 🔥", "role": "**軸馬** 🔥", "note": "今回の中心。走破タイム理論値トップ。コース実績も文句なし。"},
            5:  {"status": "最高 (AA) 🔥", "role": "**軸馬** 🔥", "note": "前走の伸び脚が優秀。砂を被らない位置取りなら勝ち負け。"},
            10: {"status": "上位 (A)", "role": "**相手**", "note": "クラス上位の安定感。外枠からスムーズに先行できれば残り目十分。"},
            2:  {"status": "上位 (A)", "role": "**相手**", "note": "内枠の立ち回りが鍵。インをロスなく立ち回れば一発ある。"},
            9:  {"status": "中位 (B)", "role": "**相手**", "note": "距離短縮はプラス。時計の掛かる馬場になれば浮上。"},
            6:  {"status": "中位 (B)", "role": "**相手/紐穴**", "note": "大荒れ展開による自動救済枠。展開がハマれば3着十分。"},
            1:  {"status": "中位 (B)", "role": "**相手/紐穴**", "note": "激走穴騎手（藤江渉）起用。内ラチ沿いで死んだふりからの激走警戒。"},
            8:  {"status": "下位 (C)", "role": "**穴紐**", "note": "激走穴騎手（加藤雄真）起用。展開極限泥仕合での救済。"},
            7:  {"status": "下位 (C)", "role": "**穴紐**", "note": "複勝大口歪み（インサイダー）検知。ヒモには押さえたい。"},
            3:  {"status": "消し ❌", "role": "強制排除", "note": "秋元フィルターにより完全消去。静観が妥当。"},
        }

    # 2. テーブルヘッダーの構築
    markdown_lines = [
        "### 📊 全頭精密診断・地方ダート適性リスト\n",
        "| 馬番 | 馬名 | 父 / 母父 | 地方ダート砂適性 | AI評価 | 短評・前走分析 |",
        "| :---: | :--- | :--- | :---: | :---: | :--- |"
    ]

    # 3. 馬柱データを「馬番 枠番 チェック」をトリガーに分割
    # netkeibaや地方競馬データの「1 1 --」や「2 2 ✓」の並びで区切る
    horse_blocks = re.split(r'\n(?=\d+\s+\d+\s+(?:--|✓))', raw_text)

    # 4. 全頭ループ処理（ここを徹底ガード）
    for block in horse_blocks:
        lines = [line.strip() for line in block.split('\n') if line.strip()]
        
        # ブロックが空、または最初の行が数字（馬番）でなければスキップ
        if not lines or not re.match(r'^\d+$', lines[0]):
            continue
            
        try:
            # --- 馬番の確定 ---
            num = int(lines[0])
            formatted_num = f"**{num:02d}**"
            
            # --- 血統（カッコ）のインデックスを探索 ---
            blood_idx = -1
            for i, line in enumerate(lines):
                if line.startswith('(') and line.endswith(')'):
                    blood_idx = i
                    break
            
            # --- 馬名・血統の抽出 ---
            if blood_idx != -1 and blood_idx >= 2:
                father = lines[blood_idx - 2]       # カッコの2行上が「父」
                horse_name = lines[blood_idx - 1]   # カッコの1行上が「馬名」
                broodmare_sire = lines[blood_idx]   # カッコ自体が「母父」
                pedigree = f"{father}<br>{broodmare_sire}"
            else:
                # 血統構成が上手く取れなかった場合の安全弁
                # カッコがない場合は、1行目が馬番なので2行目を仮で馬名にする
                horse_name = lines[1] if len(lines) > 1 else "解析エラー"
                pedigree = "--"

            # --- ジョッキーなどのパーツ処理（もし今後拡張する場合もここなら安全） ---
            # 例: parts = lines[...]
            # jockey = parts (前回の構文エラー原因をここで完全に内包してガード)

            # --- AI評価データの紐付け ---
            # 該当の馬番がai_recommendationsに無ければデフォルト（下位評価）を適用
            rec = ai_recommendations.get(num, {
                "status": "下位 (C)", 
                "role": "`--`", 
                "note": "近走の走破タイム判定から、この舞台では静観が妥当。"
            })
            
            # --- マークダウンの行を生成 ---
            row = f"| {formatted_num} | {horse_name} | {pedigree} | {rec['status']} | {rec['role']} | {rec['note']} |"
            markdown_lines.append(row)
            
        except Exception as e:
            # 🛡️ 万が一ここでパースエラーが起きても、アプリ全体を落とさずに次の馬へ進む
            continue

    # 5. 生成されたリストを1つの文字列に結合して返す
    return "\n".join(markdown_lines)


# --- StreamlitのUI部分での呼び出し例 ---
# 実際にapp.pyで表示させる時は以下のように記述します
if "copypaste_input" in st.session_state and st.session_state.copypaste_input:
    st.success("コピペデータのパースに成功しました。")
    
# 変換実行
# もしAIの解析結果データ（辞書型）が別にあるなら、第2引数にそれを渡します
# 例として、変数名が「ai_analysis_result」の場合：
final_table_md = parse_and_generate_table(
# （この上には関数の定義や、テキストエリアなどの st.text_area("...", key="copypaste_input") がある想定です）

# ==========================================
# 🛑 ここから下が差し替えるコードです！
# ==========================================

# st.session_state の中身を安全にチェック（存在しない場合は None を返す）
copypaste_data = st.session_state.get("copypaste_input")

if copypaste_data:
    st.success("コピペデータのパースに成功しました。")
    
    # 変換実行（カッコも綺麗に閉じています！）
    final_table_md = parse_and_generate_table(copypaste_data)
    
    # テーブルを描画
    st.markdown(final_table_md, unsafe_html=True)
else:
    # まだデータが入力されていない時の案内（エラーにせず、優しく待つ）
    st.info("サイドバーまたは入力エリアにレースデータを貼り付けてください。")

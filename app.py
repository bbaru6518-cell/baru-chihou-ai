import streamlit as st
import google.generativeai as genai
import os
import datetime

# --- 設定 ---
LOG_DIR = "racing_logs_standard"
os.makedirs(LOG_DIR, exist_ok=True)
st.set_page_config(page_title="Baru 競馬AI Pro", layout="wide")

# --- サイドバー：総監督司令部 ---
with st.sidebar:
    st.header("⚙️ 総監督司令部")
    api_key = st.text_input("Gemini API KEY", type="password")
    
    st.subheader("🎯 統合解析基準（常時適用）")
    st.info("""
    以下の要素を全頭診断に統合せよ：
    - JRA/地方競馬の高速馬場・トラックバイアス
    - 芝・ダートのキレ
    - 走破タイム理論（基準タイム・馬場補正）
    - 上がり3F
    - 展開・ハナ争い
    """)
    
    st.divider()
    
    # 期待値フィルター設定（オッズ下限の設定）
    st.header("💰 期待値フィルター設定")
    min_odds = st.number_input(
        "軸馬・2列目から除外する単勝オッズのしきい値", 
        min_value=1.0, 
        max_value=20.0, 
        value=4.0, 
        step=0.5
    )
    st.caption(f"💡 現在の設定: 単勝 {min_odds} 倍以下の馬は軸・2列目から除外。")

    st.divider()
    
    # 【追加機能】画像データ手動入力インターフェース
    st.header("📸 画面スクショ・データ連動")
    img1_top_horses = st.text_input("1枚目：データ上位馬3頭（例: 6, 1, 5）", value="")
    img2_track_horses = st.text_input("2枚目：今回のレース間隔実績馬（例: 8, 10）", value="")

    st.divider()
    
    # 過去ログエリア
    st.header("📂 過去ログ・結果復習ルーム")
    log_files = sorted([f for f in os.listdir(LOG_DIR) if f.endswith(".txt")], reverse=True)
    selected_log = st.selectbox("復習・確認する過去の予想", log_files)
    if st.button("📖 予想指示書を呼び出す"):
        with open(os.path.join(LOG_DIR, selected_log), "r", encoding="utf-8") as f:
            st.session_state["res"] = f.read()
        st.rerun()

# --- メインエリア ---
st.title("🏇 Baru 競馬AI Pro - 統合解析司令部")
manual_data = st.text_area("✍️ 次回の馬柱・オッズデータ入力（データ分析傾向も含む）", height=300)

if st.button("🚀 統合解析実行"):
    if not api_key: 
        st.error("APIキーを入力してください")
    else:
        try:
            with st.spinner("統合解析中..."):
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel('gemini-2.5-flash')
                
                # スクショデータの指示を動的に生成
                image_logic_prompt = ""
                if img1_top_horses:
                    image_logic_prompt += f"\n- スクショ1（データ上位馬）として指定された馬番 【 {img1_top_horses} 】 は極めて強力な適性馬として評価せよ。"
                if img2_track_horses:
                    image_logic_prompt += f"\n- スクショ2（レース間隔実績馬）として指定された馬番 【 {img2_track_horses} 】 は、今回のローテーション適性が高い紐候補として3列目や流し相手に必ず組み込め。"

                prompt = f"""
                【今回の馬柱・オッズデータ（netkeiba分析情報含む）】
                {manual_data}
                
                【📸 スクショ画像からの最優先連動データ】{image_logic_prompt}

                【⚙️ 総監督絶対厳守ロジック：軸馬スクリーニング】
                1. スクショ1のデータ上位馬の中から、単勝オッズが【 {min_odds} 倍超 】を満たす4番人気〜8番人気前後の伏兵を、本レースの【絶対の本命軸（◎）】の1列目に据えよ。
                2. スクショ1のデータ上位馬であっても、単勝オッズが【 {min_odds} 倍以下 】の過剰人気馬は、3連複の1列目（軸）に据えることを【禁止】とし、2列目（対抗）に置くか、配当を著しく下げる場合は3列目の保険に落とせ。

                【⚙️ 総監督絶対厳守ロジック：3連複「最低50倍以上」限定フィルター】
                買い目を構築する際、配当が安くなる組み合わせ（例：上位人気同士が紐で絡み、3連複の想定配当が50倍未満になるような組み合わせ）は、投資効率が極めて悪いため【買い目から完全に排除（間引き）】せよ。
                軸馬に中穴を据え、2列目に実力馬を配置し、3列目にスクショ2の実績馬や大穴馬（7〜11人気・最下位）を散らすフォーメーションを組み、的中時に確実に【50倍（5,000円）以上、および万馬券〜十万馬券】となる尖った15点を構築すること。

                【投資指示書：出力フォーマット】
                AIの最終結論として、以下の形式で高回収率データを必ず提示せよ。

                1. 🎯 【裏・波乱特化型 3連複15点フォーメーション（想定配当50倍〜万馬券限定）】
                   - 1列目（軸・1頭）: スクショ1のデータ上位かつ、単勝オッズ【 {min_odds} 倍超 】の伏兵から厳選。
                   - 2列目（対抗・2頭）: スクショ1の残りの上位馬や実力馬を選定。
                   - 3列目（大穴・6頭）: スクショ2の実績馬、および大穴馬。1番人気を保険で入れる場合は「1列目と2列目のオッズの掛け算で、50倍以上の配当が物理的に維持できる場合のみ」3列目に1頭だけ許可する。
                   ※組み合わせを「ぴったり15点」で書き出せ。

                2. 🤝 【中穴直撃 ワイド3点】
                   - データ上位馬およびスクショ2の実績馬を絡めた、中穴ゾーンの有力馬3頭によるボックス（計3点）。

                3. 🐎 【主導権強奪 馬連4点】
                   - 1列目に指定した軸馬から、データ上位馬や展開利のある馬へ流す高オッズ狙いの4点。

                【指示】
                上記のオッズ制限、スクショデータ連動、および「3連複50倍以上厳守」のロジックを思考に統合し、全頭を精密に診断せよ。
                出力は必ず以下のMarkdownテーブル形式で行うこと：
                | 馬番 | 馬名 | 人気（オッズ） | 評価 | 診断コメント（オッズフィルター・50倍以上選定、およびスクショデータの適用有無を明記） |
                | --- | --- | --- | --- | --- |
                
                最後に、上記【3連複15点（50倍以上保証）】【ワイド3点】【馬連4点】の買い目を総監督への【統合投資指示書】として結論提示せよ。
                """
                
                response = model.generate_content(prompt)
                st.session_state["res"] = response.text
                
                now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                with open(os.path.join(LOG_DIR, f"Race_{now}.txt"), "w", encoding="utf-8") as f:
                    f.write(response.text)
            
            st.rerun()
            
        except Exception as e: 
            st.error(f"解析エラー: {e}")

if "res" in st.session_state:
    st.markdown(st.session_state["res"])

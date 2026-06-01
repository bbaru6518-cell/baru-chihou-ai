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
    
    # 過去ログエリア
    st.header("📂 過去ログ・結果復習ルーム")
    log_files = sorted([f for f in os.listdir(LOG_DIR) if f.endswith(".txt")], reverse=True)
    selected_log = st.selectbox("復習・確認する過去の予想", log_files)
    if st.button("📖 予想指示書を呼び出す"):
        with open(os.path.join(LOG_DIR, selected_log), "r", encoding="utf-8") as f:
            st.session_state["res"] = f.read()
        st.rerun()

    st.divider()

    # レース結果コピペ投入エリア
    st.header("🏁 レース結果のコピペ投入")
    race_result_input = st.text_area("1行目：レース名 / 2行目～：結果コピペ", height=200)
    
    if st.button("🚨 実際の着順・ハナ争いと照合して復習"):
        if not api_key:
            st.error("APIキーを入力してください")
        elif not race_result_input:
            st.error("結果データをコピペしてください")
        elif "res" not in st.session_state:
            st.error("まずメイン画面で予想を実行するか過去ログを呼び出してください")
        else:
            try:
                with st.spinner("実際のレース結果と照合し、反省会を実施中..."):
                    genai.configure(api_key=api_key)
                    model = genai.GenerativeModel('gemini-2.5-flash')
                    
                    review_prompt = f"""
                    【総監督からの命令：レース結果の答え合わせと徹底反省】
                    あなたが先ほど出力した【予想指示書】と、実際に発生した【レース結果・着順】を照合し、以下の基準で猛反省を行え。
                    1. 軸に据えた中穴馬（4〜8番人気）の成否と、3連複50倍以上の決着になったかどうかのオッズ検証。
                    
                    【提出された現在の予想指示書】
                    {st.session_state["res"]}
                    
                    【実際のレース結果（コピペデータ）】
                    {race_result_input}
                    """
                    response = model.generate_content(review_prompt)
                    st.session_state["res"] = response.text
                st.rerun()
            except Exception as e:
                st.error(f"反省解析エラー: {e}")

    st.divider()

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
                
                prompt = f"""
                【今回の馬柱・オッズデータ（netkeiba分析情報含む）】
                {manual_data}
                
                【⚙️ 総監督絶対厳守ロジック：netkeiba「データ上位馬3頭」スクリーニング】
                1. 「データ上位馬3頭」セクションの馬は強力な適性馬。
                   - ただし、単勝オッズが【 {min_odds} 倍以下 】の安い人気馬は、1列目（軸）および2列目に配置することを【完全に禁止】とする。一律で3列目の紐（保険）に落とすか、完全除外（消し）にせよ。
                2. 「データ上位馬3頭」の中で、単勝オッズが【 {min_odds} 倍超 】を満たす4番人気〜8番人気前後の伏兵を、本レースの【絶対の本命軸（◎）】に据えよ。

                【⚙️ 総監督絶対厳守ロジック：3連複「最低50倍以上」限定フィルター】
                買い目を構築する際、配当が安くなる組み合わせ（例：上位人気同士が紐で絡み、3連複の想定配当が50倍未満になるような組み合わせ）は、投資効率が極めて悪いため【最初から買い目から完全に排除（間引き）】せよ。
                必ず「中穴（4〜8人気） → 中穴（4〜8人気） → 大穴・最下位（7〜11人気・最下位）」のラインを意識し、的中時に確実に【50倍（5,000円）以上、および万馬券〜十万馬券】となる尖った15点を構築すること。

                【投資指示書：出力フォーマット】
                AIの最終結論として、以下の3つの高回収率データを必ず提示せよ。

                1. 🎯 【裏・波乱特化型 3連複15点フォーメーション（想定配当50倍〜万馬券限定）】
                   - 1列目（軸・1頭）: 単勝オッズ【 {min_odds} 倍超 】の4〜8番人気から、データ上位・バイアス最適馬を1頭厳選（絶対に安い上位人気は置かない）。
                   - 2列目（紐・2頭）: 同じく4〜8番人気ゾーンの残りの伏兵から2頭選定。
                   - 3列目（大穴・6頭）: 7〜11番人気、最下位人気、死んだふり末脚爆弾馬、および「1番人気を保険で入れる場合は3列目に1頭だけ（ただし50倍以上の組み合わせが維持できる場合のみ）」を含めた6頭で【ぴったり15点】を構築。

                2. 🤝 【中穴直撃 ワイド3点】
                   - 4〜8番人気ゾーン（単勝 {min_odds} 倍超）の有力馬3頭によるボックス（計3点）。安い上位人気は一切排除。

                3. 🐎 【主導権強奪 馬連4点】
                   - 1列目に指定した4〜8番人気の軸馬から、データ上位馬や展開利のある馬へ流す高オッズ狙いの4点。

                【指示】
                上記のオッズ制限および「3連複50倍以上厳守」のロジックを思考に統合し、全頭を精密に診断せよ。
                出力は必ず以下のMarkdownテーブル形式で行うこと：
                | 馬番 | 馬名 | 単勝勝率(%) | 複勝勝率(%) | ダート砂適性 | 脚質 | 人気（オッズ） | 評価 | 診断コメント（オッズフィルター・50倍以上選定の有無を明記） |
                | --- | --- | --- | --- | --- | --- | --- | --- | --- |
                
                最後に、上記【3連複15点（50倍以上保証）】【ワイド3点】【馬連4点】の買い目を総監督への【投資指示書】として結論提示せよ。
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

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
    
    # 期待値フィルター設定
    st.header("💰 期待値フィルター設定")
    min_odds = st.number_input(
        "一般馬を軸から除外する単勝オッズのしきい値", 
        min_value=1.0, 
        max_value=20.0, 
        value=4.0, 
        step=0.5
    )
    st.caption(f"💡 現在の設定: 指定馬以外の一般馬で単勝 {min_odds} 倍以下の馬は軸から除外。")

    st.divider()
    
    # 📸 スクショ馬指定
    st.header("📸 画面スクショ・データ連動")
    img1_top_horses = st.text_input("1枚目：データ上位馬（例: 1, 5）", value="1, 5")
    img2_track_horses = st.text_input("2枚目：レース間隔実績馬（例: 8, 10）", value="8, 10")

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
manual_data = st.text_area("✍️ 次回の馬柱・オッズデータ入力", height=300)

if st.button("🚀 統合解析実行"):
    if not api_key: 
        st.error("APIキーを入力してください")
    else:
        try:
            with st.spinner("統合解析中..."):
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel('gemini-2.5-flash')
                
                prompt = f"""
                【今回の馬柱・オッズデータ】
                {manual_data}
                
                【📸 スクショ最優先連動データ】
                - スクショ1（データ上位馬）：馬番 【 {img1_top_horses} 】 
                - スクショ2（レース間隔実績馬）：馬番 【 {img2_track_horses} 】

                【❌ 絶対厳守：オッズフィルターの例外ルール】
                1. スクショ1で指定された馬番（【 {img1_top_horses} 】）は、単勝オッズが {min_odds} 倍以下（4.0倍ジャスト等）であっても、上位適性馬として【絶対に買い目（1列目・2列目）から排除してはならない】。
                2. ただし、スクショ1に含まれない「普通の馬」で、単勝オッズが {min_odds} 倍以下の過剰人気馬（例：1.3倍の6番など）は、1列目・2列目への配置を【一斉禁止】とする。

                【💰 3連複「最低50倍以上」限定フォーメーション構築法】
                本レースは軸（1番・5番）の時点で十分な好配当が担保されている。そのため、3列目（紐）には中穴・大穴である【 1番、2番、3番 】を配置しても50倍未満に落ちるリスクはない。AIの独断でこれらを紐から除外することを禁止する。
                
                以下のフォーメーション枠に正確に馬番をハメ込み、ぴったりの「15点」を構築せよ。

                - 1列目（軸・1頭）: 【 1 】（データ上位・7番人気）を完全固定。
                - 2列目（軸・1頭）: 【 5 】（データ上位・2番人気）を完全固定。
                - 3列目（紐・6頭）: 【 6、8、10、2、3、4 】 
                  ※バル総監督の指示により、1番（自身）、2番、3番の紐入れを完全容認。1番人気6番は3列目の保険としてのみ配置。

                【投資指示書：出力フォーマット】
                以下の構成で、バル総監督への最終レポートを出力せよ。

                1. 📊 【画像連動型 全頭精密診断テーブル】
                   必ず以下のMarkdownテーブル形式で全頭を評価すること。5番が消えていないこと、および1, 2, 3番が紐として正しく評価されているかをコメントに明記せよ。
                   | 馬番 | 馬名 | 人気（オッズ） | 評価 | 診断コメント |

                2. 🎯 【裏・波乱特化型 3連複15点フォーメーション（想定配当50倍〜万馬券限定）】
                   - 1列目: 1
                   - 2列目: 5
                   - 3列目: 6, 8, 10, 2, 3, 4
                   ※この組み合わせで展開される「計15点」の買い目をすべて具体的（例：1-5-6）に書き出せ。

                3. 🤝 【中穴直撃 ワイド3点】
                   - 1, 5, 8 のボックス（計3点）

                4. 🐎 【主導権強奪 馬連4点】
                   - 1 から 5, 4, 8, 9 への流し（計4点）
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

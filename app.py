import streamlit as st
import google.generativeai as genai
import re

st.set_page_config(page_title="Baru競馬AI Pro", layout="wide")

# ====================================================================
# 💾 全自動記憶システム（セッション状態の初期化）
# ====================================================================
if "api_key" not in st.session_state:
    st.session_state.api_key = ""
if "analysis_criteria" not in st.session_state:
    st.session_state.analysis_criteria = (
        "• JRA/地方競馬の高速馬場・トラックバイアス\n"
        "• 芝・ダートのキレ\n"
        "• 走破タイム理論（基準タイム・馬場補正）\n"
        "• 上がり3F\n"
        "• 展開・ハナ争い"
    )
if "review_input" not in st.session_state:
    st.session_state.review_input = ""
if "raw_input" not in st.session_state:
    st.session_state.raw_input = ""

# ====================================================================
# 🛠️ サイドバー：総監督司令部（自動記憶対応）
# ====================================================================
st.sidebar.markdown("## ⚙️ 総監督司令部")

st.session_state.api_key = st.sidebar.text_input(
    "Gemini API KEY", 
    value=st.session_state.api_key,
    type="password"
)

st.sidebar.markdown("---")
st.sidebar.markdown("### 🎯 統合解析基準（常時適用）")
st.session_state.analysis_criteria = st.sidebar.text_area(
    "解析基準プロンプト", 
    value=st.session_state.analysis_criteria, 
    height=120
)

st.sidebar.markdown("---")
st.sidebar.markdown("### 🔍 過去レース復習解析（復活）")
st.session_state.review_input = st.sidebar.text_area(
    "復習用の過去レース結果・パドック等のメモ",
    value=st.session_state.review_input,
    height=150,
    placeholder="過去のタイムや、前走の不利などのメモをここに記憶させます"
)

if st.sidebar.button("🛠️ 設定と復習データを強制保存", use_container_width=True):
    st.sidebar.success("すべてのデータを記憶しました！")


# ====================================================================
# 🎯 メイン画面：Baru競馬AI Pro 解析エンジン
# ====================================================================
st.title("🎯 Baru競馬AI Pro — 地方・中央 走破理論解析")

st.session_state.raw_input = st.text_area(
    "netkeibaの出馬表をコピペしてください", 
    value=st.session_state.raw_input,
    height=180,
    placeholder="ここにレース名や出馬表をそのまま貼り付けてください"
)

if st.button("レース解析エンジン起動", use_container_width=True):
    if not st.session_state.api_key:
        st.error("❌ 総監督司令部に Gemini API KEY を入力してください！")
    elif not st.session_state.raw_input:
        st.warning("⚠️ 出馬表データが空っぽです。netkeiba等のデータを貼り付けてください。")
    else:
        with st.spinner("🧠 走破理論AIエンジンがコピペデータを深層解析中..."):
            try:
                # Gemini APIの初期化
                genai.configure(api_key=st.session_state.api_key)
                model = genai.GenerativeModel('gemini-1.5-pro')
                
                # 記憶されたすべてのデータをプロンプトに統合
                prompt = f"""
あなたは競馬予想のプロフェッショナルAI「Baru競馬AI Pro」の解析エンジンです。
以下の【統合解析基準】と【復習データ・メモ】をベースに、コピペされた【出馬表データ】をパース・解析し、走破タイム理論に基づいた診断を行ってください。

【統合解析基準】
{st.session_state.analysis_criteria}

【復習データ・メモ（前走不利やパドック情報など）】
{st.session_state.review_input}

【コピペされた出馬表データ】
{st.session_state.raw_input}

---
【出力ルール】
1. 必ずコピペされた出馬表の「正しいレース名・条件」を冒頭に抽出して表示すること（例: 船橋11R 富里特別）。
2. コピペされた馬枠・馬名・騎手を正確にすべて網羅して診断すること。固定のテストデータは絶対に出さないこと。
3. 各馬の評価（◎, 〇, ▲, ☆, △, 消）を打ち、勝率・複勝率（パーセント）、展開適性、血統、オッズ、および「走破AI展開指示（詳細な見解）」を出力してください。
4. 最後に、それらの評価を元にした「3連複フォーメーション」の具体的な買い目（1列目、2列目、3列目）と合計点数をシミュレーションして提示してください。
5. Markdownの綺麗な見出しや絵文字を使って、ユーザーがパッと見て scannable（見やすい）なレイアウトに整えてください。
"""

                # AI解析の実行
                response = model.generate_content(prompt)
                
                # 結果表示
                st.markdown("---")
                st.success("📊 解析完了！現在のコピペデータに基づく最新の予想です。")
                
                if st.session_state.review_input:
                    st.caption(f"ℹ️ **総監督司令部からの復習メモを解析に反映しました:** {st.session_state.review_input[:40]}...")
                
                # Geminiからの出力をそのまま画面にレンダリング
                st.markdown(response.text)
                
            except Exception as e:
                st.error(f"解析中にエラーが発生しました: {e}")

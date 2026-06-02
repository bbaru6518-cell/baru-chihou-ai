import streamlit as st
import google.generativeai as genai

st.set_page_config(page_title="Baru競馬AI Pro", layout="wide")

# ====================================================================
# 💾 全自動記憶システム（セッション状態の初期化）
# ====================================================================
if "api_key" not in st.session_state:
    st.session_state.api_key = ""
if "analysis_criteria" not in st.session_state:
    st.session_state.analysis_criteria = (
        "• JRA/地方競馬の高速馬場・トラックバイアス・砂厚の補正\n"
        "• 走破タイム理論（基準タイム・馬場補正・ハイペース/スロー展開予測）\n"
        "• 上がり3Fのキレとスタミナ持続力\n"
        "• netkeibaデータ分析（コース・距離・馬場・間隔）の完全システム連動"
    )
if "review_input" not in st.session_state:
    st.session_state.review_input = (
        "【🔥 バル式・4大特化データ強制ハメ込み黄金律】\n"
        "1.『このコースが得意な馬』 2.『この距離が得意な馬』\n"
        "3.『この競馬場が得意な馬』 4.『今回の馬場状態が得意な馬』\n\n"
        "【🚨 1番人気データ圏外の危険シグナル検知】\n"
        "・単勝1番人気が、上記の4大特化データ（上位3頭）に1つもランクインしていない場合は【極めて危険な過剰人気馬】と判定せよ。\n\n"
        "【⚠️ レース間隔の鉄の掟】\n"
        "・『今回のレース間隔で実績がある馬』に名前がある馬は、人気に関わらず必ず【軸】または【紐（相手）】に100%組み込むこと。\n\n"
        "【💣 ★超重要：地方・高知爆穴救出ロジック】\n"
        "・船橋、川崎、大井、および高知ファイナルレース等では、最下位人気馬の激走確率が跳ね上がるため、AIの独自の判断での消去を厳禁とする。\n"
        "・出走馬の中から【ブービー（最下位から2番目）】および【最下位人気】を含めた【下位人気から数えて3頭】を自動で割り出し、3連複フォーメーションの【3列目（紐）】に必ず強制的に全頭組み込むこと！"
    )
if "raw_input" not in st.session_state:
    st.session_state.raw_input = ""

# ====================================================================
# 🛠️ サイドバー：総監督司令部
# ====================================================================
st.sidebar.markdown("## ⚙️ 総監督司令部")
st.session_state.api_key = st.sidebar.text_input("Gemini API KEY", value=st.session_state.api_key, type="password")

st.sidebar.markdown("---")
st.sidebar.markdown("### 🎯 統合解析基準（常時適用）")
st.session_state.analysis_criteria = st.sidebar.text_area("解析基準プロンプト", value=st.session_state.analysis_criteria, height=120)

st.sidebar.markdown("---")
st.sidebar.markdown("### 🔍 バル式・爆穴救出＆間隔必勝黄金律")
st.session_state.review_input = st.sidebar.text_area("過去レースからの教訓・絶対条件", value=st.session_state.review_input, height=270)

if st.sidebar.button("🛠️ 設定と必勝データを強制保存", use_container_width=True):
    st.sidebar.success("爆穴救出ロジックをAIに完全同期しました！")

# ====================================================================
# 🎯 メイン画面：Baru競馬AI Pro 解析エンジン
# ====================================================================
st.title("🎯 Baru競馬AI Pro — 爆穴紐ハメ込みシステム")
st.markdown("##### ※netkeibaの出馬表から、下の『データ分析』の項目まで丸ごとコピーして貼り付けてください。")

st.session_state.raw_input = st.text_area(
    "出馬表 ＋ 特化データ分析をここにペースト", 
    value=st.session_state.raw_input,
    height=250,
    placeholder="出馬表データを貼り付けると、AIが自動で人気順を解析し、最下位含む下位3頭を自動で紐にセットします。"
)

if st.button("レース解析エンジン起動", use_container_width=True):
    if not st.session_state.api_key:
        st.error("❌ 総監督司令部に Gemini API KEY を入力してください！")
    elif not st.session_state.raw_input:
        st.warning("⚠️ データが空っぽです。データを貼り付けてください。")
    else:
        with st.spinner("🧠 人気順位をスキャン中... 最下位人気3頭を紐へ強制配置しています..."):
            try:
                genai.configure(api_key=st.session_state.api_key)
                model = genai.GenerativeModel('gemini-2.5-pro')
                
                prompt = f"""
あなたは競馬予想のプロフェッショナルAI「Baru競馬AI Pro」の解析エンジンです。
バルさんが提供した【コピペデータ】から、人気順（〇人気という表記）を正確に読み取り、以下のルールを完全に厳守して出力してください。

【統合解析基準】
{st.session_state.analysis_criteria}

【超重要！バル式・データ必勝黄金律（絶対に破ってはならない掟）】
{st.session_state.review_input}

【バルさんが提供したコピペデータ（出馬表＋データ分析情報）】
{st.session_state.raw_input}

---
【AI解析・プログラミング指示（省略厳禁）】
1. 【最下位人気3頭の自動特定】: 出馬表のオッズ・人気データから、最も人気がない馬（例：9頭立てなら9人気、8人気、7人気）を3頭正確にピックアップし、ログとして「💣 【爆穴救出】下位3頭（〇番、〇番、〇番）を自動検知しました」と出力してください。
2. 【全頭診断】: 1番から最終頭数まで省略せず1頭ずつ見解を書き下してください。下位3頭については「バル式爆穴ロジックにより紐固定」と明記すること。
3. 【買い目の出力】: 3連複フォーメーションの【3列目（紐）】には、AI自身の評価に関わらず、特定した「最下位人気から3頭」を必ず100%全頭追加して買い目を構築してください。
"""

                response = model.generate_content(prompt)
                
                st.markdown("---")
                st.success("📊 バル式・爆穴救出＆特化データ完全同期解析が完了しました！")
                st.markdown(response.text)
                
            except Exception as e:
                st.error(f"解析中にエラーが発生しました: {e}")

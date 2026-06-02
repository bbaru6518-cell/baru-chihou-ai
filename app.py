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
        "コピペデータ内から以下の4ファクターを最優先で抽出すること：\n"
        "1.『このコースが得意な馬』 2.『この距離が得意な馬』\n"
        "3.『この競馬場が得意な馬』 4.『今回の馬場状態が得意な馬』\n\n"
        "【🚨 1番人気データ圏外の危険シグナル検知】\n"
        "・単勝1番人気（あるいは単勝1倍台〜2倍台前半の圧倒的人気馬）が、上記の4大特化データ（上位3頭）に1つもランクインしていない場合は【極めて危険な過剰人気馬】と判定せよ。\n"
        "・この条件に合致した場合、AIはその1番人気馬への◎評価を禁止し、評価を『消し』または『▲（単穴）』以下に叩き落とすこと。同時に、レース全体の波乱度を『高（大波乱）』に設定し、データ上位馬を軸とした高配当フォーメーションを組むこと。\n\n"
        "【⚠️ レース間隔の鉄の掟】\n"
        "・『今回のレース間隔で実績がある馬』に名前がある馬は、激走確率が極めて高いため、人気に関わらず必ず【軸】または【紐（相手）】のフォーメーション内に100%強制的に組み込むこと！"
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
st.sidebar.markdown("### 🔍 バル式・危険馬検知＆間隔必勝黄金律")
st.session_state.review_input = st.sidebar.text_area("過去レースからの教訓・絶対条件", value=st.session_state.review_input, height=250)

if st.sidebar.button("🛠️ 設定と必勝データを強制保存", use_container_width=True):
    st.sidebar.success("危険馬検知ロジックをAIに完全同期しました！")

# ====================================================================
# 🎯 メイン画面：Baru競馬AI Pro 解析エンジン
# ====================================================================
st.title("🎯 Baru競馬AI Pro — 危険人気馬パージシステム")
st.markdown("##### ※netkeibaの出馬表から、下の『データ分析』の項目（上位3頭、今週のレース傾向など）まで丸ごとコピーして貼り付けてください。")

st.session_state.raw_input = st.text_area(
    "出馬表 ＋ 特化データ分析をここにペースト", 
    value=st.session_state.raw_input,
    height=250,
    placeholder="『このコースが得意な馬』『今回のレース間隔で実績がある馬』などのテキストが含まれるように貼り付けてください。"
)

if st.button("レース解析エンジン起動", use_container_width=True):
    if not st.session_state.api_key:
        st.error("❌ 総監督司令部に Gemini API KEY を入力してください！")
    elif not st.session_state.raw_input:
        st.warning("⚠️ データが空っぽです。データを貼り付けてください。")
    else:
        with st.spinner("🧠 1番人気のデータ盲点チェック ＆ 間隔実績馬の配置を実行中..."):
            try:
                genai.configure(api_key=st.session_state.api_key)
                model = genai.GenerativeModel('gemini-2.5-pro')
                
                prompt = f"""
あなたは競馬予想のプロフェッショナルAI「Baru競馬AI Pro」の解析エンジンです。
バルさんが提供した【コピペデータ】から、以下の【危険馬検知ロジック】を最優先で実行し、買い目を構築してください。

【統合解析基準】
{st.session_state.analysis_criteria}

【超重要！バル式・データ必勝黄金律（絶対に破ってはならない掟）】
{st.session_state.review_input}

【バルさんが提供したコピペデータ（出馬表＋データ分析情報）】
{st.session_state.raw_input}

---
【AI解析・プログラミング指示】
1. 【1番人気チェック機能】: 出馬表の「1人気」となっている馬を特定してください。その後、データ分析欄の「このコースが得意」「この距離が得意」「この競馬場が得意」「今回の馬場状態が得意」の各大項目（上位3頭）に、その1番人気馬の名前（略称含む）があるか徹底的にスキャンしてください。
2. 【危険馬の自動排除】: もし1番人気馬が上記の4大データ上位3頭に【1つも入っていない】場合、その馬は地方のタフな馬場やバイアスに適合していない「名前だけの過剰人気馬（地雷馬）」です。AIは即座に警告文（例：「🚨 警告：1番人気馬〇〇はデータ上位に不在！危険な過剰人気馬と判定しました」）を出力し、その馬の評価を大幅に下げてください。
3. 【レース間隔実績馬の強制セット】: 「今回のレース間隔で実績がある馬」の欄にある馬は激走確率が極めて高いため、必ず【軸】または【紐（相手）】として買い目に100%残してください。
4. 【買い目の出力】: 危険な1番人気をハズしたことで跳ね上がる配当を仕留めるため、データ上位馬とレース間隔実績馬を絡めた「3連複フォーメーション」を正確に提示してください。
"""

                response = model.generate_content(prompt)
                
                st.markdown("---")
                st.success("📊 バル式・危険馬検知＆特化データ完全同期解析が完了しました！")
                st.markdown(response.text)
                
            except Exception as e:
                st.error(f"解析中にエラーが発生しました: {e}")

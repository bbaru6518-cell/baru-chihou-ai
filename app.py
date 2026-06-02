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
        "・船橋、川崎、大井、および高知ファイナルレース等では、最下位人気馬の激走確率が跳ね上がるため、出走馬の中から【下位人気から数えて3頭】を自動で割り出し、3連複フォーメーションの【3列目（紐）】に必ず強制的に全頭組み込むこと！"
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
st.sidebar.markdown("### 🔍 バル式・最強必勝黄金律（強制記憶）")
st.session_state.review_input = st.sidebar.text_area("過去レースからの教訓・絶対条件", value=st.session_state.review_input, height=250)

if st.sidebar.button("🛠️ 設定と必勝データを強制保存", use_container_width=True):
    st.sidebar.success("色彩装飾＆脚質パース機能をAIに完全同期しました！")

# ====================================================================
# 🎯 メイン画面：Baru競馬AI Pro 解析エンジン
# ====================================================================
st.title("🎯 Baru競馬AI Pro — カラー視覚特化・完全復活版")
st.markdown("##### ※netkeibaの出馬表から、下の『データ分析』の項目まで丸ごとコピーして貼り付けてください。")

st.session_state.raw_input = st.text_area(
    "出馬表 ＋ 特化データ分析をここにペースト", 
    value=st.session_state.raw_input,
    height=250,
    placeholder="出馬表データを貼り付けると、AIが自動で人気順・騎手・オッズ・脚質を識別し、カラー色分けされた診断画面を出力します。"
)

if st.button("レース解析エンジン起動", use_container_width=True):
    if not st.session_state.api_key:
        st.error("❌ 総監督司令部に Gemini API KEY を入力してください！")
    elif not st.session_state.raw_input:
        st.warning("⚠️ データが空っぽです。データを貼り付けてください。")
    else:
        with st.spinner("🧠 カラーレンダリング適用中... 脚質・騎手・オッズを鮮やかに色分けしています..."):
            try:
                genai.configure(api_key=st.session_state.api_key)
                model = genai.GenerativeModel('gemini-2.5-pro')
                
                prompt = f"""
あなたは競馬予想のプロフェッショナルAI「Baru競馬AI Pro」の解析エンジンです。
バルさんが提供した【コピペデータ】から、人気、オッズ、騎手、そして【脚質（逃・先・差・追）】を正確に読み取り、以下の【超美麗・カラーHTML出力フォーマット】を絶対に崩さずに最後まで出力してください。

【統合解析基準】
{st.session_state.analysis_criteria}

【超重要！バル式・データ必勝黄金律（絶対に破ってはならない掟）】
{st.session_state.review_input}

【バルさんが提供したコピペデータ（出馬表＋データ分析情報）】
{st.session_state.raw_input}

---
【出力フォーマット・構造指示（Markdown内でのHTML装飾を徹底すること）】

### 🚨 【バル式・危険馬判定】
- 対象の1番人気馬がデータ上位にいるか検証し、結果を報告してください。

### 📋 【バル式・全頭診断（カラー視覚特化版）】
出走するすべての馬（1番から最終頭数まで）について、以下のHTML装飾ルールを完全に適用して1頭ずつすべて書き下してください。

【🎨 カラー装飾・脚質表記ルール】
1. 各馬のタイトルは「### **X番 [馬名] 【[脚質]】**」とし、コピペデータから読み取った脚質（逃・先・差・追）を必ず入れること。
2. 人気・単勝オッズは、目立つように赤文字 `<span style="color:#ff3333; font-weight:bold;">〇人気 / 単勝〇.〇倍</span>` で表記すること。
3. 騎手名は、青文字 `<span style="color:#1e90ff; font-weight:bold;">[騎手名]</span>` で表記すること。
4. 特記すべき【秋元】騎手、または激走確率の極めて高いバル式爆穴ロジックに該当する下位3頭には、タイトルのすぐ下に `<div style="background-color:#ffe4e1; border-left:5px solid #ff3333; padding:10px; font-weight:bold; color:#ff3333;">🚨バル式・超警戒爆穴ハメ込み馬（紐固定）🚨</div>` という目立つカラーボックスを必ず出力すること。

【馬ごとの出力テンプレート】
### **X番 [馬名] 【[脚質]】**
- **ステータス:** <span style="color:#ff3333; font-weight:bold;">〇人気 / 単勝〇.〇倍</span> ／ 騎手: <span style="color:#1e90ff; font-weight:bold;">[騎手名]</span>
- **該当データ:** [該当する特化データを記載]
- **理論的見解:** [走破タイム・展開・馬場バイアスからの見解を詳細に]

### 🎯 【バル式・最終フォーメーション】
- 「レース間隔で実績がある馬」および「最下位人気から3頭の爆穴馬」を100%完全にハメ込んだ【3連複フォーメーション】の買い目を正確に提示してください。
"""

                response = model.generate_content(prompt)
                
                st.markdown("---")
                st.success("📊 バル式・カラー色分け＆脚質表記の完全復活版解析が完了しました！")
                
                # HTMLタグをStreamlit上で正常に色付け表示させるために unsafe_allow_html=True を使用
                st.markdown(response.text, unsafe_allow_html=True)
                
            except Exception as e:
                st.error(f"解析中にエラーが発生しました: {e}")

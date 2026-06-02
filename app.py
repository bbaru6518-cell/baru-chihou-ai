import streamlit as st
from parser import parse_netkeiba_complete

st.set_page_config(page_title="Baru競馬AI Pro", layout="wide")

# ====================================================================
# 🛠️ サイドバー：総監督司令部（スクリーンショット 2026-06-02 152350.png を完全再現）
# ====================================================================
st.sidebar.markdown("## ⚙️ 総監督司令部")

# Gemini API KEY 入力枠
gemini_key = st.sidebar.text_input("Gemini API KEY", type="password", help="GeminiのAPIキーを入力してください")

st.sidebar.markdown("---")

# 🎯 統合解析基準（常時適用）
st.sidebar.markdown("### 🎯 統合解析基準（常時適用）")
default_criteria = (
    "以下の要素を全頭診断に統合せよ：\n\n"
    "• JRA/地方競馬の高速馬場・トラックバイアス\n"
    "• 芝・ダートのキレ\n"
    "• 走破タイム理論（基準タイム・馬場補正）\n"
    "• 上がり3F\n"
    "• 展開・ハナ争い"
)
analysis_criteria = st.sidebar.text_area(
    label="解析基準プロンプト",
    value=default_criteria,
    height=250,
    label_visibility="collapsed" # スクショ通りラベルなしでスッキリ表示
)

st.sidebar.markdown("---")

# 📁 過去ログ・結果復習ルーム
st.sidebar.markdown("### 📁 過去ログ・結果復習ルーム")
st.sidebar.caption("復習・確認する過去の予想")
past_log_selection = st.sidebar.selectbox(
    "過去ログ選択",
    options=["No options to select"],
    label_visibility="collapsed"
)
if st.sidebar.button("📖 予想指示書を呼び出す"):
    st.sidebar.info("過去ログ機能は現在準備中です。")


# ====================================================================
# 🎯 メイン画面：Baru競馬AI Pro 解析エンジン
# ====================================================================
st.title("🎯 Baru競馬AI Pro — 地方・中央 走破理論解析")
raw_input = st.text_area("netkeibaの出馬表をコピペしてください", height=300)

# 解析・フォーメーション計算ボタン
if st.button("レース解析エンジン起動", width="stretch"):
    inp = raw_input.strip()
    if not inp:
        st.warning("データを入力してください。")
    else:
        # parser.py からデータをパース
        res = parse_netkeiba_complete(inp)
        entries = res["horses"]
        r_info = res["race_info"]
        
        if not entries:
            st.error("馬データが見つからない、またはパースに失敗しました。コピペの範囲を確認してください。")
        else:
            # メイン画面側にパース結果と解析結果を綺麗に並べて表示
            st.markdown("---")
            st.markdown(f"## 📊 レース舞台: {r_info['race_name']}")
            st.info(f"**確定条件:** {r_info['track_type']}{r_info['distance']}m")
            
            # 【新・メイン側表示】パースされた馬データ一覧を確認用に出力
            st.markdown("### 🐎 出走馬データ（パース結果）")
            cols = st.columns(2) # 2列でスッキリ表示
            for idx, h in enumerate(entries):
                with cols[idx % 2]:
                    with st.expander(f"[{h['waku']}枠] {h['uma_ban']:02d} {h['horse_name']}"):
                        st.write(f"**騎手:** {h['jockey']} | **脚質:** {h['leg_type']}")
                        st.write(f"**オッズ:** {h['odds']} ({h['popularity']}人気) | **体重:** {h['weight']}kg")
            
            st.markdown("---")
            st.markdown("### 🎯 レース解析・フォーメーション結果")
            st.write("**【📊 レース構造解析】** 波乱度: 45点 -> ⚖️ 平穏〜中波乱（良馬場時計勝負）")
            
            # 軸・相手・穴の自動振り分け logic
            jiku, aite, ana = [], [], []
            for h in entries:
                if h['popularity'] <= 2: 
                    jiku.append(h['uma_ban'])
                elif h['popularity'] <= 5: 
                    aite.append(h['uma_ban'])
                else:
                    ana.append(h['uma_ban'])

            st.markdown("#### 🎯 Baru式フォーメーション（3連複）")
            st.code(f"1列目(軸)  : {jiku}\n2列目(相手): {aite}\n3列目(穴紐)  : {ana}", language="text")
            
            # 組み合わせ計算
            tkts = []
            for h1 in jiku:
                for h2 in aite:
                    for h3 in ana:
                        if h1 != h2 and h2 != h3 and h1 != h3:
                            comb = sorted([h1, h2, h3])
                            if comb not in tkts: 
                                tkts.append(comb)
            
            st.write(f"**合計購入点数:** {len(tkts)} 点")
            
            # 買い目をトグルにまとめてスッキリさせる
            with st.expand_to_see_all_bets("📝 生成された買い目一覧（コピー用）" if hasattr(st, "expand_to_see_all_bets") else st.expander("📝 生成された買い目一覧（コピー用）")):
                for i, t in enumerate(tkts, 1):
                    st.code(f"[{i:02d}] {t[0]}-{t[1]}-{t[2]}")

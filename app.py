import re
import streamlit as st
import google.generativeai as genai
import json
import os
import datetime

# --- 設定（ワイドモードで2画面構成を美しく配置） ---
LOG_DIR = "racing_logs_chihou"
os.makedirs(LOG_DIR, exist_ok=True)
st.set_page_config(page_title="Baru 地方競馬AI Pro", layout="wide")

# ==============================================================================
# 1. ⚙️ サイドバー：過去ログ・結果復習ルーム
# ==============================================================================
with st.sidebar:
    st.button("💾 設定保存")
    st.write("")
    st.header("📂 過去ログ・結果復習ルーム")
    st.caption("復習・確認する過去の予想")
    
    # 過去ログファイルの取得
    log_files = sorted([f for f in os.listdir(LOG_DIR) if f.endswith(".txt")], reverse=True)
    if log_files:
        selected_log = st.selectbox("予想ログ選択", log_files, label_visibility="collapsed")
        if st.button("📖 予想指示書を呼び出す"):
            with open(os.path.join(LOG_DIR, selected_log), "r", encoding="utf-8") as f:
                st.session_state["res"] = f.read()
            st.rerun()
    else:
        st.info("過去ログはまだありません")

    st.write("---")

    # レース結果コピペ投入エリア（機能完全維持）
    st.header("🏁 レース結果のコピペ投入")
    st.caption("💡 1行目にレース名を入力し、2行目から結果を丸ごとコピペしてください！")
    race_result_input = st.text_area("1行目：レース名／2行目〜：結果コピペ", height=150, label_visibility="collapsed")
    st.caption("コーナー通過順位の見方")
    st.text_area("レース別馬メモ", height=100)
    
    # API KEYの入力（隠し入力）
    api_key = st.text_input("Gemini API KEY", type="password", placeholder="AI解析に必須です")
    
    # 互換性エラーの起きない安全なボタン幅設定
    if st.button("🔮 実際の着順・ハナ争いと照合して復習", use_container_width=True):
        if not api_key:
            st.error("APIキーを入力してください")
        elif not race_result_input:
            st.error("結果データをコピペしてください")
        elif "res" not in st.session_state:
            st.error("まずメイン画面で過去ログを呼び出すか、予想を実行して『現在の予想指示書』を表示させてください")
        else:
            try:
                with st.spinner("実際のレース結果と照合し、反省会を実施中..."):
                    genai.configure(api_key=api_key)
                    model = genai.GenerativeModel('gemini-2.5-flash')
                    
                    # 最初の1行目を安全に取得
                    race_name = race_result_input.splitlines()[0] if race_result_input.splitlines() else "対象レース"
                    current_res = st.session_state["res"]
                    
                    # f-stringのエラーを完全に防ぐため、プレーンな文字列としてプロンプトを結合
                    review_prompt = "【総監督からの命令：レース結果の答え合わせと徹底反省】\n\n"
                    review_prompt += "あなたが先ほど出力した【予想指示書】と、実際に発生した【レース結果・着順】を照合し、以下の基準で猛反省（回回）を行え。\n\n"
                    review_prompt += "1. 軸馬（◎, ○, ▲）の成否\n - 軸に据えた馬は馬券圏内（3着以内）にきたか？\n - netkeibaの「データ上位馬3頭」の信頼度はどうだったか？\n\n"
                    review_prompt += "2. 「死んだふり下剋上穴馬」の生存確認\n - あなたが「上がり最速爆弾馬」や「激走警戒馬（注）」として救済・指名した不人気馬の実際の着順・上がり3Fを確認せよ。\n - 実際に激走したか？ 凡走した場合、展開（スローペース等）やトラックバイアスがどう影響したか推測せよ。\n\n"
                    review_prompt += "3. 展開・ハナ争いの答え合わせ\n - 事前に想定したハナ争いやペース（ハイ・ミドル・スロー）は、実際の展開と一致していたか？\n\n"
                    review_prompt += f"【提出された現在の予想指示書】\n{current_res}\n\n"
                    review_prompt += f"【実際のレース結果（コピペデータ）】\n{race_result_input}\n\n"
                    review_prompt += f"【出力フォーマット】\n### 🏁 {race_name} - 統合反省レポート\n"

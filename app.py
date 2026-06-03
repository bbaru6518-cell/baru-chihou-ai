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
                    
                    review_prompt = f"""
                    【総監督からの命令：レース結果の答え合わせと徹底反省】
                    
                    あなたが先ほど出力した【予想指示書】と、実際に発生した【レース結果・着順】を照合し、以下の基準で猛反省（回顧）を行え。
                    
                    1. 軸馬（◎, ○, ▲）の成否
                       - 軸に据えた馬は馬券圏内（3着以内）にきたか？
                       - netkeibaの「データ上位馬3頭」の信頼度はどうだったか？
                    
                    2. 「死んだふり下剋上穴馬」の生存確認
                       - あなたが「上がり最速爆弾馬」や「激走警戒馬（注）」として救済・指名した不人気馬の実際の着順・上がり3Fを確認せよ。
                       - 実際に激走したか？ 凡走した場合、展開（スローペース等）やトラックバイアスがどう影響したか推測せよ。
                    
                    3. 展開・ハナ争いの答え合わせ
                       - 事前に想定したハナ争いやペース（ハイ・ミドル・スロー）は、実際の展開と一致していたか？
                    
                    【提出された現在の予想指示書】
                    {st.session_state["res"]}
                    
                    【実際のレース結果（コピペデータ）】
                    {race_result_input}
                    
                    【出力フォーマット】
                    ### 🏁 {race_result_input.splitlines()[0] if race_result_input.splitlines() else '対象レース'} - 統合反省レポート
                    - **総合評価**: （例：大的中 / 軸は合致も紐抜け / 展開不一致による大敗 など）
                    
                    #### 📊 着順答え合わせ
                    | 印 | 馬名 | 事前評価 | 実際の着順 | 上がり3F（結果） | 反省・要因分析 |
                    | --- | --- | --- | --- | --- | --- |
                    
                    #### 🧠 次回に向けたロジック修正点（総監督への進言）
                    - （教訓を箇条書きで書くこと）
                    """
                    response = model.generate_content(review_prompt)
                    st.session_state["res"] = response.text
                st.rerun()
            except Exception as e:
                st.error(f"反省解析エラー: {e}")

# ==============================================================================
# 2. 🏛️ メインエリア：スクショ通りの2連カラムレイアウト
# ==============================================================================
st.title("🏇 Baru 地方競馬AI Pro - 【Ver 24.8.5 高速・軽量化安定版】")
st.write("")

# 画面を綺麗に左右2分割
col1, col2 = st.columns([1, 1])

# --- 2-A. 左側：データ入力・送信セクション ---
with col1:
    st.header("📋 地方競馬 過去馬柱・オッズ混在 テキスト入力")
    st.text_input("🔗 地方レースURL（netkeiba等）")
    
    manual_data = st.text_area(
        "✍️ 地方競馬コピペデータ（データ分析傾向も含む）", 
        placeholder="ここに馬柱データやnetkeibaの分析テキストを貼り付けてください",
        height=450
    )
    
    if st.button("🚀 統合解析実行", use_container_width=True):
        if not api_key: 
            st.error("APIキーを入力してください（サイドバー下部、または設定欄）")
        elif not manual_data:
            st.error("解析するレースデータを入力してください")
        else:
            try:
                with st.spinner("地方ダート・走破タイム理論 統合解析中..."):
                    genai.configure(api_key=api_key)
                    model = genai.GenerativeModel('gemini-2.5-flash')
                    
                    # 地方競馬専用・スクショのテーブルヘッダーを強制出力させるプロンプト
                    prompt = f"""
                    【今回の馬柱・オッズデータ（netkeiba分析情報含む）】
                    {manual_data}
                    
                    【統合解析基準】
                    - JRAおよび地方競馬の高速馬場・トラックバイアス、芝・ダートのキレ、走破タイム理論（基準タイム・馬場補正）、上がり3F、展開・ハナ争いを統合解析せよ。
                    
                    【⚙️ 総監督絶対厳守ロジック：netkeibaデータ傾向スクリーニング】
                    1. 投入されたデータ内に「データ上位馬3頭」というセクションがある場合、そこに名前がある馬はクラス・条件への地力高いと判断し、軸馬・相手筆頭（◎, 〇, ▲）の最有力候補として評価パラメータを大きく加算せよ。
                    2. データ内の「今回の馬場状態が得意な馬」「今回のレース間隔で実績がある馬」「この競馬場が得意な馬」のいずれかの項目に該当する不人気馬（目安：単勝5番人気以下）を発見した場合は、近走着順がどれだけ悪くても「消し」評価にすることを厳禁とし、必ず【穴候補・紐（△または注）】として救済・格納せよ。

                    【⚙️ 総監督絶対厳守ロジック：死んだふり下剋上馬（上がり最速爆弾）の検知】
                    近走成績が崩れていても、以下の「激走ファクター」を満たす伏兵馬は、展開（ミドル〜ハイペース）がハマった瞬間に上がり最速で下剋上を起こす爆弾馬として自動検知せよ。
                    - 条件A：過去2〜3走以内に、敗れてはいるが「上がり3Fタイムがメンバー中1位または2位」の隠れた強烈な末脚・スタミナ実績がある馬。
                    - 条件B：前走が短い距離（マイル以下）で大敗しており、今回スタミナが問われる長距離（1800m〜2000m以上）へと大幅に距離延長してきた馬（追走ペースが楽になり、道中死んだふりから3〜4コーナーでの捲り差しが炸裂するパターン）。
                    - 上記に該当する馬は、展開利による激走警戒馬（注）として評価し、3連複フォーメーション等の3列目（紐）に必ず強制配置せよ。

                    【地方ダート・出力テーブル厳守指示】
                    全頭診断は、必ず以下の列構成（血統情報を含む）のMarkdownテーブルのみで出力せよ。

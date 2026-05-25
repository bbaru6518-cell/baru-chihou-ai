import streamlit as st
import google.generativeai as genai
import json
import os
import requests
from bs4 import BeautifulSoup
import datetime
import re

# --- 設定保存機能 ---
CONFIG_FILE = "baru_triple_config.json"
LOG_DIR = "racing_logs_triple"  # ⭕ トリプル馬単専用の独立フォルダ
os.makedirs(LOG_DIR, exist_ok=True)

def save_cfg(k, b):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump({"k": k, "b": b}, f, ensure_ascii=False, indent=4)

def load_cfg():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {
        "k": "", 
        # ⭕ 【初期値修正】起動した瞬間にトリプル馬単（馬単1,2着）のロジックが強制適用されるよう初期バイアスを固定
        "b": "トリプル馬単対象地方レース（主に後半3R）のトラックバイアス、砂質、1角ポジション争い、絶対に崩れない軸馬の選定、および逆転候補の展開利・ハナ争いを統合解析せよ。"
    }

def clean_filename(name):
    if not name:
        return ""
    clean = re.sub(r'[\\/*?:"<>| \t]', '_', name.strip())
    return clean[:50]

cfg = load_cfg()

# 👑 【看板完全死守】総監督指定のオリジナル大看板タイトル・バージョン表記へ完全固定
st.set_page_config(page_title="Baru 地方競馬AI Pro v24.8.5", layout="wide", initial_sidebar_state="expanded")
st.title("🏇 Baru 地方競馬AI Pro - 【Ver 24.8.5 高速・軽量化安定版】")

with st.sidebar:
    # ⭕ トリプル馬単版であることが内部的にわかるよう、管理用の識別文字を小さく追加
    st.header("⚙️ 総監督ルーム（司令部）[Triple]")
    api_key = st.text_input("Gemini API KEY", value=cfg.get("k", ""), type="password")
    bias = st.text_area("🧠 総監督バイアス（トリプル馬単補正値）", value=cfg.get("b"), height=150)
    budget = st.number_input("1レース予算(円)", value=1500, step=100)
    if st.button("💾 設定保存"):
        save_cfg(api_key, bias)
        st.success("トリプル馬単専用設定を保存しました。")

    # 📂 過去ログ呼び出し ＆ 復習ルーム
    st.markdown("---")
    st.header("📂 過去ログ復習 [Triple]")
    log_files = sorted([f for f in os.listdir(LOG_DIR) if f.endswith(".txt")], reverse=True)
    
    if log_files:
        selected_log = st.selectbox("復習・確認する対象レース", log_files)
        
        if st.button("📖 予想指示書を呼び出す"):
            with open(os.path.join(LOG_DIR, selected_log), "r", encoding="utf-8") as f:
                st.session_state["res"] = f.read()
            st.success(f"{selected_log} を読み込みました！")
            
        st.markdown("---")
        st.subheader("🏁 対象・レース結果コピペ")
        st.caption("💡 1行目にレース名を入力し、2行目から結果（着順・払戻金・通過順）を丸ごとコピペしてください。")
        result_copypaste = st.text_area("1行目：レース名 / 2行目〜：結果コピペ", height=200)
        
        if st.button("🚨 馬単の着順・ハナ争いと照合して復習"):
            if not api_key or not result_copypaste.strip():
                st.error("APIキーと結果データが必要です")
            else:
                try:
                    genai.configure(api_key=api_key)
                    available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                    m_name = next((m for m in available_models if "pro" in m.lower()), available_models[0] if available_models else "models/gemini-1.5-flash")
                    model = genai.GenerativeModel(m_name)
                    
                    lines = result_copypaste.splitlines()
                    raw_title = lines[0].strip() if lines else "対象レース結果"
                    cleaned_title = clean_filename(raw_title)
                    
                    with open(os.path.join(LOG_DIR, selected_log), "r", encoding="utf-8") as f:
                        past_prediction = f.read()
                        
                    p_1 = "あなたは総監督Baruの右腕競馬AIだ。提示されたトリプル馬単対象レースの予想指示書と、実際のレース結果コピペを徹底的に突き合わせ、短く簡潔に箇条書きで猛省レポートを作成せよ。\n\n"
                    p_2 = f"【タイトル】最上部に見出し「### 🏁 {raw_title} 戦果照合」を出力せよ。\n\n"
                    p_3 = "【馬単解析掟】\n1. 1着・2着の入線パターンとコーナー通過順から、想定外の逃げ残りや差し遅れのズレを炙り出せ。\n2. 馬単高配当を演出した人気薄の激走理由（地方砂質・トラックバイアス）の読みのズレを猛省せよ。\n3. 次回トリプル馬単を仕留めるため、バイアス設定をどう微調整すべきか簡潔に導け。\n\n"
                    p_4 = f"【出力フォーマット】\n### 🏁 {raw_title} 戦果照合\n馬単払戻金および戦果の整理\n\n### 🧠 1着2着・ハナ争いのズレ解剖\n馬単の着順に直結した地方小回り展開・バイアスのズレ分析\n\n### 🛠️ 次回制覇へのAIロジック微調整案\n地方ダート補正や馬場バイアスの具体的アドバイス\n\n"
                    p_5 = f"---\n【当時の予想指示書】:\n{past_prediction}\n\n【実際のレース結果コピペ】:\n{result_copypaste}"
                    
                    review_prompt = p_1 + p_2 + p_3 + p_4 + p_5

                    with st.spinner("1・2着展開のズレから猛省・復習中..."):
                        response = model.generate_content(review_prompt)
                        review_result = "\n\n" + "="*20 + f" 🏁 {raw_title} 復習ログ " + "="*20 + "\n" + response.text
                        
                        old_path = os.path.join(LOG_DIR, selected_log)
                        now_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                        new_filename = f"{cleaned_title}_{now_str}.txt"
                        new_path = os.path.join(LOG_DIR, new_filename)
                        
                        full_content = past_prediction + review_result
                        with open(new_path, "w", encoding="utf-8") as nf:
                            nf.write(full_content)
                        
                        if old_path != new_path and os.path.exists(old_path):
                            os.remove(old_path)
                            
                        st.session_state["res"] = full_content
                        st.success(f"💾 ファイル名を「{new_filename}」に変更し、復習ログを完全保存しました！")
                        st.rerun()
                except Exception as e:
                    st.error(f"復習解析エラー: {e}")
    else:
        st.info("まだ保存された予想ログはありません。")

if "res" not in st.session_state:
    st.session_state["res"] = ""

col1, col2 = st.columns([1, 1])
with col1:
    st.subheader("📋 対象レース 馬柱・オッズ混在テキスト入力")
    url_input = st.text_input("🔗 地方レースURL（netkeiba等）")
    manual_data = st.text_area("✍️ 対象レースコピペデータ", height=500)
    
    if st.button("🚀 構造解剖＆勝負指示書生成"):
        try:
            target_data = ""
            if url_input:
                with st.spinner("対象レースデータをスクレイピング中..."):
                    headers = {"User-Agent": "Mozilla/5.0"}
                    res = requests.get(url_input, headers=headers)
                    res.encoding = res.apparent_encoding
                    soup = BeautifulSoup(res.text, "html.parser")
                    main_data = soup.find_all("table")
                    for table in main_data:
                        target_data += table.get_text(separator="\n", strip=True) + "\n"
                    target_data = target_data[:15000]
            else:
                target_data = manual_data[:15000]

            if not api_key or not target_data:
                st.error("必要なデータが不足しています")
            else:
                genai.configure(api_key=api_key)
                available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                m_name = next((m for m in available_models if "pro" in m.lower()), available_models[0] if available_models else "models/gemini-1.5-flash")
                model = genai.GenerativeModel(m_name)
                
                # ⭕ 【トリプル馬単特化型プロンプト】看板は維持しつつ、馬単の1着2着を執念で当てるためのロジックを確実に注入
                base_instruction = """あなたはトリプル馬単を完全ハックするプロ競馬AIであり、総監督Baruの絶対的右腕だ。
入力されたデータから人気・枠番・馬番・馬名・オッズ・通過順を完全に解剖し、地方ダート戦で馬単の「1着・2着」を絶対に

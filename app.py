import streamlit as st
import google.generativeai as genai
import json
import os
import requests
from bs4 import BeautifulSoup
import datetime
import re

# --- 設定保存機能 ---
CONFIG_FILE = "baru_pro_config.json"
LOG_DIR = "racing_logs_standard"
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
        "b": "JRA（中央競馬）および地方競馬の高速馬場・トラックバイアス、芝・ダートのキレ、走破タイム理論（基準タイム・馬場補正）、上がり3F、展開・ハナ争いを統合解析せよ。"
    }

# ファイル名に使えない禁止文字を安全にクリーニングする関数
def clean_filename(name):
    if not name:
        return ""
    clean = re.sub(r'[\\/*?:"<>| \t]', '_', name.strip())
    return clean[:50]

cfg = load_cfg()
st.set_page_config(page_title="Baru AI Pro v24.8", layout="wide", initial_sidebar_state="expanded")
st.title("🏇 Baru 競馬AI Pro - 【Ver 24.8 ファイル名連動・自己学習型】")

with st.sidebar:
    st.header("⚙️ 総監督ルーム（通常レース指令部）")
    api_key = st.text_input("Gemini API KEY", value=cfg.get("k", ""), type="password")
    bias = st.text_area("🧠 総監督バイアス（馬場・補正値）", value=cfg.get("b"), height=150)
    budget = st.number_input("1レース予算(円)", value=1500, step=100)
    if st.button("💾 設定保存"):
        save_cfg(api_key, bias)
        st.success("通常レースの設定を保存しました。")

    # 📂 過去ログ呼び出し ＆ 復習ルーム
    st.markdown("---")
    st.header("📂 過去ログ・結果復習ルーム")
    log_files = sorted([f for f in os.listdir(LOG_DIR) if f.endswith(".txt")], reverse=True)
    
    if log_files:
        selected_log = st.selectbox("復習・確認する過去の予想", log_files)
        
        if st.button("📖 予想指示書を呼び出す"):
            with open(os.path.join(LOG_DIR, selected_log), "r", encoding="utf-8") as f:
                st.session_state["res"] = f.read()
            st.success(f"{selected_log} を読み込みました！")
            
        st.markdown("---")
        st.subheader("🏁 レース結果のコピペ投入")
        st.caption("💡 1行目にレース名やタイトル（例：大井11R 帝王賞）を入力し、2行目から結果を丸ごとコピペしてください！ファイル名がそのレース名に生まれ変わります。")
        result_copypaste = st.text_area("1行目：レース名 / 2行目〜：結果コピペ", height=200)
        
        if st.button("🚨 実際の着順・ハナ争いと照合して復習"):
            if not api_key or not result_copypaste.strip():
                st.error("APIキーと結果データが必要です")
            else:
                try:
                    genai.configure(api_key=api_key)
                    available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                    m_name = next((m for m in available_models if "pro" in m.lower()), available_models[0] if available_models else "models/gemini-1.5-flash")
                    model = genai.GenerativeModel(m_name)
                    
                    lines = result_copypaste.splitlines()
                    raw_title = lines[0].strip() if lines else "通常レース結果"
                    cleaned_title = clean_filename(raw_title)
                    
                    with open(os.path.join(LOG_DIR, selected_log), "r", encoding="utf-8") as f:
                        past_prediction = f.read()
                        
                    review_prompt = f"""あなたは総監督Baruの右腕AIだ。提示された【当時の予想指示書】と、実際の【レース結果コピペ】を徹底的に突き合わせ、超精密な反省・復習レポートを作成せよ。

【超重要：タイトル認識の掟】
最上部には、必ず総監督が指定したタイトル「{raw_title}」を引用して「### 🏁 {raw_title} 答え合わせ・戦果照合」という見出しからスタートせよ。

【解析の絶対掟】
1. 通過順データから「想定外の逃げ・先行馬の動き」や「予測したハナ争いのズレ」を完全に炙り出せ。
2. タイム補正やトラックバイアスが結果にどう影響したか、AI側の読みのズレを猛省せよ。
3. 次回全く同じコース・条件下で勝負する際、バイアスやスピード指数をどう微調整すべきか、具体的な改善策を導き出せ。

【出力フォーマット】
### 🏁 {raw_title} 答え合わせ・戦果照合
（的中か不中断か、実際の配当結果の整理）

### 🧠 展開・ハナ争いのズレ解剖（猛省）
（コーナー通過順や実際の逃げ馬の動きから、展開予測がどう狂ったかを分析）

### 🛠️ 次回に向けたAIロジック微調整案
（次回に向けてスピード補正や馬場バイアスの設定をどう変更すべきかの具体的アドバイス）

---
【当時の予想指示書】:
{past_prediction}

【実際のレース結果コピペ】:
{result_copypaste}"""

                    with st.spinner("実際の着順・コーナー通過順から猛省・復習中..."):
                        response = model.generate_content(review_prompt)
                        review_result = "\n\n" + "="*20 + f" 🏁 {raw_title} 復習ログ " + "="*20 + "\n" + response.text
                        
                        # 古い日付だけのファイルから、レース名入りの新ファイル名へリネーム＆追記
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
    st.subheader("📋 9走馬柱・オッズ混在テキスト入力")
    url_input = st.text_input("🔗 レースURL")
    manual_data = st.text_area("✍️ netkeibaコピペデータ", height=500)
    
    if st.button("🚀 構造解剖・多角データ解析開始"):
        try:
            target_data = ""
            if url_input:
                with st.spinner("レースデータをスクレイピング中..."):
                    headers = {"User-Agent": "Mozilla/5.0"}
                    # ⭕ 【修正箇所】カッコ閉じと変数名を100%修正しました
                    res = requests.get(url_input, headers=headers)
                    res.encoding = res.apparent_encoding
                    soup = BeautifulSoup(res.text, "html.parser")
                    main_data = soup.find_all("table")
                    for table in main_data:
                        target_data += table.get_text(separator="\n", strip=True) + "\n"
                    target_data = target_data[:50000]
            else:
                target_data = manual_data

            if not api_key or not target_data:
                st.error("必要なデータが不足しています")
            else:
                genai.configure(api_key=api_key)
                available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                m_name = next((m for m in available_models if "pro" in m.lower()), available_models[0] if available_models else "models/gemini-1.5-flash")
                model = genai.GenerativeModel(m_name)

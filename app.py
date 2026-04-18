import streamlit as st
import google.generativeai as genai
import json
import os
import requests
from bs4 import BeautifulSoup

# --- 設定保存機能 ---
CONFIG_FILE = "baru_pro_config.json"
def save_cfg(k, b):
    with open(CONFIG_FILE, "w") as f: json.dump({"k": k, "b": b}, f)
def load_cfg():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f: return json.load(f)
        except: pass
    return {"k": "", "b": "芝の決め手、血統適性、上がり3F、トラックバイアスを統合解析せよ。"}

cfg = load_cfg()
st.set_page_config(page_title="Baru AI Pro", layout="wide")
st.title("🏇 Baru 競馬AI Pro - 【勝率予測・鉄壁インデント版】")

# --- スクレイピング関数 ---
def get_netkeiba_data(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(url, headers=headers)
        res.encoding = res.apparent_encoding
        soup = BeautifulSoup(res.text, "html.parser")
        main_data = soup.find("table", class_=["RaceTable01", "db_table"]) or soup
        return main_data.get_text(separator="\n", strip=True)[:20000]
    except Exception as e:
        return f"Error: {e}"

# --- サイドバー設定 ---
with st.sidebar:
    st.header("⚙️ 総監督ルーム")
    api_key = st.text_input("Gemini API KEY", value=cfg.get("k", ""), type="password")
    bias = st.text_area("🧠 総監督バイアス", value=cfg.get("b"), height=200)
    budget = st.number_input("予算(円)", value=1000, step=100)
    if st.button("💾 設定保存"):
        save_cfg(api_key, bias)
        st.success("設定を保存しました。")

# --- メイン解析 ---
if "res" not in st.session_state:
    st.session_state["res"] = ""

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📋 データ入力")
    url_input = st.text_input("🔗 URL")
    manual_data = st.text_area("✍️ 貼り付け", height=400)
    
    if st.button("🚀 解析開始"):
        target = ""
        if url_input:
            with st.spinner("データを抽出中..."):
                target = get_netkeiba_data(url_input)
        else:
            target = manual_data

        if not api_key or not target:
            st.error("APIキーとデータが必要です")
        else:
            try:
                genai.configure(api_key=api_key)
                # 利用可能なモデルから最適なものを自動選択
                ms = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                m_name = next((x for x in ms if "pro" in x), next((x for x in ms if "flash" in x), ms[0]))
                
                model = genai.GenerativeModel(m_name)
                prompt = f"""
                競馬総監督Baruの右腕として18頭フルゲートまで精密に解析せよ。
                【必須ルール】全頭短評に[単勝勝率%/複勝圏内率%]を記載せよ。
                【構成】1.適性 2.展開 3.下剋上 4.全頭勝率予測 5.結論 6.🚀1軸4頭流し(予算{budget}円)
                データ: {target}
                バイアス: {bias}
                """
                with st.spinner(f"エンジン {m_name} で解析中..."):
                    response = model.generate_content(prompt)
                    st.session_state["res"] = response.text
            except Exception as e:
                st.error(f"解析エラー: {e}")

with col2:
    st.subheader("📊 投資指示書")
    if st.session_state["res"]:
        st.markdown(st.session_state["res"])
    else:
        st.info("解析を開始するとここに結果が表示されます。")

st.caption("Baru Stable AI Pro v12.6")

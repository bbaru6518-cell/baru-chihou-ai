import streamlit as st
import google.generativeai as genai
import json
import os
import requests
from bs4 import BeautifulSoup
import re

# --- 設定保存 ---
CONFIG_FILE = "baru_chihou_config.json"
def save_cfg(k, b):
    with open(CONFIG_FILE, "w") as f: json.dump({"k": k, "b": b}, f)
def load_cfg():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f: return json.load(f)
        except: pass
    return {"k": "", "b": ""}

cfg = load_cfg()
st.set_page_config(page_title="Baru 競馬AI Pro", layout="wide")
st.title("🏇 Baru 競馬AI Pro - 【URL自動解析＆期待値計算】")

# --- スクレイピング関数 ---
def get_netkeiba_data(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(url, headers=headers)
        res.encoding = res.apparent_encoding
        soup = BeautifulSoup(res.text, "html.parser")
        # 出馬表や結果のテキストを抽出（簡易版）
        text = soup.get_text(separator="\n", strip=True)
        # 不要なヘッダー・フッターを削る（キーワードでトリミング）
        start = text.find("枠番") if "枠番" in text else 0
        return text[start:start+5000] # 5000文字程度に制限
    except Exception as e:
        return f"データ取得エラー: {e}"

with st.sidebar:
    st.header("⚙️ 設定")
    api_key = st.text_input("Gemini API KEY", value=cfg.get("k", ""), type="password")
    bias = st.text_area("🧠 総監督バイアス", value=cfg.get("b", "地方の深い砂に適応できるパワー馬、先行馬を最優先せよ。"), height=150)
    if st.button("💾 保存"):
        save_cfg(api_key, bias)
        st.success("設定を保存しました。")
    
    st.divider()
    st.subheader("💰 期待値シミュレーター")
    budget = st.number_input("1レースの予算(円)", value=1000, step=100)

col1, col2 = st.columns([1, 1])

with col1:
    url_input = st.text_input("🔗 netkeiba等のURLを貼り付け")
    manual_data = st.text_area("📋 またはデータを直接貼り付け", height=400)
    
    if st.button("🚀 解析＆シミュレーション開始"):
        target_data = ""
        if url_input:
            with st.spinner("URLからデータを抽出中..."):
                target_data = get_netkeiba_data(url_input)
        else:
            target_data = manual_data

        if not api_key or not target_data:
            st.error("APIキーとデータを入力してください")
        else:
            try:
                genai.configure(api_key=api_key)
                available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                target_model = next((m for m in available_models if "1.5-flash" in m or "2.5-flash" in m), available_models[0])
                
                model = genai.GenerativeModel(target_model)
                prompt = f"""
                あなたは競馬AI総監督Baruの右腕だ。以下のデータから結論を出せ。
                
                【必須項目】
                1. 砂の王 (POWER-AXIS)
                2. 先行優位ジャッジ
                3. 下剋上・勝負気配
                4. 全頭短評 (買い/消し)
                5. Baruの最終結論 (◎○▲△×)
                6. 期待値シミュレーション: 予算{budget}円での最適な資金配分(円単位)
                
                データ: {target_data}
                バイアス: {bias}
                """
                
                with st.spinner("最強エンジンで解析中..."):
                    response = model.generate_content(prompt)
                    st.session_state["result"] = response.text
                    st.success(f"解析完了 ({target_model})")
            except Exception as e:
                st.error(f"エラー: {e}")

with col2:
    st.subheader("📊 解析結果・投資指示書")
    if "result" in st.session_state:
        st.markdown(st.session_state["result"])
    else:
        st.info("左側のボタンを押すとここに結果が表示されます。")

st.caption("Baru Stable AI System v9.0 - Automation & Simulation")

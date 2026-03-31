import streamlit as st
import google.generativeai as genai
import json
import os

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
st.set_page_config(page_title="Baru 競馬AI", layout="wide")
st.title("🏇 Baru 競馬AI - 【最新規格対応・解決版】")

with st.sidebar:
    st.header("⚙️ 設定")
    api_key = st.text_input("Gemini API KEY", value=cfg.get("k", ""), type="password")
    bias = st.text_area("🧠 総監督バイアス", value=cfg.get("b", "地方の深い砂に対応できるパワー馬、先行馬を最優先。"), height=150)
    if st.button("💾 保存"):
        save_cfg(api_key, bias)
        st.success("最新キーを保存しました。")

col1, col2 = st.columns([2, 1])
with col1:
    data = st.text_area("📋 レースデータ", height=500, key="data_input", placeholder="データを貼り付け...")
with col2:
    if st.button("🚀 解析スタート"):
        if not api_key or not data:
            st.error("APIキーとデータを入力してください")
        else:
            try:
                # API設定
                genai.configure(api_key=api_key)
                
                # --- 【解決策】利用可能なモデルを直接リストアップして、動くものを自動選択 ---
                with st.spinner("接続経路を自動判別中..."):
                    try:
                        # 404を回避するため、まず利用可能なモデル名をGoogleに問い合わせる
                        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                        
                        # 優先順位：1.5-flash -> 1.5-pro -> その他
                        target_model = None
                        for m in available_models:
                            if "1.5-flash" in m:
                                target_model = m
                                break
                        if not target_model and available_models:
                            target_model = available_models[0]
                            
                        if target_model:
                            model = genai.GenerativeModel(target_model)
                            prompt = f"バイアス: {bias}\n\nデータ: {data}"
                            response = model.generate_content(prompt)
                            
                            st.success(f"✅ 通信成功！ (使用モデル: {target_model})")
                            st.markdown("---")
                            st.markdown(response.text)
                        else:
                            st.error("利用可能なモデルが見つかりません。APIキーの権限を確認してください。")
                            
                    except Exception as inner_e:
                        st.error(f"接続に失敗しました。APIキーが間違っているか、有効化されていません。\n詳細: {inner_e}")

            except Exception as e:
                st.error(f"システムエラー: {e}")

st.caption("Baru Stable AI System v8.0 - Auto-Selection Edition")

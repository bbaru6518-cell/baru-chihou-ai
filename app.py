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
st.set_page_config(page_title="Baru 地方競馬AI", layout="wide")
st.title("🏇 Baru 地方競馬AI - 【地方砂質・先行特化版】")

def reset_data():
    st.session_state["data_input"] = ""

with st.sidebar:
    st.header("⚙️ 地方専用設定")
    api_key = st.text_input("Gemini API KEY", value=cfg.get("k", ""), type="password")
    bias = st.text_area("🧠 地方総監督バイアス", value=cfg.get("b", "地方の深い砂に対応できるパワー馬、および小回り内枠の先行馬を最優先せよ。"), height=150)
    if st.button("💾 保存"):
        save_cfg(api_key, bias)
        st.success("地方競馬ロジック、起動完了。")

col1, col2 = st.columns([2, 1])
with col1:
    data = st.text_area("📋 地方レースデータ", height=550, key="data_input", placeholder="地方競馬のデータを貼り付け...")
with col2:
    if st.button("🚀 地方砂質・先行ジャッジ"):
        if not api_key or not data:
            st.error("入力不足です")
        else:
            try:
                genai.configure(api_key=api_key)
                
                # --- 修正ポイント：利用可能なモデルを順番に試す ---
                success = False
                # 試行するモデルのリスト（最新から順に）
                model_names = ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-pro"]
                
                prompt = f"""競馬AI総監督Baruの右腕として結論を出せ。
                【データ】: {data}
                【バイアス】: {bias}
                1.砂の王(POWER-AXIS) 2.先行優位 3.移籍/勝負気配 4.全頭診断 5.買い目
                """

                for m_name in model_names:
                    try:
                        model = genai.GenerativeModel(m_name)
                        with st.spinner(f"モデル {m_name} で解析中..."):
                            response = model.generate_content(prompt)
                            st.success(f"✅ 解析完了 (使用モデル: {m_name})")
                            st.markdown("---")
                            st.markdown(response.text)
                            success = True
                            break # 成功したらループを抜ける
                    except Exception as inner_e:
                        continue # 失敗したら次のモデルを試す

                if not success:
                    st.error("利用可能なGeminiモデルが見つかりませんでした。APIキーが有効か、またはGoogle AI Studioでモデルの権限を確認してください。")

            except Exception as e:
                st.error(f"致命的なエラー: {e}")

    st.button("🧹 データをクリア", on_click=reset_data)

st.caption("Baru Stable AI System v5.0 - 地方競馬・砂質攻略ロジック")

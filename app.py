import streamlit as st
import google.generativeai as genai
import json
import os

# --- 設定保存（地方専用ファイル名） ---
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
    data = st.text_area("📋 地方レースデータ", height=550, key="data_input", placeholder="地方競馬（大井・高知など）のデータを貼り付け...")
with col2:
    if st.button("🚀 地方砂質・先行ジャッジ"):
        if not api_key or not data:
            st.error("入力不足です（APIキーとデータを入力してください）")
        else:
            try:
                # --- API設定 ---
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel("gemini-1.5-flash")
                
                prompt = f"""
                あなたは競馬AI総監督Baruの右腕だ。
                地方競馬特有の【砂質・小回り・先行バイアス】に基づき、結論を出せ。
                
                【対象データ】: {data}
                【総監督バイアス】: {bias}
                
                以下の5項目で出力せよ：
                1.★地方・砂の王(POWER-AXIS): 地方特有のタフな砂を苦にしない大型馬、または小回りを逃げ切れる快速馬を指名。
                2.小回り内枠・先行の絶対優位: 最初のコーナーを3番手以内で回れる馬を評価。
                3.移籍・勝負気配の察知: 中央からの移籍初戦やリーディング騎手への乗り替え。
                4.全頭診断: 1行ずつ。馬番、馬名、砂の適性と位置取り予測。
                5.買い目: 逃げ・先行馬を軸にした「馬複・ワイド・3連複」。爆穴を1頭含めること。
                """
                
                with st.spinner("地方の深い砂と展開を読み解き中..."):
                    res = model.generate_content(prompt)
                    st.success("✅ 地方解析完了。")
                    st.markdown("---")
                    st.markdown(res.text)
            except Exception as e:
                st.error(f"解析エラーが発生しました。詳細: {e}")

    st.button("🧹 データをクリア", on_click=reset_data)

st.caption("Baru Stable AI System v5.0 - 地方競馬・砂質攻略ロジック")

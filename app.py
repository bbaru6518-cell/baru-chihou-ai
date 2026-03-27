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
                # --- API設定の最安定化 ---
                genai.configure(api_key=api_key)
                
                # 404エラーを回避するための標準指定
                model = genai.GenerativeModel('gemini-1.5-flash')
                
                prompt = f"""
                あなたは競馬AI総監督Baruの右腕だ。
                地方競馬特有の【砂質・小回り・先行バイアス】に基づき、結論を出せ。
                
                【対象データ】: {data}
                【総監督バイアス】: {bias}
                
                以下の5項目で出力せよ：
                1.★地方・砂の王(POWER-AXIS): 地方特有の砂に強い大型馬、または逃げ馬を指名。
                2.小回り内枠・先行の絶対優位: 前に行ける馬を評価。
                3.移籍・勝負気配の察知: 移籍初戦やリーディング騎手への乗り替え。
                4.全頭診断: 1行ずつ。馬番、馬名、砂適性と位置予測。
                5.買い目: 逃げ・先行馬軸。爆穴を1頭含める。
                """
                
                with st.spinner("砂の適性を解析中..."):
                    # 呼び出し方式を最もシンプルな形に
                    response = model.generate_content(prompt)
                    st.success("✅ 地方解析完了。")
                    st.markdown("---")
                    st.markdown(response.text)
            except Exception as e:
                # エラーが出た場合、旧名称の 'gemini-pro' で最後の悪あがき（リトライ）
                try:
                    model_alt = genai.GenerativeModel('gemini-pro')
                    response = model_alt.generate_content(prompt)
                    st.success("✅ 解析成功（代替モデル使用）")
                    st.markdown(response.text)
                except:
                    st.error(f"解析エラー: {e}")

    st.button("🧹 データをクリア", on_click=reset_data)

st.caption("Baru Stable AI System v5.0 - 地方競馬・砂質攻略ロジック")

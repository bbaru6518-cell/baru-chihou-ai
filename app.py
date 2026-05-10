import streamlit as st
import google.generativeai as genai
import json
import os
import requests
from bs4 import BeautifulSoup

# --- 設定保存機能 ---
CONFIG_FILE = "baru_pro_config.json"
def save_cfg(k, b):
    with open(CONFIG_FILE, "w") as f:
        json.dump({"k": k, "b": b}, f)

def load_cfg():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        except:
            pass
    return {"k": "", "b": "芝の決め手、血統適性、上がり3F、トラックバイアスを統合解析せよ。"}

cfg = load_cfg()
st.set_page_config(page_title="Baru AI Pro", layout="wide")
st.title("🏇 Baru 競馬AI Pro - 【軸馬精密・下剋上昇格版】")

def get_netkeiba_data(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(url, headers=headers)
        res.encoding = res.apparent_encoding
        soup = BeautifulSoup(res.text, "html.parser")
        main_data = soup.find_all("table")
        combined_text = ""
        for table in main_data:
            combined_text += table.get_text(separator="\n", strip=True) + "\n"
        return combined_text[:30000] # データ量をさらに確保
    except Exception as e:
        return f"Error: {e}"

with st.sidebar:
    st.header("⚙️ 総監督ルーム")
    api_key = st.text_input("Gemini API KEY", value=cfg.get("k", ""), type="password")
    bias = st.text_area("🧠 総監督バイアス", value=cfg.get("b"), height=200)
    budget = st.number_input("予算(円)", value=1000, step=100)
    if st.button("💾 設定保存"):
        save_cfg(api_key, bias)
        st.success("設定を保存しました。")

if "res" not in st.session_state:
    st.session_state["res"] = ""

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📋 データ・調教入力")
    url_input = st.text_input("🔗 URLを入力（出馬表・調教・厩舎どれでも可）")
    manual_data = st.text_area("✍️ 貼り付け（調教タイムやコメント）", height=400)
    
    if st.button("🚀 軸馬・精密スキャン解析開始"):
        target_data = ""
        if url_input:
            with st.spinner("データを抽出中..."):
                target_data = get_netkeiba_data(url_input)
        else:
            target_data = manual_data

        if not api_key or not target_data:
            st.error("APIキーとデータが必要です")
        else:
            try:
                genai.configure(api_key=api_key)
                # モデル自動選択（性能の高い1.5 Proを最優先）
                models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                m_name = next((x for x in models if "1.5-pro" in x), 
                             next((x for x in models if "pro" in x), 
                             models[0]))
                
                model = genai.GenerativeModel(m_name)
                prompt = f"""
                あなたは競馬AI総監督Baruの右腕だ。軸馬（◎）の選定ミスを撲滅せよ。
                
                【今回の鉄壁指令】
                - 「紐は合っているが軸がズレる」という失態を繰り返すな。
                - 調教評価がB以上かつ、前走からの「上積み」が確信できる馬だけを◎に選べ。
                - 実績馬が「休み明け」「太め」「調教C」なら、迷わず◎から外し、紐で拾っている「デキのいい穴馬」を軸に昇格させよ。
                
                【解析・構成ルール】
                1. 砂の王/芝の覇者 (血統・適性)
                2. 調教・軸馬適合判定 (◎として信頼できる理由、または軸を替えた理由)
                3. 下剋上・勝負気配 (紐に隠れた真の軸候補)
                4. 全頭解析＆勝率予測 [単%/複%] 
                5. 最終結論 (◎○▲△×) ※軸の信頼度を「A:不動/B:信頼/C:混戦」で付記
                6. 🚀 1軸流し馬券(予算{budget}円)
                   - 軸の信頼度がCなら、ワイド・馬連の「2頭軸マルチ」的な買い目も検討せよ。
                
                データ: {target_data}
                バイアス: {bias}
                """
                with st.spinner(f"高性能エンジン {m_name} で軸馬を再構築中..."):
                    response = model.generate_content(prompt)
                    st.session_state["res"] = response.text
            except Exception as e:
                st.error(f"解析エラー: {e}")

with col2:
    st.subheader("📊 投資指示書")
    if st.session_state["res"]:
        st.markdown(st.session_state["res"])

st.caption("Baru Stable AI Pro v13.0 - Axis & Training Precision Edition")

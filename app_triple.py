import streamlit as st
import google.generativeai as genai
import json
import os
import requests
from bs4 import BeautifulSoup

# --- 設定保存機能 ---
CONFIG_FILE = "baru_pro_config.json"
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
        "b": "地方競馬のトリプル馬単対象3レースを完全解析せよ。トラックバイアス（イン有利・外伸び）、砂の深さ、タイム理論（基準タイム・馬場補正）、展開・ハナ争い、そして『絶対に1着を外さない鉄板馬』と『2着に突っ込んでくる爆穴馬』を徹底的に炙り出せ。"
    }

# --- データ取得ヘルパー関数 ---
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
        return combined_text[:60000]
    except Exception as e:
        return f"Error: {e}"

cfg = load_cfg()
st.set_page_config(page_title="Baru AI Triple Master v26", layout="wide")
st.title("🏇 Baru 競馬AI Pro - 【Ver 26.0 トリプル馬単・3連勝サバイバル】")

with st.sidebar:
    st.header("⚙️ 総監督ルーム（トリプル馬単戦略本部）")
    api_key = st.text_input("Gemini API KEY", value=cfg.get("k", ""), type="password")
    bias = st.text_area("🧠 総監督バイアス（地方砂質・トラックバイアス）", value=cfg.get("b"), height=150)
    budget = st.number_input("トリプル馬単総予算(円)", value=5000, step=500)
    if st.button("💾 設定保存"):
        save_cfg(api_key, bias)
        st.success("トリプル馬単の設定を保存しました。")

if "res" not in st.session_state:
    st.session_state["res"] = ""

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📋 トリプル馬単対象 3レース分のデータ一括投入")
    url_input = st.text_input("🔗 対象レースURL（または代表URL）")
    manual_data = st.text_area("✍️ 地方最終3レース分の出馬表・過去9走コピペデータ（連続貼り付けOK）", height=500)
    
    if st.button("🚀 トリプル馬単・電撃フォーメーション生成"):
        target_data = ""
        if url_input:
            with st.spinner("地方トリプル対象データを解析中..."):
                target_data = get_netkeiba_data(url_input)
        else:
            target_data = manual_data

        if not api_key or not target_data:
            st.error("APIキーと解析対象のデータが必要です")
        else:
            try:
                genai.configure(api_key=api_key)
                
                # 有効モデル全自動検知
                available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                m_name = next((m for m in available_models if "pro" in m.lower()), available_models[0] if available_models else "models/gemini-1.5-flash")
                
                model = genai.GenerativeModel(m_name)
                
                # --- トリプル馬単・軍資金コントロールプロンプト ---
                base_instruction = """あなたは地方競馬のトリプル馬単（三重勝馬単二連勝単式）を完全攻略するために最適化された最強のAIであり、総監督Baruの絶対的右腕だ。
入力された最終3レースのデータを完全に解剖し、総監督の指定予算（50円単位での購入を考慮）に収まる馬単フォーメーション指示書を作成せよ。

【トリプル馬単における絶対掟】
1. 馬単は1着と2着の着順が完全一致する必要がある。そのため「1着固定（アタマ信頼）」「1・2着裏表（マルチ）」「ボックス」のどれが最適かを各レースの力関係から見極めよ。
2. 地方特有のトラックバイアス（内拉致沿いが軽い、外に出さないと伸びない等）や「ハナ争い🔥」の激しさを分析し、地方競馬の砂で粘り切れる逃げ・先行馬、および展開が向く差し馬を特定せよ。
3. 指定された「総予算（例: 5,000円＝50円単位なら100点分）」を絶対に超えないよう、3レースの合計買い目点数（1レース目の馬単点数 × 2レース目の馬単点数 × 3レース目の馬単点数）を緻密に調整せよ。

【出力フォーマット】
以下の3つのセクション構成のみを出力せよ。余計な前置きや挨拶は一切禁止する。

### 📊 トリプル馬単・3ステージ難易度マップ
対象3レースの構造を以下のテーブル形式で瞬時に可視化せよ。
| レース | 条件/距離 | 1着軸信頼度 (鉄板/危険/混戦) | 逃げ🔥・先行📢候補 | 2着候補（紐荒れ注意馬） | 決断 (固定/マルチ/BOX) |

### 📈 各ステージの馬単深層解剖＆ハナ看破
1. 【第1ステージ（対象1レース目）】: 展開・ハナ争い予想。1着に据えるべき馬と、2着に粘り込むヒモ穴馬の馬単構築ロジック。
2. 【第2ステージ（対象2レース目）】: 展開・ハナ争い予想。基準タイム・馬場補正から浮上する、馬単の裏表（マルチ）が必要な激戦の理由。
3. 【第3ステージ（最終レース）】: 展開・ハナ争い予想。地方の深い砂を苦にしない血統・コース適性馬と、一発逆転の爆穴馬。

### 💰 トリプル馬単：最終投資指示書
予算内に完全最適化された組み合わせを出力せよ。最後に「合計点数」と「50円購入時の合計金額」を明記すること。

フォーマット例：
- **第1ステージ**：1着：〇 / 2着：〇, 〇, 〇 （計〇点）
- **第2ステージ**：1着：〇, 〇 / 2着：〇, 〇 （計〇点）
- **第3ステージ**：ボックス 〇, 〇, 〇 （計〇点）
**🔥 計算：〇点 × 〇点 × 〇点 ＝ 〇点 (50円購入時 合計〇,〇〇円)**"""
                
                prompt = base_instruction + f"\n対象データ: {target_data}\n総監督バイアス: {bias}\n予算: {budget}円"

                with st.spinner(f"🚀 トリプル馬単・3タテサバイバル解析中... ({m_name})"):
                    response = model.generate_content(prompt)
                    st.session_state["res"] = response.text
            except Exception as e:
                st.error(f"解析エラー: {e}")

with col2:
    st.subheader("📊 トリプル馬単・最終投資指示書")
    if st.session_state["res"]:
        st.markdown(st.session_state["res"])

st.caption("Baru Stable AI Triple Master v26.0 - 3-Stage Exacta Matrix Edition")

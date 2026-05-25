import streamlit as st
import google.generativeai as genai
import json
import os
import requests
from bs4 import BeautifulSoup
import datetime

# --- 設定保存機能 ---
CONFIG_FILE = "baru_pro_config.json"
LOG_DIR = "racing_logs_standard"

# 🚀 【修正】フォルダがすでにあっても絶対にエラーにしない安全設計
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
        return combined_text[:50000]
    except Exception as e:
        return f"Error: {e}"

cfg = load_cfg()
st.set_page_config(
    page_title="Baru AI Pro v24.8", 
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🏇 Baru 競馬AI Pro - 【Ver 24.8 通常レース・予測ログ完全保存版】")

with st.sidebar:
    st.header("⚙️ 総監督ルーム（通常レース指令部）")
    api_key = st.text_input("Gemini API KEY", value=cfg.get("k", ""), type="password")
    bias = st.text_area("🧠 総監督バイアス（馬場・補正値）", value=cfg.get("b"), height=150)
    budget = st.number_input("1レース予算(円)", value=1500, step=100)
    if st.button("💾 設定保存"):
        save_cfg(api_key, bias)
        st.success("通常レースの設定を保存しました。")

    # 📂 過去ログ振り返りルーム
    st.markdown("---")
    st.header("📂 過去ログ振り返りルーム")
    log_files = sorted([f for f in os.listdir(LOG_DIR) if f.endswith(".txt")], reverse=True)
    if log_files:
        selected_log = st.selectbox("確認する過去の予想", log_files)
        if st.button("📖 選択した予想を呼び出す"):
            with open(os.path.join(LOG_DIR, selected_log), "r", encoding="utf-8") as f:
                st.session_state["res"] = f.read()
            st.success(f"{selected_log} を読み込みました！")
    else:
        st.info("まだ保存された予想ログはありません。")

if "res" not in st.session_state:
    st.session_state["res"] = ""

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📋 9走馬柱・オッズ混在テキスト入力")
    url_input = st.text_input("🔗 レースURL（出馬表・オッズページ等）")
    manual_data = st.text_area("✍️ netkeibaコピペデータ（オッズ表やデータ分析テキストをそのまま一括投入）", height=500)
    
    if st.button("🚀 構造解剖・多角データ解析開始"):
        target_data = ""
        if url_input:
            with st.spinner("レースデータをバックグラウンドスクレイピング中..."):
                target_data = get_netkeiba_data(url_input)
        else:
            target_data = manual_data

        if not api_key or not target_data:
            st.error("APIキーと解析対象のデータが必要です")
        else:
            try:
                genai.configure(api_key=api_key)
                
                available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                m_name = next((m for m in available_models if "pro" in m.lower()), available_models[0] if available_models else "models/gemini-1.5-flash")
                
                model = genai.GenerativeModel(m_name)
                
                base_instruction = """あなたは中央競馬（JRA）および地方競馬を統括する競馬AIであり、総監督Baruの絶対的右腕だ。
入力されたテキストデータから人気・枠・馬番・馬名・オッズ・過去の通過順を完全に解剖し、逃げ・先行馬の有利不利を見抜いた勝負指示書を作成せよ。

【データ解剖における絶対掟】
1. 過去9走の通過順データ（例: 1-1-1 や 11-10-8 等）や、データ分析テキスト内の「有利な脚質：逃げ」などの文脈から、今回の出走馬の脚質を「逃げ」「先行」「差し」「追込」に超精密に分類せよ。
2. 特に、ハナを叩きそうな「逃げ」馬、好位をキープする「先行」馬にはマーク（印）をつけ、展開面での有利不利を可視化せよ。

【出力フォーマット】
以下の3つのセクション構成のみを出力せよ。余計な前置きや挨拶は一切禁止する。

### 📊 全頭精密診断・血統適性リスト
必ず以下の列を持つMarkdownテーブル形式で今回の出走馬を全頭出力せよ。
| 馬番 | 馬名 | 父 | 母 | 血統適性 | 脚質 | 人気 | 評価 | 理由 |
※【脚質】列には、「逃げ🔥」「先行📢」「差し」「追込」のように、逃げ・先行馬がひと目でわかるよう絵文字付きで印をつけよ！
※評価は（◎、○、▲、△、注、消）で厳選せよ。

### 📈 走破タイム・トラックバイアス深層データ分析
1. 【走破理論・スピード指数分析】: 距離・コース・今回の馬場状態（不・重など）から、走破タイムの基準値・補正値が最も優秀な上位3頭。
2. 【展開・ハナ争い完全看破】: 今回ハナを叩く可能性が最も高い「逃げ🔥」馬の特定と、その馬が作るペース予想（ハイ/ミドル/スロー）。それによって展開利を受ける「先行📢」馬や差し馬の力関係。
3. 【激走のシグナル（上積みチェック）】: 過去9走の馬体重の変動、レース間隔の実績、調教評価から、今回「完全叩き一変」の激走気配がある下剋上穴馬。
4. 【血統×コースマトリクス】: 開催競馬場・コースのリーディングサイアー実績に最も合致する特注配合馬。

### 💰 三連複フォーメーション：厳選15点指示書
投資効率を最大化する【合計15点】のフォーメーションを強制生成せよ。
 - 1頭目（軸馬）：◎（1頭）
 - 2頭目（対抗）：○や▲から「厳選した2頭」のみを指定
 - 3頭目（紐・穴）：◎、○、▲、△、注を含めた「合計7頭」を指定
※計算式：1頭×2頭×(7頭 - 2頭) ＝ 【15点】に完全固定。

フォーマット例：
**◎ 軸馬: 〇番 (馬名)**
1頭目：〇
2頭目：〇, 〇
3頭目：〇, 〇, 〇, 〇, 〇, 〇, 〇"""
                
                prompt = base_instruction + f"\n対象データ: {target_data}\n総監督バイアス: {bias}\n予算: {budget}円"

                with st.spinner(f"🚀 展開・脚質をマッピング中... (自動選択: {m_name})"):
                    response = model.generate_content(prompt)
                    output_text = response.text
                    st.session_state["res"] = output_text
                    
                    # 🚀 自動ログ保存
                    now_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                    log_path = os.path.join(LOG_DIR, f"3連複15点_{now_str}.txt")
                    with open(log_path, "w", encoding="utf-8") as log_f:
                        log_f.write(f"=== 予想生成日時: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n")
                        log_f.write(f"🔗 URL: {url_input}\n")
                        log_f.write(f"🧠 バイアス: {bias}\n")
                        log_f.write("="*40 + "\n\n")
                        log_f.write(output_text)
                    st.toast("💾 予想ログを自動保存しました！", icon="💾")
                    
            except Exception as e:
                st.error(f"解析エラー: {e}")

with col2:
    st.subheader("📊 投資指示書 (展開・データ分析枠完全版)")
    if st.session_state["res"]:
        st.markdown(st.session_state["res"])

st.caption("Baru Stable AI Pro v24.8 - Pace & Position Dynamics Edition with Auto-Logger")

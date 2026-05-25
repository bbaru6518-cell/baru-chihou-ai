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
LOG_DIR = "racing_logs_local"  # 地方専用のログフォルダに変更
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
        # ⭕ 【地方特化】デフォルトのバイアス指示を地方ダート・小回り展開用に変更
        "b": "地方競馬（南関東・門別・高知・園田等）の砂質・砂の深さ、トラックバイアス（イン有利・外伸び）、逃げ先行圧倒的有利な小回りコース特性、走破タイム理論（基準タイム・馬場補正）、イン差し・連対率を統合解析せよ。"
    }

def clean_filename(name):
    if not name:
        return ""
    clean = re.sub(r'[\\/*?:"<>| \t]', '_', name.strip())
    return clean[:50]

cfg = load_cfg()
# ⭕ 【地方特化】看板タイトルを地方専用仕様に変更
st.set_page_config(page_title="Baru AI Local Pro v24.8", layout="wide", initial_sidebar_state="expanded")
st.title("🏇 Baru 地方競馬AI Pro - 【Ver 24.8 地方特化・ファイル名連動型】")

with st.sidebar:
    st.header("⚙️ 総監督ルーム（地方レース指令部）")
    api_key = st.text_input("Gemini API KEY", value=cfg.get("k", ""), type="password")
    bias = st.text_area("🧠 総監督バイアス（地方砂質・補正値）", value=cfg.get("b"), height=150)
    budget = st.number_input("1レース予算(円)", value=1500, step=100)
    if st.button("💾 設定保存"):
        save_cfg(api_key, bias)
        st.success("地方競馬専用の設定を保存しました。")

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
        st.caption("💡 1行目にレース名（例：大井11R 帝王賞）を入力し、2行目から結果を丸ごとコピペしてください！ファイル名がそのレース名に生まれ変わります。")
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
                    raw_title = lines[0].strip() if lines else "地方レース結果"
                    cleaned_title = clean_filename(raw_title)
                    
                    with open(os.path.join(LOG_DIR, selected_log), "r", encoding="utf-8") as f:
                        past_prediction = f.read()
                        
                    # 安全な文字列結合方式（バグ根絶型）
                    p_1 = "あなたは総監督Baruの右腕AIだ。提示された地方競馬の予想指示書と、実際のレース結果コピペを徹底的に突き合わせ、超精密な反省レポートを作成せよ。\n\n"
                    p_2 = f"【重要：タイトル認識】最上部には必ず総監督が指定したタイトル「{raw_title}」を引用して「### 🏁 {raw_title} 答え合わせ・戦果照合」という見出しからスタートせよ。\n\n"
                    p_3 = "【地方解析掟】\n1. 地方特有のキツいコーナー通過順データから、ハナ争いのズレや内をロスなく立ち回った馬の動きを炙り出せ。\n2. 各地方競馬場特有の砂質（軽い・重い・内荒れ）やトラックバイアスがどう影響したか、AI側の読みのズレを猛省せよ。\n3. 次回同じ地方コースで勝負する際、バイアス設定をどう微調整すべきか具体的な改善策を導け。\n\n"
                    p_4 = f"【出力フォーマット】\n### 🏁 {raw_title} 答え合わせ・戦果照合\n的中や地方配当結果の整理\n\n### 🧠 地方砂質×ハナ争いのズレ解剖\nコーナー通過順からの展開分析・パドックや馬場状態のズレ\n\n### 🛠️ 次回に向けたAIロジック微調整案\n地方ダート補正や馬場バイアスの具体的アドバイス\n\n"
                    p_5 = f"---\n【当時の予想指示書】:\n{past_prediction}\n\n【実際のレース結果コピペ】:\n{result_copypaste}"
                    
                    review_prompt = p_1 + p_2 + p_3 + p_4 + p_5

                    with st.spinner("地方の砂質・小回り展開のズレから猛省・復習中..."):
                        response = model.generate_content(review_prompt)
                        review_result = "\n\n" + "="*20 + f" 🏁 {raw_title} 復習ログ " + "="*20 + "\n" + response.text
                        
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
                        st.success(f"💾 ファイル名を「{new_filename}」に変更し、地方復習ログを完全保存しました！")
                        st.rerun()
                except Exception as e:
                    st.error(f"復習解析エラー: {e}")
    else:
        st.info("まだ保存された地方予想ログはありません。")

if "res" not in st.session_state:
    st.session_state["res"] = ""

col1, col2 = st.columns([1, 1])
with col1:
    st.subheader("📋 地方競馬 過去馬柱・オッズ混在テキスト入力")
    url_input = st.text_input("🔗 地方レースURL（netkeiba等）")
    manual_data = st.text_area("✍️ 地方競馬コピペデータ", height=500)
    
    if st.button("🚀 地方構造解剖・ダートデータ解析開始"):
        try:
            target_data = ""
            if url_input:
                with st.spinner("地方レースデータをスクレイピング中..."):
                    headers = {"User-Agent": "Mozilla/5.0"}
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
                
                # ⭕ 【地方特化】プロンプトのロジックを地方競馬専用に完全チューニング
                base_instruction = """あなたは地方競馬（南関・門別・高知・園田など）を完全ハックするプロ競馬AIであり、総監督Baruの絶対的右腕だ。
入力されたテキストデータから人気・枠・馬番・馬名・オッズ・過去の地方通過順を完全に解剖し、先行有利な地方ダートでハナを叩く馬、インで死んだふりをする激走穴馬を見抜いた勝負指示書を作成せよ。

【データ解剖における地方絶対掟】
1. 地方は小回り特有の「最初の直線での位置取り」が命だ。過去の通過順データ（例: 1-1-1 や 2-2-3 等）から、今回のダート戦での脚質を「逃げ」「先行」「差し」「追込」に超精密に分類せよ。
2. 特に、何が何でもハナを叩きそうな「逃げ」馬、内枠を引き当てて好位をキープする「先行」馬には強力なマーク（印）をつけ、地方特有の展開面での有利不利を完全可視化せよ。

【出力フォーマット】
以下の3つのセクション構成のみを出力せよ。余計な前置きや挨拶は一切禁止する。

### 📊 全頭精密診断・地方ダート適性リスト
必ず以下の列を持つMarkdownテーブル形式で今回の出走馬を全頭出力せよ。
| 馬番 | 馬名 | 父 | 母 | ダート砂適性 | 脚質 | 人気 | 評価 | 理由 |
※【脚質】列には、「逃げ🔥」「先行📢」「差し」「追込」のように、前残りが基本の地方戦で主導権を握る馬がひと目でわかるよう絵文字付きで印をつけよ！
※評価は（◎、○、▲、△、注、消）で厳選せよ。

### 📈 地方走破タイム・砂質トラックバイアス深層データ分析
1. 【地方走破理論・スピード指数分析】: 開催場（大井・川崎・船橋・浦和・園田・高知など）の現在の馬場状態（不良・重・稍重など）から、ダート走破タイムの基準値・補正値が最も優秀な上位3頭。
2. 【地方小回り・ハナ争い完全看破】: 今回1角までにハナを叩く可能性が最も高い「逃げ🔥」馬の特定と、競り合いの有無。それによって壊滅するか、あるいはマイペースで逃げ切れるかの展開予測。
3. 【移籍・外厩・叩き一変シグナル】: 中央からの転入初戦、あるいはヤリ気配の強い地方外厩帰り、叩き2戦目の上積みから、今回激走する気配がある下剋上穴馬。
4. 【地方コース×血統マトリクス】: その地方競馬場の砂質（大井のタペタ系新砂、タフな門別・高知の砂など）に最も合致するパワー・マッド適性配合馬。

### 💰 三連複フォーメーション：厳選15点指示書
投資効率を最大化する【合計15点】のフォーメーションを強制生成せよ。
 - 1頭目（軸馬）：◎（1頭）
 - 2頭目（対抗）：○や▲から「厳選した2頭」のみを指定
 - 3頭目（紐・穴）：◎、○、▲、△、注を含めた「合計7頭」を指定
※計算式 : 1頭 × 2頭 × (7頭 - 2頭) ＝ 【15点】に完全固定。

フォーマット例：
**◎ 軸馬: 〇番 (馬名)**
1頭目：〇
2頭目：〇, 〇
3頭目：〇, 〇, 〇, 〇, 〇, 〇, 〇"""

                prompt = base_instruction + f"\n対象データ: {target_data}\n総監督バイアス: {bias}\n予算: {budget}円"

                with st.spinner(f"🚀 地方小回り展開・砂適性をマッピング中... ({m_name})"):
                    response = model.generate_content(prompt)
                    output_text = response.text
                    st.session_state["res"] = output_text
                    
                    now_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                    with open(os.path.join(LOG_DIR, f"地方3連複15点_{now_str}.txt"), "w", encoding="utf-8") as log_f:
                        log_f.write(f"=== 予想生成日時: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n🧠 地方バイアス: {bias}\n\n" + output_text)
                    st.toast("💾 地方予想ログを仮保存しました！結果復習時にファイル名が自動変更されます。", icon="💾")
                    st.rerun()
        except Exception as e:
            st.error(f"解析エラー: {e}")

with col2:
    st.subheader("📊 投資指示書 ＆ 復習ルーム連動表示")
    if st.session_state["res"]:
        st.markdown(st.session_state["res"])
st.caption("Baru Stable AI Local Pro v24.8 - Local Edition")

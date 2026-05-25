import streamlit as st
import google.generativeai as genai
import json
import os
import requests
from bs4 import BeautifulSoup
import datetime
import re

# --- 設定保存機能 ---
CONFIG_FILE = "baru_triple_config.json"
LOG_DIR = "racing_logs_triple"  # トリプル馬単専用の独立フォルダ
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
        # 【トリプル馬単特化】馬単を3連続で射抜くための、地方の展開・ハナ争い・完全前残りバイアスに特化した初期指示
        "b": "トリプル馬単対象地方レース（主に後半3R）のトラックバイアス, 砂質, 1角ポジション争い, 絶対に崩れない軸馬の選定, および逆転候補の展開利・ハナ争いを統合解析せよ。"
    }

def clean_filename(name):
    if not name:
        return ""
    clean = re.sub(r'[\\/*?:"<>| \t]', '_', name.strip())
    return clean[:50]

cfg = load_cfg()

# 👑 【完全換装】総監督のご指示通り、大看板タイトルおよびタブ名を「トリプル馬単地方競馬AI Pro」仕様へ完全リニューアル！
st.set_page_config(page_title="Baru トリプル馬単地方競馬AI Pro v24.8.5", layout="wide", initial_sidebar_state="expanded")
st.title("🏇 Baru トリプル馬単地方競馬AI Pro - 【Ver 24.8.5 高速・軽量化安定版】")

with st.sidebar:
    st.header("⚙️ 総監督ルーム（司令部）[Triple]")
    api_key = st.text_input("Gemini API KEY", value=cfg.get("k", ""), type="password")
    bias = st.text_area("🧠 総監督バイアス（トリプル馬単補正値）", value=cfg.get("b"), height=150)
    budget = st.number_input("1レース予算(円)", value=1500, step=100)
    if st.button("💾 設定保存"):
        save_cfg(api_key, bias)
        st.success("トリプル馬単専用設定を保存しました。")

    # 📂 過去ログ呼び出し ＆ 復習ルーム
    st.markdown("---")
    st.header("📂 過去ログ復習 [Triple]")
    log_files = sorted([f for f in os.listdir(LOG_DIR) if f.endswith(".txt")], reverse=True)
    
    if log_files:
        selected_log = st.selectbox("復習・確認する対象レース", log_files)
        
        if st.button("📖 予想指示書を呼び出す"):
            with open(os.path.join(LOG_DIR, selected_log), "r", encoding="utf-8") as f:
                st.session_state["res"] = f.read()
            st.success(f"{selected_log} を読み込みました！")
            
        st.markdown("---")
        st.subheader("🏁 対象・レース結果コピペ")
        st.caption("💡 1行目にレース名を入力し、2行目から結果（着順・払戻金・通過順）を丸ごとコピペしてください。")
        result_copypaste = st.text_area("1行目：レース名 / 2行目〜：結果コピペ", height=200)
        
        if st.button("🚨 馬単の着順・ハナ争いと照合して復習"):
            if not api_key or not result_copypaste.strip():
                st.error("APIキーと結果データが必要です")
            else:
                try:
                    genai.configure(api_key=api_key)
                    available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                    m_name = next((m for m in available_models if "pro" in m.lower()), available_models[0] if available_models else "models/gemini-1.5-flash")
                    model = genai.GenerativeModel(m_name)
                    
                    lines = result_copypaste.splitlines()
                    raw_title = lines[0].strip() if lines else "対象レース結果"
                    cleaned_title = clean_filename(raw_title)
                    
                    with open(os.path.join(LOG_DIR, selected_log), "r", encoding="utf-8") as f:
                        past_prediction = f.read()
                        
                    p_1 = "あなたは総監督Baruの右腕競馬AIだ。提示されたトリプル馬単対象レースの予想指示書と、実際のレース結果コピペを徹底的に突き合わせ、短く簡潔に箇条書きで猛省レポートを作成せよ。\n\n"
                    p_2 = f"【タイトル】最上部に見出し「### 🏁 {raw_title} 戦果照合」を出力せよ。\n\n"
                    p_3 = "【馬単解析掟】\n1. 1着・2着の入線パターンとコーナー通過順から、想定外の逃げ残りや差し遅れのズレを炙り出せ。\n2. 馬単高配当を演出した人気薄の激走理由（地方砂質・トラックバイアス）の読みのズレを猛省せよ。\n3. 次回トリプル馬単を仕留めるため、バイアス設定をどう微調整すべきか簡潔に導け。\n\n"
                    p_4 = f"【出力フォーマット】\n### 🏁 {raw_title} 戦果照合\n馬単払戻金および戦果の整理\n\n### 🧠 1着2着・ハナ争いのズレ解剖\n馬単の着順に直結した地方小回り展開・バイアスのズレ分析\n\n### 🛠️ 次回制覇へのAIロジック微調整案\n地方ダート補正や馬場バイアスの具体的アドバイス\n\n"
                    p_5 = f"---\n【当時の予想指示書】:\n{past_prediction}\n\n【実際のレース結果コピペ】:\n{result_copypaste}"
                    
                    review_prompt = p_1 + p_2 + p_3 + p_4 + p_5

                    with st.spinner("1・2着展開のズレから猛省・復習中..."):
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
                        st.success(f"💾 ファイル名を「{new_filename}」に変更し、復習ログを完全保存しました！")
                        st.rerun()
                except Exception as e:
                    st.error(f"復習解析エラー: {e}")
    else:
        st.info("まだ保存された予想ログはありません。")

if "res" not in st.session_state:
    st.session_state["res"] = ""

col1, col2 = st.columns([1, 1])
with col1:
    st.subheader("📋 対象レース 馬柱・オッズ混在テキスト入力")
    url_input = st.text_input("🔗 地方レースURL（netkeiba等）")
    manual_data = st.text_area("✍️ 対象レースコピペデータ", height=500)
    
    if st.button("🚀 構造解剖＆勝負指示書生成"):
        try:
            target_data = ""
            if url_input:
                with st.spinner("対象レースデータをスクレイピング中..."):
                    headers = {"User-Agent": "Mozilla/5.0"}
                    res = requests.get(url_input, headers=headers)
                    res.encoding = res.apparent_encoding
                    soup = BeautifulSoup(res.text, "html.parser")
                    main_data = soup.find_all("table")
                    for table in main_data:
                        target_data += table.get_text(separator="\n", strip=True) + "\n"
                    target_data = target_data[:15000]
            else:
                target_data = manual_data[:15000]

            if not api_key or not target_data:
                st.error("必要なデータが不足しています")
            else:
                genai.configure(api_key=api_key)
                available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                m_name = next((m for m in available_models if "pro" in m.lower()), available_models[0] if available_models else "models/gemini-1.5-flash")
                model = genai.GenerativeModel(m_name)
                
                # 【トリプル馬単特化型プロンプト】馬単の1着2着を執念で当てるためのロジック
                base_instruction = """あなたはトリプル馬単を完全ハックするプロ競馬AIであり、総監督Baruの絶対的右腕だ。
入力されたデータから人気・枠番・馬番・馬名・オッズ・通過順を完全に解剖し、地方ダート戦で馬単の「1着・2着」を絶対に逃さない鋭い勝負指示書を最速で作成せよ。

【データ解剖・出力の絶対ルール】
1. 前置き、挨拶、まとめの雑談は一切禁止。即座に出力フォーマットを開始せよ。
2. 地方競馬の馬単で1着に突き抜ける能力（スピード・ハナ奪取率）と、2着に粘り込む地方馬場バイアス適性を最重要視せよ。
3. 理由や分析セクションは、要点のみを鋭い箇条書きでコンパクトに記述し、冗長な表現を徹底的に排除せよ。

【出力フォーマット】
### 📊 全頭精密診断・馬単適性リスト
必ず以下の列を持つMarkdownテーブル形式で今回の出走馬を全頭出力せよ。
| 馬番 | 馬名 | 父 | 母 | 馬単2連対適性 | 脚質 | 人気 | 評価 | 1着2着への決定打 |
※【脚質】列には、「逃げ🔥」「先行📢」「差し」「追込」の印をつけよ。
※評価は（◎、○、▲、△、注、消）で厳選せよ。

### 📈 連対圏（1,2着）深層データ分析
1. 【1着候補・スピード指数分析】: 単勝・馬単1着として突き抜けるタイム・指数を持つ上位3頭（◎○▲級）。
2. 【2着泥臭い粘り込み・ハナ争い看破】: 1角ポジション争いから、地方小回りで2着に粘り込む「逃げ先行」馬、および展開を利する馬の特定。
3. 【配当を破壊する激走穴馬】: 人気薄ながら2着以内に突っ込んで配当を跳ね上げるポテンシャルを持つ下剋上穴馬の特定。
4. 【地方コース×砂質マトリクス】: 当該競馬場の現在の砂質状態（イン有利、外伸び、砂の深さ等）に血統面・馬体重面で最も合致する特注馬。

### 💰 馬単フォーメーション：トリプル制覇の厳選12点指示書
投資効率とカバー率を最大化する【合計12点】のフォーメーションを強制生成せよ。
 - 1着（頭固定）：◎および○（合計2頭）
 - 2着（ヒモ連対）：◎、○、▲、△、注から「厳選した7頭（1着指定馬含む）」を指定
※計算式 : 2頭 × (7頭 - 1頭) ＝ 【12点】に完全固定。

フォーマット例：
**🏆 馬単フォーメーション指示（計12点）**
1着：〇, 〇
2着：〇, 〇, 〇, 〇, 〇, 〇, 〇"""

                prompt = base_instruction + f"\n対象データ: {target_data}\n総監督バイアス: {bias}\n予算: {budget}円"

                with st.spinner(f"🚀 連対圏（1,2着）をマッピング中... ({m_name})"):
                    response = model.generate_content(prompt)
                    output_text = response.text
                    st.session_state["res"] = output_text
                    
                    now_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                    with open(os.path.join(LOG_DIR, f"トリプル馬単12点_{now_str}.txt"), "w", encoding="utf-8") as log_f:
                        log_f.write(f"=== 予想生成日時: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n🧠 トリプルバイアス: {bias}\n\n" + output_text)
                    st.toast("💾 予想ログを保存しました！", icon="💾")
                    st.rerun()
        except Exception as e:
            st.error(f"解析エラー: {e}")

with col2:
    st.subheader("📊 予想指示書 ＆ 復習ルーム連動表示")
    if st.session_state["res"]:
        st.markdown(st.session_state["res"])

# 👑 【完全換装】フッターのクレジットも総監督指定通りトリプル馬単仕様へ！
st.caption("🏇 Baru トリプル馬単地方競馬AI Pro - 【Ver 24.8.5 高速・軽量化安定版】")

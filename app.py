import streamlit as st
import re

# 1. 画面の基本設定
st.set_page_config(page_title="Baru競馬AI Pro", page_icon="🎯", layout="wide")

st.title("🎯 Baru競馬AI Pro 〜研究者レベル最終進化版〜")
st.write("ネット競馬コピペデータ自動パース・インサイダーオッズ歪み・秋元フィルター完全統合システム")
st.markdown("---")

# ----------------------------------------------------
# 2. データの入力エリア（画面の左サイドバー）
# ----------------------------------------------------
st.sidebar.header("🛠 レース条件設定")
venue = st.sidebar.selectbox("競馬場", ["船橋", "大井", "川崎", "浦和"], index=0)
race_num = st.sidebar.number_input("レース番号", min_value=1, max_value=12, value=3)
race_class = st.sidebar.selectbox("クラス", ["C3", "C2", "C1", "B3", "A2", "重賞"], index=0)

st.sidebar.markdown("---")

st.sidebar.header("📋 netkeiba 出馬表コピペ入力")
pasted_data = st.sidebar.text_area(
    "サイトのテキストを丸ごとここに貼り付けてください",
    height=300,
    placeholder="3R C3二組下選抜馬...\n11--\nモズアスコット...\n(コマンズ)..."
)

# ----------------------------------------------------
# 🌟 【完全解決版】本物の馬番ブロックだけを正確に狙い撃ちするパースロジック
# ----------------------------------------------------
def parse_netkeiba_perfect(text):
    if not text.strip():
        return []
        
    # 1. 特殊な空白文字、全角スペースをすべて通常の半角スペースに一括クリア
    cleaned_text = text.replace('\xa0', ' ').replace('\u3000', ' ')
    
    # 2. 特殊なハイフン・長音記号（–, —, ―, ─）をすべて標準の「-」に置換
    cleaned_text = re.sub(r'[–—―─−-]', '-', cleaned_text)
    
    # 3. 【超重要】馬のデータの開始地点（例: 「11--」「22--」など、改行＋数字＋ハイフン2つ）だけを厳密に探す
    # 過去成績の中にある「12番」や「6人」などの数字で誤分割するのを完全に防ぎます
    matches = list(re.finditer(r'\n\s*(\d+)--', cleaned_text))
    
    if not matches:
        return []
        
    parsed_entries = []
    
    # マッチした位置を元に、馬ごとのテキストブロックを綺麗に切り出す
    for idx, match in enumerate(matches):
        raw_num = match.group(1).strip()
        start_pos = match.end()
        
        # 次の馬の開始位置、もしくはテキストの最後までをこの馬のブロックとする
        end_pos = matches[idx+1].start() if idx + 1 < len(matches) else len(cleaned_text)
        block_content = cleaned_text[start_pos:end_pos]
        
        # 枠番＋馬番（例: 8枠10番の810など）のケア。3桁以上の場合は下2桁を馬番とする
        maruban = int(raw_num[1:]) if len(raw_num) >= 3 and raw_num.startswith(('1','2','3','4','5','6','7','8')) else int(raw_num)
            
        lines = [line.strip() for line in block_content.split('\n') if line.strip()]
        if not lines:
            continue
            
        # --- 基本変数の初期化 ---
        jockey = "不明"
        kyashitsu = "差し"  # デフォルト値
        tan_odds = 99.0
        ninki = 10
        time_score = 75.0
        
        # 1. 脚質の判定 (ブロックの上部から検出)
        for line in lines[:10]:
            if line in ["逃", "逃げ"]: kyashitsu = "逃げ"; break
            if line in ["先", "先行"]: kyashitsu = "先行"; break
            if line in ["差", "差し"]: kyashitsu = "差し"; break
            if line in ["追", "追い込み"]: kyashitsu = "追い込み"; break
            
        # 2. オッズと人気の抽出 (例: "28.3(8人気)" のような形をあらゆるスペース不問で探す)
        odds_pattern = re.compile(r'([\d.]+)\s*\(\s*(\d+)\s*人気\s*\)')
        for line in lines[:20]: # 馬ブロックの前半部分から探す
            match = odds_pattern.search(line)
            if match:
                tan_odds = float(match.group(1))
                ninki = int(match.group(2))
                break
                
        # 3. 騎手名の自動抽出
        known_jockeys = ['藤江渉', '福原杏', '沖響主', '山口達', '笠野雄', '濱田達', '山林堂', '加藤雄', '吉留孝', '本橋孝', '古岡勇', '秋元耕']
        for line in lines[:25]:
            for kj in known_jockeys:
                if line.startswith(kj):
                    jockey = kj
                    break
            if jockey != "不明":
                break
                
        # 4. 過去の走破タイムの抽出とスコア化
        time_pattern = re.compile(r'ダ\d+\s+(\d+):(\d+\.\d+)')
        times = []
        for line in lines:
            match = time_pattern.search(line)
            if match:
                minutes = int(match.group(1))
                seconds = float(match.group(2))
                times.append(minutes * 60 + seconds)

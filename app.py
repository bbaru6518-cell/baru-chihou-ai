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
# 🌟 【完全修正版】ネット競馬縦型コピーデータ専用クレンジング＆パースロジック
# ----------------------------------------------------
def parse_netkeiba_clean(text):
    if not text.strip():
        return []
        
    # 1. 特殊な空白（ノーブレークスペース等）を通常の半角スペースに一括変換
    cleaned_text = text.replace('\xa0', ' ').replace('\u3000', ' ')
    
    # 2. 「馬番--」の直前の改行を統一し、行頭の余分なスペースを削除
    cleaned_text = re.sub(r'\n\s*(\d+)--', r'\n\1--', cleaned_text)
    
    # 3. 馬番（例: 11--, 810--）を基準にテキストを確実に分割
    # 行頭、または改行直後の「数字+ハイフン2つ以上」で区切る
    raw_blocks = re.split(r'\n?(\d+)--\s*\n?', cleaned_text)
    
    if len(raw_blocks) < 3:
        return []
        
    parsed_entries = []
    
    # 最初のブロック（レースヘッダー情報）を飛ばして、[馬番, 中身, 馬番, 中身...] でループ
    for i in range(1, len(raw_blocks), 2):
        raw_num = raw_blocks[i].strip()
        block_content = raw_blocks[i+1] if i+1 < len(raw_blocks) else ""
        
        if not raw_num or not block_content.strip():
            continue
            
        # 馬番の整形 (例: 8枠10番の "810" は下2桁の "10" を取る。1〜2桁はそのまま)
        if len(raw_num) >= 3 and raw_num.startswith(('1','2','3','4','5','6','7','8')):
            maruban = int(raw_num[1:])
        else:
            maruban = int(raw_num)
            
        lines = [line.strip() for line in block_content.split('\n') if line.strip()]
        
        # 変数の初期化
        jockey = "不明"
        kyashitsu = "差し" # デフォルト
        tan_odds = 99.0
        ninki = 10
        time_score = 75.0
        
        # 脚質の判定
        for line in lines[:15]:
            if line in ["逃", "逃げ"]: kyashitsu = "逃げ"; break
            if line in ["先", "先行"]: kyashitsu = "先行"; break
            if line in ["差", "差し"]: kyashitsu = "差し"; break
            if line in ["追", "追い込み"]: kyashitsu = "追い込み"; break
            
        # オッズと人気の抽出 (例: "28.3(8人気)" や "28.3 (8人気)" を探す)
        odds_pattern = re.compile(r'([\d.]+)\s*\(\s*(\d+)\s*人気\s*\)')
        for line in lines:
            match = odds_pattern.search(line)
            if match:
                tan_odds = float(match.group(1))
                ninki = int(match.group(2))
                break
                
        # 騎手名の抽出
        known_jockeys = ['藤江渉', '福原杏', '沖響主', '山口達', '笠野雄', '濱田達', '山林堂', '加藤雄', '吉留孝', '本橋孝', '古岡勇', '秋元耕']
        for line in lines:
            for kj in known_jockeys:
                if line.startswith(kj):
                    jockey = kj
                    break
            if jockey != "不明":
                break
                
        # 走破タイム（過去走から最新を自動取得してスコア化）
        time_pattern = re.compile(r'ダ\d+\s+(\d+):(\d+\.\d+)')
        times = []
        for line in lines:
            match = time_pattern.search(line)
            if match:
                minutes = int(match.group(1))
                seconds = float(match.group(2))
                times.append(minutes * 60 + seconds)
                
        if times:
            latest_time = times[0]
            # 船橋1500m/1400mを想定した走破AIタイムスコアリング（簡易版）
            time_score = round(100 - (latest_time - 95.0) * 2, 1)
            if time_score > 98: time_score = 98.0
            if time_score < 60: time_score = 60.0

        fuku_odds_min = round(max(1.1, tan_odds * 0.25), 1)
        
        parsed_entries.append({
            'maruban': maruban,
            'jockey': jockey,
            'kyashitsu': kyashitsu,
            'tan_odds': tan_odds,
            'fuku_odds_min': fuku_odds_min,
            'time_score': time_score,
            'ninki': ninki
        })
        
    return parsed_entries

# ----------------------------------------------------
# データの読み込み実行
# ----------------------------------------------------
entries = parse_netkeiba_clean(pasted_data)

if pasted_data.strip() and not entries:
    st.sidebar.error("⚠️ パースに失敗しました。コピーしたデータの範囲を確認してください。")
elif not pasted_data.strip():
    st.sidebar.info("💡 現在はテスト用の自動デモデータを読み込んでいます。実際のレース時はここに貼り付けてください。")
    # デフォルトの船橋3Rテストデータ
    entries = [
        {'maruban': 11, 'ninki': 8,  'tan_odds': 28.3, 'fuku_odds_min': 4.5, 'time_score': 74.0, 'jockey': '藤江渉',   'kyashitsu': '差し'},
        {'maruban': 2,  'ninki': 5,  'tan_odds': 15.8, 'fuku_odds_min': 3.2, 'time_score': 79.0, 'jockey': '福原杏',   'kyashitsu': '差し'},
        {'maruban': 3,  'ninki': 11, 'tan_odds': 74.0, 'fuku_odds_min': 7.2, 'time_score': 65.0, 'jockey': '沖響主',   'kyashitsu': '追い込み'},
        {'maruban': 4,  'ninki': 2,  'tan_odds': 4.5,  'fuku_odds_min': 1.5, 'time_score': 88.0, 'jockey': '山口達',   'kyashitsu': '差し'},
        {'maruban': 5,  'ninki': 3,  'tan_odds': 8.9,  'fuku_odds_min': 2.1, 'time_score': 91.5, 'jockey': '笠野雄',   'kyashitsu': '追い込み'},
        {'maruban': 6,  'ninki': 7,  'tan_odds': 22.2, 'fuku_odds_min': 4.0, 'time_score': 76.0, 'jockey': '濱田達',   'kyashitsu': '追い込み'},
        {'maruban': 7,  'ninki': 10, 'tan_odds': 72.8, 'fuku_odds_min': 2.5, 'time_score': 80.0, 'jockey': '山林堂',   'kyashitsu': '追い込み'},
        {'maruban': 8,  'ninki': 9,  'tan_odds': 59.1, 'fuku_odds_min': 6.0, 'time_score': 71.0, 'jockey': '加藤雄',   'kyashitsu': '差し'},
        {'maruban': 9,  'ninki': 6,  'tan_odds': 17.0, 'fuku_odds_min': 3.5, 'time_score': 85.0, 'jockey': '吉留孝',   'kyashitsu': '差し'},
        {'maruban': 10, 'ninki': 4,  'tan_odds': 14.1, 'fuku_odds_min': 3.0, 'time_score': 82.0, 'jockey': '本橋孝',   'kyashitsu': '追い込み'},
    ]

# ----------------------------------------------------
# 3. AIコア解析ロジック & 結果表示
# ----------------------------------------------------
if entries:
    st.subheader("📋 AIが自動認識した出走馬データ一覧")
    st.dataframe(entries, use_container_width=True)

    front_runners = len([h for h in entries if h['kyashitsu'] in ['逃げ', '先行']])
    odds_1st_list = [h['tan_odds'] for h in entries if h['ninki'] == 1]
    odds_3rd_list = [h['tan_odds'] for h in entries if h['ninki'] == 3]
    
    odds_1st = odds_1st_list[0] if odds_1st_list else 2.0
    odds_3rd = odds_3rd_list[0] if odds_3rd_list else 6.0
    odds_gap = odds_3rd - odds_1st

    turbulence_score = 0
    if race_class == 'C3': turbulence_score += 25
    if front_runners >= 5:  turbulence_score += 40
    elif front_runners <= 2: turbulence_score -= 20
    if odds_gap < 5.0:      turbulence_score += 20

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📊 レース構造解析結果")
        if turbulence_score >= 60:
            st.error(f"判定: 🔥 大荒れ警戒（スコア: {turbulence_score}点）")
        elif 20 <= turbulence_score < 60:
            st.warning(f"判定: ⚖️ 中穴傾向（スコア: {turbulence_score}点）")
        else:
            st.success(f"判定: 🟢 ガチガチ本命（スコア: {turbulence_score}点）")

    sorted_horses = sorted(entries, key=lambda x: x['ninki'])
    total_horses = len(sorted_horses)

    # 1列目（軸）
    zone1_pool = sorted_horses[:4]
    horse_1st = sorted_horses[0]
    remaining_zone1 = [h for h in zone1_pool if h['maruban'] != horse_1st['maruban']]
    
    first_row = [horse_1st['maruban']]
    if remaining_zone1:
        best_time_horse = max(remaining_zone1, key=lambda x: x['time_score'])
        if best_time_horse['jockey'] != '秋元耕成':
            first_row.append(best_time_horse['maruban'])
    first_row.sort()

    # 2列目（相手）
    zone2_pool = sorted_horses[3:8] if total_horses >= 8 else sorted_horses[1:]
    second_row = [h['maruban'] for h in zone2_pool if h['jockey'] != '秋元耕成']
    second_row.sort()

    # 3列目（穴紐フィルター）
    zone3_pool = sorted_horses[max(0, total_horses-5):]
    third_row = []
    ana_jockey_master = ['山林堂', '吉留孝', '古岡勇', '加藤雄', '藤江渉', '笠野雄']

    with col2:
        st.subheader("🔎 大穴ゾーン個別インサイダー解析")
        for h in zone3_pool:
            if h['jockey'] == '秋元耕成':
                st.text(f"❌ 馬番:{h['maruban']:02d} -> 強制排除")
                continue
            is_selected = False
            reasons = []
            if h['tan_odds'] >= 25.0 and h['fuku_odds_min'] <= 3.5:
                is_selected = True; reasons.append("複勝歪み")
            if h['jockey'] in ana_jockey_master:
                is_selected = True; reasons.append(f"穴騎手({h['jockey']})")
            if turbulence_score >= 60:
                is_selected = True; reasons.append("大荒れ救済")
                
            if is_selected:
                third_row.append(h['maruban'])
                st.code(f"⚠️ 馬番:{h['maruban']:02d} -> 採用 [{', '.join(reasons)}]", language="text")
                
        third_row.sort()

    # 4. 点数計算＆出力
    st.markdown("---")
    st.subheader("🎯 【最終出力】Baru式・3連複フォーメーション配置")

    final_tickets = set()
    for r1 in first_row:
        for r2 in second_row:
            for r3 in third_row:
                if r1 != r2 and r1 != r3 and r2 != r3:
                    ticket = tuple(sorted([r1, r2, r3]))
                    final_tickets.add(ticket)
    sorted_tickets = sorted(list(final_tickets))

    st.success(f"🔥 【合計購入点数: {len(sorted_tickets)} 点】")

    if sorted_tickets:
        def format_row(row_list): return "　".join([f"{num:02d}" for num in list(set(row_list))])
        st.code(f"1番（軸）　　 🔴【 {format_row(first_row)} 】", language="text")
        st.code(f"2番（相手）　 🔵【 {format_row(second_row)} 】", language="text")
        st.code(f"3番（穴紐）　 🟢【 {format_row(third_row)} 】", language="text")

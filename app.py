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

# 🚨 ここに「解析ボタン」を設置しました！
start_analysis = st.sidebar.button("🚀 レース解析を実行", type="primary")

# ----------------------------------------------------
# 🌟 【完全解決版】本物の馬番ブロックだけを正確に狙い撃ちするパースロジック
# ----------------------------------------------------
def parse_netkeiba_perfect(text):
    if not text.strip():
        return []
        
    cleaned_text = text.replace('\xa0', ' ').replace('\u3000', ' ')
    cleaned_text = re.sub(r'[–—―─−-]', '-', cleaned_text)
    
    # 馬番の開始地点（例: 「11--」「22--」など、改行＋数字＋ハイフン2つ）だけを厳密に探す
    matches = list(re.finditer(r'\n\s*(\d+)--', cleaned_text))
    
    if not matches:
        return []
        
    parsed_entries = []
    
    for idx, match in enumerate(matches):
        raw_num = match.group(1).strip()
        start_pos = match.end()
        end_pos = matches[idx+1].start() if idx + 1 < len(matches) else len(cleaned_text)
        block_content = cleaned_text[start_pos:end_pos]
        
        maruban = int(raw_num[1:]) if len(raw_num) >= 3 and raw_num.startswith(('1','2','3','4','5','6','7','8')) else int(raw_num)
        lines = [line.strip() for line in block_content.split('\n') if line.strip()]
        if not lines:
            continue
            
        jockey = "不明"
        kyashitsu = "差し"  
        tan_odds = 99.0
        ninki = 10
        time_score = 75.0
        
        # 1. 脚質の判定
        for line in lines[:10]:
            if line in ["逃", "逃げ"]: kyashitsu = "逃げ"; break
            if line in ["先", "先行"]: kyashitsu = "先行"; break
            if line in ["差", "差し"]: kyashitsu = "差し"; break
            if line in ["追", "追い込み"]: kyashitsu = "追い込み"; break
            
        # 2. オッズと人気の抽出
        odds_pattern = re.compile(r'([\d.]+)\s*\(\s*(\d+)\s*人気\s*\)')
        for line in lines[:20]:
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
                
        if times:
            latest_time = times[0]
            time_score = round(100 - (latest_time - 95.0) * 2, 1)
            time_score = max(60.0, min(98.0, time_score))

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
        
        if len(parsed_entries) >= 11:
            break
        
    return parsed_entries

# ----------------------------------------------------
# 3. メイン処理（デモ表示 or ボタン押下時の解析）
# ----------------------------------------------------
# データを貼り付けた状態で、かつボタンが押された場合のみ解析を実行
if pasted_data.strip() and start_analysis:
    entries = parse_netkeiba_perfect(pasted_data)
    
    if not entries:
        st.error("⚠️ パースに失敗しました。コピーしたデータの範囲か、馬番の表記を確認してください。")
else:
    # 初期状態、またはデータ未入力時はデモデータを表示
    if not pasted_data.strip():
        st.info("💡 左のテキストエリアにデータを貼り付けて「🚀 レース解析を実行」を押してください。現在はデモデータを表示中。")
    else:
        st.warning("👈 データを貼り付けたら、左サイドバーの下にある「🚀 レース解析を実行」ボタンを押してください！")
        
    entries = [
        {'maruban': 1,  'ninki': 8,  'tan_odds': 28.3, 'fuku_odds_min': 4.5, 'time_score': 74.0, 'jockey': '藤江渉',   'kyashitsu': '差し'},
        {'maruban': 2,  'ninki': 5,  'tan_odds': 15.8, 'fuku_odds_min': 3.2, 'time_score': 79.0, 'jockey': '福原杏',   'kyashitsu': '差し'},
        {'maruban': 3,  'ninki': 11, 'tan_odds': 74.0, 'fuku_odds_min': 7.2, 'time_score': 65.0, 'jockey': '沖響主',   'kyashitsu': '追い込み'},
        {'maruban': 4,  'ninki': 2,  'tan_odds': 4.5,  'fuku_odds_min': 1.5, 'time_score': 88.0, 'jockey': '山口達',   'kyashitsu': '差し'},
        {'maruban': 5,  'ninki': 3,  'tan_odds': 8.9,  'fuku_odds_min': 2.1, 'time_score': 91.5, 'jockey': '笠野雄',   'kyashitsu': '追い込み'},
        {'maruban': 6,  'ninki': 7,  'tan_odds': 22.2, 'fuku_odds_min': 4.0, 'time_score': 76.0, 'jockey': '濱田達',   'kyashitsu': '追い込み'},
        {'maruban': 7,  'ninki': 10, 'tan_odds': 72.8, 'fuku_odds_min': 2.5, 'time_score': 80.0, 'jockey': '山林堂',   'kyashitsu': '追い込み'},
        {'maruban': 8,  'ninki': 9,  'tan_odds': 59.1, 'fuku_odds_min': 6.0, 'time_score': 71.0, 'jockey': '加藤雄',   'kyashitsu': '差し'},
        {'maruban': 9,  'ninki': 6,  'tan_odds': 17.0, 'fuku_odds_min': 3.5, 'time_score': 85.0, 'jockey': '吉留孝',   'kyashitsu': '差し'},
        {'maruban': 10, 'ninki': 4,  'tan_odds': 14.1, 'fuku_odds_min': 3.0, 'time_score': 82.0, 'jockey': '本橋孝',   'kyashitsu': '追い込み'},
        {'maruban': 11, 'ninki': 1,  'tan_odds': 1.6,  'fuku_odds_min': 1.1, 'time_score': 95.0, 'jockey': '古岡勇',   'kyashitsu': '差し'},
    ]

# ----------------------------------------------------
# 4. AIコア解析ロジック & 結果表示
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

    # 5. 点数計算＆出力
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

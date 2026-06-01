import streamlit as st

# 1. 画面の基本設定
st.set_page_config(page_title="Baru競馬AI Pro", page_icon="🎯", layout="wide")

st.title("🎯 Baru競馬AI Pro 〜研究者レベル最終進化版〜")
st.write("インサイダーオッズ歪み・穴騎手・秋元フィルター完全統合システム")
st.markdown("---")

# ----------------------------------------------------
# 2. データの入力エリア（画面の左サイドバー）
# ----------------------------------------------------
st.sidebar.header("🛠 レース条件設定")
venue = st.sidebar.selectbox("競馬場", ["船橋", "大井", "川崎", "浦和"])
race_num = st.sidebar.number_input("レース番号", min_value=1, max_value=12, value=3)
race_class = st.sidebar.selectbox("クラス", ["C3", "C2", "C1", "B3", "A2", "重賞"])

st.sidebar.markdown("---")

# 【新機能】ここにネット競馬などの馬柱テキストをコピペできるようにする
st.sidebar.header("📋 出馬表（馬柱）データの入力")
pasted_data = st.sidebar.text_area(
    "ここにデータを貼り付けてください",
    height=200,
    placeholder="例：\n11 古岡勇樹 先行 1.6 1.1 95.0 1\n4 山口達弥 逃げ 4.5 1.5 88.0 2",
    help="枠やWEBサイトからコピーしたテキストをそのまま貼り付けられます。"
)

# ----------------------------------------------------
# データ解析用のベースデータ準備（コピペがない場合はデフォルトを使用）
# ----------------------------------------------------
entries = []

if pasted_data.strip():
    # バルさんが貼り付けたテキストを1行ずつ解析（パース）するロジック
    try:
        lines = pasted_data.strip().split("\n")
        for line in lines:
            parts = line.split()
            if len(parts) >= 7:
                entries.append({
                    'maruban': int(parts[0]),
                    'jockey': parts[1],
                    'kyashitsu': parts[2],
                    'tan_odds': float(parts[3]),
                    'fuku_odds_min': float(parts[4]),
                    'time_score': float(parts[5]),
                    'ninki': int(parts[6])
                })
        if not entries:
            st.sidebar.error("⚠️ データの形式が正しくありません。スペース区切りで入力してください。")
    except Exception as e:
        st.sidebar.error(f"⚠️ データ解析エラー: {e}")
else:
    st.sidebar.info("💡 現在はテスト用の自動デモデータを読み込んでいます。実際のレース時はここに貼り付けてください。")
    # コピペが空の時は、いつもの船橋3Rのテストデータを入れる
    entries = [
        {'maruban': 11, 'ninki': 1,  'tan_odds': 1.6,  'fuku_odds_min': 1.1, 'time_score': 95.0, 'jockey': '古岡勇樹', 'kyashitsu': '先行'},
        {'maruban': 4,  'ninki': 2,  'tan_odds': 4.5,  'fuku_odds_min': 1.5, 'time_score': 88.0, 'jockey': '山口達弥', 'kyashitsu': '逃げ'},
        {'maruban': 5,  'ninki': 3,  'tan_odds': 8.9,  'fuku_odds_min': 2.1, 'time_score': 91.5, 'jockey': '笠野雄大', 'kyashitsu': '先行'},
        {'maruban': 10, 'ninki': 4,  'tan_odds': 14.1, 'fuku_odds_min': 3.0, 'time_score': 82.0, 'jockey': '本橋孝太', 'kyashitsu': '差し'},
        {'maruban': 2,  'ninki': 5,  'tan_odds': 15.8, 'fuku_odds_min': 3.2, 'time_score': 79.0, 'jockey': '福原杏',   'kyashitsu': '差し'},
        {'maruban': 9,  'ninki': 6,  'tan_odds': 17.0, 'fuku_odds_min': 3.5, 'time_score': 85.0, 'jockey': '吉留孝司', 'kyashitsu': '差し'},
        {'maruban': 6,  'ninki': 7,  'tan_odds': 22.2, 'fuku_odds_min': 4.0, 'time_score': 76.0, 'jockey': '濱田達也', 'kyashitsu': '先行'},
        {'maruban': 1,  'ninki': 8,  'tan_odds': 28.3, 'fuku_odds_min': 4.5, 'time_score': 74.0, 'jockey': '藤江渉',   'kyashitsu': '追い込み'},
        {'maruban': 8,  'ninki': 9,  'tan_odds': 59.1, 'fuku_odds_min': 6.0, 'time_score': 71.0, 'jockey': '加藤雄真', 'kyashitsu': '逃げ'},
        {'maruban': 7,  'ninki': 10, 'tan_odds': 72.8, 'fuku_odds_min': 2.5, 'time_score': 80.0, 'jockey': '山林堂信', 'kyashitsu': '差し'},
        {'maruban': 3,  'ninki': 11, 'tan_odds': 74.0, 'fuku_odds_min': 7.2, 'time_score': 65.0, 'jockey': '秋元耕成', 'kyashitsu': '差し'},
    ]

# ----------------------------------------------------
# 3. AIコア解析ロジック
# ----------------------------------------------------
if entries:
    # 3-1. レース波乱度予測
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
            st.info("💡 戦略: 3列目に大穴・歪み馬を全流しして万馬券をハメにいきます。")
        elif 20 <= turbulence_score < 60:
            st.warning(f"判定: ⚖️ 中穴傾向（スコア: {turbulence_score}点）")
            st.info("💡 戦略: 2列目の4〜8番人気を厚めに。バランス型の布陣。")
        else:
            st.success(f"判定: 🟢 ガチガチ本命（スコア: {turbulence_score}点）")
            st.info("💡 戦合法: 1番人気を固定し、点数を極限まで絞るか見送り。")

    # 3-2. 各列（1・2・3番）の選定
    sorted_horses = sorted(entries, key=lambda x: x['ninki'])
    total_horses = len(sorted_horses)

    # --- 【1番：1列目（軸）】 ---
    zone1_pool = sorted_horses[:4]
    horse_1st_list = [h for h in zone1_pool if h['ninki'] == 1]
    horse_1st = horse_1st_list[0] if horse_1st_list else sorted_horses[0]
    remaining_zone1 = [h for h in zone1_pool if h['maruban'] != horse_1st['maruban']]
    
    first_row = [horse_1st['maruban']]
    if remaining_zone1:
        best_time_horse = max(remaining_zone1, key=lambda x: x['time_score'])
        if best_time_horse['jockey'] != '秋元耕成':
            first_row.append(best_time_horse['maruban'])
        elif len(remaining_zone1) > 1:
            runner_up = sorted(remaining_zone1, key=lambda x: x['time_score'], reverse=True)[1]
            first_row.append(runner_up['maruban'])
    first_row.sort()

    # --- 【2番：2列目（相手）】 ---
    zone2_pool = sorted_horses[3:8] if total_horses >= 8 else sorted_horses[1:]
    second_row = [h['maruban'] for h in zone2_pool if h['jockey'] != '秋元耕成']
    second_row.sort()

    # --- 【3番：3列目（穴紐フィルター）】 ---
    zone3_pool = sorted_horses[max(0, total_horses-5):]
    third_row = []
    ana_jockey_master = ['山林堂信', '吉留孝司', '古岡勇樹', '加藤雄真', '藤江渉', '笠野雄大']

    with col2:
        st.subheader("🔎 大穴ゾーン個別インサイダー解析")
        for h in zone3_pool:
            if h['jockey'] == '秋元耕成':
                st.text(f"❌ 馬番:{h['maruban']:02d} ({h['jockey']}) -> 秋元フィルターで強制排除")
                continue
            
            is_selected = False
            reasons = []
            if h['tan_odds'] >= 25.0 and h['fuku_odds_min'] <= 3.5:
                is_selected = True
                reasons.append("複勝大口歪み")
            if h['jockey'] in ana_jockey_master:
                is_selected = True
                reasons.append(f"穴騎手({h['jockey']})")
            if turbulence_score >= 60:
                is_selected = True
                reasons.append("大荒れ救済")
                
            if is_selected:
                third_row.append(h['maruban'])
                st.code(f"⚠️ 馬番:{h['maruban']:02d} ({h['jockey']}) -> 採用 [{', '.join(reasons)}]", language="text")
            else:
                st.text(f"💤 馬番:{h['maruban']:02d} ({h['jockey']}) -> 武器不足で見送り")
                
        third_row.sort()

    # ----------------------------------------------------
    # 4. 点数計算＆マークシート配置出力
    # ----------------------------------------------------
    st.markdown("---")
    st.subheader("🎯 【最終出力】Baru式・3連複フォーメーション配置（投票画面用）")

    final_tickets = set()
    for r1 in first_row:
        for r2 in second_row:
            for r3 in third_row:
                if r1 != r2 and r1 != r3 and r2 != r3:
                    ticket = tuple(sorted([r1, r2, r3]))
                    final_tickets.add(ticket)
    sorted_tickets = sorted(list(final_tickets))

    st.success(f"🔥 重複目を自動排除した【合計購入点数: {len(sorted_tickets)} 点】")

    if sorted_tickets:
        def format_row(row_list):
            return "　".join([f"{num:02d}" for num in row_list])

        st.code(f"1番（軸）　　 🔴【 {format_row(first_row)} 】", language="text")
        st.code(f"2番（相手）　 🔵【 {format_row(second_row)} 】", language="text")
        st.code(f"3番（穴紐）　 🟢【 {format_row(third_row)} 】", language="text")
        st.markdown("---")
    else:
        st.warning("買い目が生成されませんでした。条件を緩和してください。")

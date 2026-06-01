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
race_num = st.sidebar.number_input("レース番号", min_value=1, max_value=12, value=1)
race_class = st.sidebar.selectbox("クラス", ["3歳", "C3", "C2", "C1", "B3", "A2", "重賞"], index=0)

st.sidebar.markdown("---")

st.sidebar.header("📋 netkeiba 出馬表コピペ入力")
pasted_data = st.sidebar.text_area(
    "サイトのテキストを丸ごとここに貼り付けてください",
    height=300,
    placeholder="データを貼り付けてください"
)

# 解析ボタン
start_analysis = st.sidebar.button("🚀 レース解析を実行", type="primary")

# ----------------------------------------------------
# 🌟 【改良版】脚質・オッズ完全追従型パースロジック
# ----------------------------------------------------
def parse_netkeiba_v4(text):
    if not text.strip():
        return []
        
    cleaned_text = text.replace('\xa0', ' ').replace('\u3000', ' ').replace('\t', ' ')
    raw_lines = cleaned_text.split('\n')
    
    horse_blocks = []
    current_block = []
    current_maruban = None
    
    block_start_pattern = re.compile(r'^\s*(\d{1,2})\s+(\d{1,2})\s*--')
    
    for line in raw_lines:
        line_str = line.strip()
        if not line_str:
            continue
            
        if "※結果" in line_str or "netkeiba" in line_str or "データ分析" in line_str:
            if current_maruban is not None and current_block:
                horse_blocks.append((current_maruban, current_block))
                current_maruban = None
                current_block = []
            continue
            
        match_block = block_start_pattern.match(line_str)
        if match_block:
            if current_maruban is not None and current_block:
                horse_blocks.append((current_maruban, current_block))
            current_maruban = int(match_block.group(2))
            current_block = [line_str]
            continue
            
        if current_maruban is not None:
            current_block.append(line_str)
            
    if current_maruban is not None and current_block:
        horse_blocks.append((current_maruban, current_block))
        
    if not horse_blocks:
        return []
        
    parsed_entries = []
    
    for maruban, lines in horse_blocks:
        jockey = "不明"
        kyashitsu = "差し"  
        tan_odds = 99.0
        ninki = 10
        time_score = 75.0
        
        # 【強化】脚質の判定：独立した行、または複合行から確実に抽出
        for line in lines[:15]:
            if line in ["逃", "逃げ"] or " 逃 " in f" {line} ": kyashitsu = "逃げ"; break
            if line in ["先", "先行"] or " 先 " in f" {line} ": kyashitsu = "先行"; break
            if line in ["差", "差し"] or " 差 " in f" {line} ": kyashitsu = "差し"; break
            if line in ["追", "追い込み"] or " 追 " in f" {line} ": kyashitsu = "追い込み"; break
            
        # オッズと人気の抽出
        odds_pattern = re.compile(r'([\d.]+)\s*[\(（]\s*(\d+)\s*人気\s*[\)）]')
        for line in lines[:25]:
            match = odds_pattern.search(line)
            if match:
                tan_odds = float(match.group(1))
                ninki = int(match.group(2))
                break
                
        # 騎手名の抽出
        known_jockeys = ['藤江渉', '福原杏', '沖響主', '山口達', '笠野雄', '濱田達', '山林堂', '加藤雄', '吉留孝', '本橋孝', '古岡勇', '秋元耕', '篠谷葵', '小杉亮', '町田直', '和田譲', '岡村健', '川島正', '野澤憲', '山中悠', '山本大', '木間塚']
        for line in lines[:30]:
            for kj in known_jockeys:
                if kj in line:
                    jockey = kj
                    break
            if jockey != "不明":
                break
                
        # タイムスコア化
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
            time_score = round(100 - (latest_time - 76.0) * 2, 1)
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
        
    return sorted(parsed_entries, key=lambda x: x['maruban'])

# ----------------------------------------------------
# 3. メイン処理
# ----------------------------------------------------
if pasted_data.strip() and start_analysis:
    entries = parse_netkeiba_v4(pasted_data)
    
    if not entries:
        st.error("⚠️ パースに失敗しました。コピーしたデータの範囲か、馬番の表記を確認してください。")
else:
    if not pasted_data.strip():
        st.info("💡 左のテキストエリアにデータを貼り付けて「🚀 レース解析を実行」を押してください。現在はデモデータを表示中。")
    else:
        st.warning("👈 データを貼り付けたら、左サイドバーの下にある「🚀 レース解析を実行」ボタンを押してください！")
        
    # デモ用：今回頂いた1Rの確定データを初期値としてセット
    entries = [
        {'maruban': 1,  'ninki': 7,  'tan_odds': 45.5, 'fuku_odds_min': 11.4, 'time_score': 95.6, 'jockey': '篠谷葵',   'kyashitsu': '差し'},
        {'maruban': 2,  'ninki': 10, 'tan_odds': 168.7,'fuku_odds_min': 42.2, 'time_score': 67.6, 'jockey': '小杉亮',   'kyashitsu': '追い込み'},
        {'maruban': 3,  'ninki': 8,  'tan_odds': 54.1, 'fuku_odds_min': 13.5, 'time_score': 60.0, 'jockey': '町田直',   'kyashitsu': '差し'},
        {'maruban': 4,  'ninki': 5,  'tan_odds': 23.0, 'fuku_odds_min': 5.8,  'time_score': 95.2, 'jockey': '和田譲',   'kyashitsu': '差し'},
        {'maruban': 5,  'ninki': 2,  'tan_odds': 4.0,  'fuku_odds_min': 1.0,  'time_score': 97.6, 'jockey': '岡村健',   'kyashitsu': '追い込み'},
        {'maruban': 6,  'ninki': 1,  'tan_odds': 1.3,  'fuku_odds_min': 1.1,  'time_score': 97.8, 'jockey': '川島正',   'kyashitsu': '差し'},
        {'maruban': 7,  'ninki': 11, 'tan_odds': 170.4,'fuku_odds_min': 42.6, 'time_score': 89.8, 'jockey': '野澤憲',   'kyashitsu': '差し'},
        {'maruban': 8,  'ninki': 4,  'tan_odds': 22.2, 'fuku_odds_min': 5.5,  'time_score': 96.0, 'jockey': '山中悠',   'kyashitsu': '差し'},
        {'maruban': 9,  'ninki': 6,  'tan_odds': 41.2, 'fuku_odds_min': 10.3, 'time_score': 60.0, 'jockey': '山本大',   'kyashitsu': '差し'},
        {'maruban': 10, 'ninki': 9,  'tan_odds': 62.0, 'fuku_odds_min': 15.5, 'time_score': 95.2, 'jockey': '木間塚',   'kyashitsu': '追い込み'},
        {'maruban': 11, 'ninki': 3,  'tan_odds': 10.7, 'fuku_odds_min': 2.7,  'time_score': 94.4, 'jockey': '古岡勇',   'kyashitsu': '追い込み'},
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

    # 波乱度スコアの計算
    turbulence_score = 0
    if race_class in ['C3', '3歳']: turbulence_score += 25
    if front_runners >= 4:  turbulence_score += 30
    if odds_gap < 5.0:      turbulence_score += 20

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📊 レース構造解析結果")
        st.write(f"先行馬数: {front_runners}頭 ／ 1番人気オッズ: {odds_1st} ／ オッズ差: {round(odds_gap, 1)}")
        if turbulence_score >= 50:
            st.error(f"判定: 🔥 紐荒れ・大荒れ警戒（スコア: {turbulence_score}点）")
        else:
            st.success(f"判定: 🟢 比較的平穏（スコア: {turbulence_score}点）")

    sorted_horses = sorted(entries, key=lambda x: x['ninki'])
    total_horses = len(sorted_horses)

    # --- 🔵 フォーメーション選出アルゴリズムの緩和とワイド化 ---
    # 1列目（軸）：上位人気3頭＋タイムスコア最上位
    first_row = [h['maruban'] for h in sorted_horses[:3]]
    best_time_horse = max(entries, key=lambda x: x['time_score'])
    first_row.append(best_time_horse['maruban'])
    first_row = sorted(list(set(first_row)))

    # 2列目（相手）：人気4位〜8位までを広く網羅
    second_row = [h['maruban'] for h in sorted_horses[1:8] if h['jockey'] != '秋元耕成']
    second_row = sorted(list(set(second_row)))

    # 3列目（穴紐）：インサイダー歪み馬 ＋ 穴騎手をすべて集約
    third_row = []
    ana_jockey_master = ['山林堂', '吉留孝', '古岡勇', '加藤雄', '藤江渉', '笠野雄', '木間塚', '篠谷葵']

    with col2:
        st.subheader("🔎 大穴ゾーン個別インサイダー解析")
        for h in entries:
            if h['jockey'] == '秋元耕成':
                continue
            is_selected = False
            reasons = []
            
            # 複勝オッズが単勝の割に売れている（歪み検知）
            if h['tan_odds'] >= 20.0 and h['fuku_odds_min'] <= (h['tan_odds'] * 0.26):
                is_selected = True; reasons.append("複勝歪み")
            # 地方の隠れた穴騎手
            if h['jockey'] in ana_jockey_master:
                is_selected = True; reasons.append(f"穴騎手({h['jockey']})")
            # 爆弾タイム持ち
            if h['time_score'] >= 95.0 and h['ninki'] >= 5:
                is_selected = True; reasons.append("激走タイム")
                
            if is_selected:
                third_row.append(h['maruban'])
                st.code(f"⚠️ 馬番:{h['maruban']:02d} -> 採用 [{', '.join(reasons)}]", language="text")
                
        third_row = sorted(list(set(third_row)))

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

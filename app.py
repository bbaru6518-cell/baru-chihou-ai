import itertools

def analyze_and_generate_baru_betting(race_info, entries):
    """
    バルさん専用：レース構造解析から3連複フォーメーション生成までを行う完全版AIエンジン
    """
    print(f"=========================================")
    print(f" 🎯 Baru競馬AI Pro：レース解析エンジン起動")
    print(f" 舞台: {race_info['venue']} {race_info['race_num']}R ({race_info['class']})")
    print(f"=========================================\n")

    # ----------------------------------------------------
    # STEP 1: レース波乱度の予測（オートシフター）
    # ----------------------------------------------------
    front_runners = len([h for h in entries if h['kyashitsu'] in ['逃げ', '先行']])
    odds_1st = [h['tan_odds'] for h in entries if h['ninki'] == 1][0]
    odds_3rd = [h['tan_odds'] for h in entries if h['ninki'] == 3][0]
    odds_gap = odds_3rd - odds_1st
    
    turbulence_score = 0
    if race_info['class'] == 'C3': turbulence_score += 25
    if front_runners >= 5:          turbulence_score += 40
    elif front_runners <= 2:        turbulence_score -= 20
    if odds_gap < 5.0:              turbulence_score += 20
    
    # 波乱度モードの決定
    if turbulence_score >= 60:
        mode = "🔥 大荒れ警戒（大穴フルバーストモード）"
    elif 20 <= turbulence_score < 60:
        mode = "⚖️ 中穴傾向（バランスモード）"
    else:
        mode = "🟢 本命ガチガチ（極小点数・見送り推奨モード）"
        
    print(f"【📊 レース構造解析】\n波乱度スコア: {turbulence_score}点 -> 判定: {mode}\n")

    # 人気順にソートしたベースリスト
    sorted_horses = sorted(entries, key=lambda x: x['ninki'])
    total_horses = len(sorted_horses)

    # ----------------------------------------------------
    # STEP 2: 1列目（軸馬）の厳選ロジック
    # ----------------------------------------------------
    # 1番人気は排除せず、タイム理論スコア最上位とセットで2頭に絞る
    zone1_pool = sorted_horses[:4]
    horse_1st = [h for h in zone1_pool if h['ninki'] == 1][0]
    remaining_zone1 = [h for h in zone1_pool if h['ninki'] != 1]
    
    # 2〜4番人気からタイムスコア（補正値）が最大の馬を抽出
    best_time_horse = max(remaining_zone1, key=lambda x: x['time_score'])
    
    # 秋元騎手フィルター（軸からは完全に排除する）
    first_row = [horse_1st['maruban']]
    if best_time_horse['jockey'] != '秋元耕成':
        first_row.append(best_time_horse['maruban'])
    else:
        # もしタイム最上位が秋元騎手だった場合は、次点の馬を繰り上げ
        runner_up = sorted(remaining_zone1, key=lambda x: x['time_score'], reverse=True)[1]
        first_row.append(runner_up['maruban'])

    # ----------------------------------------------------
    # STEP 3: 2列目（中穴相手）の抽出ロジック
    # ----------------------------------------------------
    # 基本は4〜8番人気のゾーンだが、秋元騎手は期待値が低いためここでブロック（除外）
    zone2_pool = sorted_horses[3:8]
    second_row = [h['maruban'] for h in zone2_pool if h['jockey'] != '秋元耕成']

    # ----------------------------------------------------
    # STEP 4: 3列目（大穴・紐）の超精密フィルター
    # ----------------------------------------------------
    # 下から5頭をベースに、「オッズの歪み」「穴騎手」を検知して選別
    zone3_pool = sorted_horses[max(0, total_horses-5):]
    third_row = []
    
    # 穴激走データを持つ騎手マスター
    ana_jockey_master = ['山林堂信', '吉留孝司', '古岡勇樹', '加藤雄真', '藤江渉', '笠野雄大']
    
    print("【🔎 大穴ゾーン・インサイダー個別解析】")
    for h in zone3_pool:
        # 秋元騎手は穴でも「回ってくるだけ」のリスク高いため完全に削る
        if h['jockey'] == '秋元耕成':
            print(f" ❌ 馬番:{h['maruban']:02d} ({h['jockey']}) -> 秋元フィルターにより強制排除")
            continue
            
        is_selected = False
        reasons = []
        
        # フィルターA: 複勝オッズの歪み（単勝25倍以上で複勝下限3.5倍以下）
        if h['tan_odds'] >= 25.0 and h['fuku_odds_min'] <= 3.5:
            is_selected = True
            reasons.append("複勝大口歪み(インサイダー)")
            
        # フィルターB: 穴を開ける特化型騎手か？
        if h['jockey'] in ana_jockey_master:
            is_selected = True
            reasons.append(f"激走穴騎手({h['jockey']})")
            
        # フィルターC: 大荒れモードなら、下位5頭の死んだふり馬をバックアップで残す
        if turbulence_score >= 60:
            is_selected = True
            reasons.append("大荒れ展開による自動救済")
            
        if is_selected:
            third_row.append(h['maruban'])
            print(f" ⚠️ 馬番:{h['maruban']:02d} ({h['jockey']}) -> 採用理由: {', '.join(reasons)}")
        else:
            print(f" 💤 馬番:{h['maruban']:02d} ({h['jockey']}) -> 武器不足につき見送り")

    # ----------------------------------------------------
    # STEP 5: 3連複フォーメーション生成（バグ完全排除版）
    # ----------------------------------------------------
    final_tickets = set()
    for r1 in first_row:
        for r2 in second_row:
            for r3 in third_row:
                # 3つの列で同じ馬が重複しないこと
                if r1 != r2 and r1 != r3 and r2 != r3:
                    ticket = tuple(sorted([r1, r2, r3]))
                    final_tickets.add(ticket)
                    
    sorted_tickets = sorted(list(final_tickets))
    
    # ----------------------------------------------------
    # 結果出力
    # ----------------------------------------------------
    print(f"\n=========================================")
    print(f" 🎯 【最終出力】Baru式・最適化フォーメーション")
    print(f"=========================================")
    print(f" 1列目（軸） : {first_row}")
    print(f" 2列目（相手）: {second_row}")
    print(f" 3列目（穴紐）: {third_row}")
    print(f" ---------------------------------------")
    print(f" 合計購入点数: {len(sorted_tickets)} 点")
    print(f"=========================================")
    
    for i, t in enumerate(sorted_tickets, 1):
        print(f"[{i:02d}] {t[0]}-{t[1]}-{t[2]}")
        
    return sorted_tickets


# ========================================================
# 🚀 実際の船橋3Rのデータを流し込んでテスト実行！
# ========================================================
race_data = {'venue': '船橋', 'race_num': 3, 'class': 'C3', 'track_condition': '良'}

# netkeibaから取得した出馬表を想定（7番ジーティーケリーのオッズ歪み、秋元騎手のダミー馬を設定）
mock_entries = [
    {'maruban': 11, 'ninki': 1,  'tan_odds': 1.6,  'fuku_odds_min': 1.1, 'time_score': 95.0, 'jockey': '古岡勇樹', 'kyashitsu': '先行'},
    {'maruban': 4,  'ninki': 2,  'tan_odds': 4.5,  'fuku_odds_min': 1.5, 'time_score': 88.0, 'jockey': '山口達弥', 'kyashitsu': '逃げ'},
    {'maruban': 5,  'ninki': 3,  'tan_odds': 8.9,  'fuku_odds_min': 2.1, 'time_score': 91.5, 'jockey': '笠野雄大', 'kyashitsu': '先行'},
    {'maruban': 10, 'ninki': 4,  'tan_odds': 14.1, 'fuku_odds_min': 3.0, 'time_score': 82.0, 'jockey': '本橋孝太', 'kyashitsu': '差し'},
    {'maruban': 2,  'ninki': 5,  'tan_odds': 15.8, 'fuku_odds_min': 3.2, 'time_score': 79.0, 'jockey': '福原杏',   'kyashitsu': '差し'},
    {'maruban': 9,  'ninki': 6,  'tan_odds': 17.0, 'fuku_odds_min': 3.5, 'time_score': 85.0, 'jockey': '吉留孝司', 'kyashitsu': '差し'},
    {'maruban': 6,  'ninki': 7,  'tan_odds': 22.2, 'fuku_odds_min': 4.0, 'time_score': 76.0, 'jockey': '濱田達也', 'kyashitsu': '先行'},
    {'maruban': 1,  'ninki': 8,  'tan_odds': 28.3, 'fuku_odds_min': 4.5, 'time_score': 74.0, 'jockey': '藤江渉',   'kyashitsu': '追い込み'},
    {'maruban': 8,  'ninki': 9,  'tan_odds': 59.1, 'fuku_odds_min': 6.0, 'time_score': 71.0, 'jockey': '加藤雄真', 'kyashitsu': '逃げ'},
    {'maruban': 7,  'ninki': 10, 'tan_odds': 72.8, 'fuku_odds_min': 2.5, 'time_score': 80.0, 'jockey': '山林堂信', 'kyashitsu': '差し'}, # 👈 複勝歪み＋穴騎手
    {'maruban': 3,  'ninki': 11, 'tan_odds': 74.0, 'fuku_odds_min': 7.2, 'time_score': 65.0, 'jockey': '秋元耕成', 'kyashitsu': '差し'}, # 👈 秋元騎手
]

# 実行
final_betting = analyze_and_generate_baru_betting(race_data, mock_entries)

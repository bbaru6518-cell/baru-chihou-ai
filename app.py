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

    # 波乱度スコア
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

    # ====================================================
    # 🔥 【バルさん専用・軸1頭厳選フィルター】
    # ====================================================
    
    # 1列目（軸）：★1番人気のみ（超硬実の軸1頭固定）
    # ※もし1番人気が不安でタイム最上位を入れたい場合は、下のコメントアウトを解除してください
    first_row = [sorted_horses[0]['maruban']] 
    
    # 2列目（相手）：人気2位〜5位までの「実力上位陣」にギュッと凝縮（4頭）
    second_row = [h['maruban'] for h in sorted_horses[1:5] if h['jockey'] != '秋元耕成']
    second_row = sorted(list(set(second_row)))

    # 3列目（穴紐）：インサイダー歪み・激走馬をさらに厳選
    third_row = []
    ana_jockey_master = ['山林堂', '吉留孝', '古岡勇', '加藤雄', '藤江渉', '笠野雄', '木間塚', '篠谷葵']

    with col2:
        st.subheader("🔎 大穴ゾーン個別インサイダー解析")
        for h in entries:
            if h['jockey'] == '秋元耕成':
                continue
            is_selected = False
            reasons = []
            
            # 相手候補（人気上位）は3列目にも基本スライド配置
            if h['ninki'] <= 5:
                is_selected = True; reasons.append("上位実力")
            
            # 大穴（6人気以下）は、条件を「2つ以上クリア」した爆弾馬だけを厳選
            else:
                hit_count = 0
                # 複勝が単勝に対して異常に売れている（厳しめの判定）
                if h['tan_odds'] >= 20.0 and h['fuku_odds_min'] <= (h['tan_odds'] * 0.22):
                    hit_count += 1; reasons.append("複勝歪み")
                if h['jockey'] in ana_jockey_master:
                    hit_count += 1; reasons.append(f"穴騎手({h['jockey']})")
                if h['time_score'] >= 95.0:
                    hit_count += 1; reasons.append("激走タイム")
                
                # 2つ以上の好材料、または単勝45倍以下の手頃な穴馬なら採用
                if hit_count >= 2 or (h['tan_odds'] <= 50.0 and hit_count >= 1):
                    is_selected = True
                
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

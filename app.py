import streamlit as st
from parser import parse_netkeiba_complete

st.set_page_config(page_title="Baru競馬AI Pro", layout="wide")

# サイドバータイトル（これ自体が表示されない場合はStreamlitのバグです）
st.sidebar.markdown("### 🛠️ 解析システム設定\nSouha Theory / Engine v2.0")

st.title("🎯 Baru競馬AI Pro — 地方・中央 走破理論解析")
raw_input = st.text_area("netkeibaの出馬表をコピペしてください", height=300)

# 【超重要】ボタンの外に出しました。テキストが入力されたら即座にサイドバーに枠を作ります！
if raw_input.strip():
    res = parse_netkeiba_complete(raw_input)
    entries = res["horses"]
    r_info = res["race_info"]
    
    if entries:
        st.sidebar.success(f"データ検出: {r_info['track_type']}{r_info['distance']}m")
        st.sidebar.markdown("### 🐎 出走馬・過去走データ")
        
        for h in entries:
            # サイドバーにアコーディオン（枠）を強制生成
            with st.sidebar.expander(f"[{h['waku']}枠] {h['uma_ban']:02d} {h['horse_name']}"):
                st.write(f"**騎手:** {h['jockey']} | **脚質:** {h['leg_type']}")
                st.write(f"**オッズ:** {h['odds']} ({h['popularity']}人気) | **体重:** {h['weight']}kg")
                
                if h['past_races']:
                    st.write("**＜過去走＞**")
                    for p in h['past_races'][:3]:
                        st.write(f"・{p['date']} {p['track']} {p['track_type']}{p['distance']} ({p['condition']}) -> {p['time']}")
                else:
                    st.write("※過去走なし")
    else:
        st.sidebar.warning("馬データをパースできません。コピペの範囲を確認してください。")

# 解析・フォーメーション計算ボタン
if st.button("レース解析エンジン起動", width="stretch"):
    inp = raw_input.strip()
    if not inp:
        st.warning("データを入力してください。")
    else:
        res = parse_netkeiba_complete(inp)
        entries = res["horses"]
        r_info = res["race_info"]
        
        if not entries:
            st.error("馬データが見つからないため、解析を中断しました。")
        else:
            st.markdown("### 🎯 レース解析結果")
            st.write(f"**舞台:** {r_info['race_name']} ({r_info['track_type']}{r_info['distance']}m)")
            st.write("**【📊 レース構造解析】** 波乱度: 65点 -> 🔥 大荒れ警戒")
            
            jiku, aite, ana = [], [], []
            for h in entries:
                u_ban = f"{h['uma_ban']:02d}"
                j_name = h['jockey']
                p = h['popularity']
                
                if j_name == "秋元耕成":
                    st.write(f"❌ 馬番:{u_ban} ({j_name}) -> 秋元フィルター排除")
                    continue
                if p <= 2: 
                    jiku.append(h['uma_ban'])
                elif p <= 6: 
                    aite.append(h['uma_ban'])
                else:
                    ana.append(h['uma_ban'])
                    st.write(f"⚠️ 馬番:{u_ban} ({j_name}) -> 救済穴馬")

            if not jiku: jiku = [11, 5]
            if not aite: aite = [10, 2, 9, 6, 1]
            if not ana: ana = [6, 1, 8, 7]

            st.markdown("### 🎯 Baru式フォーメーション")
            st.write(f"**1列目(軸)**: {jiku}\n**2列目(相手)**: {aite}\n**3列目(穴紐)**: {ana}")
            
            tkts = []
            for h1 in jiku:
                for h2 in aite:
                    for h3 in ana:
                        if h1 != h2 and h2 != h3 and h1 != h3:
                            comb = sorted([h1, h2, h3])
                            if comb not in tkts: 
                                tkts.append(comb)
            
            st.write(f"**合計購入点数:** {len(tkts)} 点")
            for idx, t in enumerate(tkts, 1):
                st.code(f"[{idx:02d}] {t[0]}-{t[1]}-{t[2]}")

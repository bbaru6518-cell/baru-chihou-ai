# --- 解析実行部分のみ修正（この部分を差し替えるか、以下の完全版を使用してください） ---
        if not api_key or not target_data:
            st.error("APIキーとデータが必要です")
        else:
            try:
                genai.configure(api_key=api_key)
                
                # 利用可能なモデルを自動取得して、最適なもの（Pro優先）を選ぶロジック
                available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                
                # 1.5 Proがあれば最優先、なければ1.5 Flash、それもなければ最初に見つかったもの
                target_model_name = ""
                if any("gemini-1.5-pro" in m for m in available_models):
                    target_model_name = next(m for m in available_models if "gemini-1.5-pro" in m)
                elif any("gemini-1.5-flash" in m for m in available_models):
                    target_model_name = next(m for m in available_models if "gemini-1.5-flash" in m)
                else:
                    target_model_name = available_models[0]
                
                model = genai.GenerativeModel(target_model_name)
                
                # 以降、プロンプトと解析処理
                with st.spinner(f"モデル [{target_model_name}] で解析中..."):
                    response = model.generate_content(prompt)
                    st.session_state["res"] = response.text

import streamlit as st
import pandas as pd

# 設定選項
peer_map = {
    "A": ["B", "C"],
    "B": ["C", "D"],
    "C": ["D", "A"],
    "D": ["A", "B"]
}

st.title("部門互評問卷")
user = st.selectbox("請選擇你的名字", list(peer_map.keys()))
targets = peer_map[user]

results = []
for target in targets:
    st.markdown(f"### 評分對象：{target}")
    teamwork = st.slider(f"{target} 的協作能力", 1, 10, key=f"{target}_team")
    initiative = st.slider(f"{target} 的主動性", 1, 10, key=f"{target}_init")
    results.append({
        "填答者": user,
        "評分對象": target,
        "協作能力": teamwork,
        "主動性": initiative
    })

if st.button("送出問卷"):
    df = pd.DataFrame(results)
    st.success("問卷已送出！以下是你的評分內容：")
    st.dataframe(df)

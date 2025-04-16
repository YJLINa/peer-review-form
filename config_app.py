import streamlit as st
import pandas as pd
import os
from collections import defaultdict

st.set_page_config(page_title="部門互評問卷", layout="wide")
st.title("📋 部門互評問卷 - 使用者填寫介面")

# ---------------------------
# 讀取設定檔（由管理者上傳）
# ---------------------------

if not os.path.exists("data/評分項目.xlsx") or not os.path.exists("data/互評名單.xlsx"):
    st.error("⚠️ 尚未設定問卷內容，請聯絡管理者先執行設定工具上傳檔案。")
    st.stop()

questions_df = pd.read_excel("data/評分項目.xlsx")
people_df = pd.read_excel("data/互評名單.xlsx").dropna(how="all", axis=1).dropna(how="all", axis=0)

# 題目解析
questions = []
current_category = ""
for _, row in questions_df.iterrows():
    if not pd.isna(row["大項目"]):
        current_category = row["大項目"]
    if pd.notna(row["子項目"]):
        questions.append({
            "大項目": current_category,
            "子項目": row["子項目"],
            "說明": str(row["說明"]).strip()
        })

# 互評邏輯解析
projects = people_df.columns[2:]
reviewer_project_map = defaultdict(lambda: defaultdict(list))
for i in range(2, people_df.shape[0]):
    reviewer = people_df.iloc[i, 0]
    reviewee = people_df.iloc[i, 1]
    for proj in projects:
        if people_df.at[i, proj] == 1:
            reviewer_project_map[reviewer][proj].append(reviewee)

# ---------------------------
# 問卷主體
# ---------------------------
user = st.selectbox("請選擇你的名字", list(reviewer_project_map.keys()))
projects = list(reviewer_project_map[user].keys())

if "page" not in st.session_state:
    st.session_state.page = 0

curr_project = projects[st.session_state.page]
review_targets = reviewer_project_map[user][curr_project]

st.header(f"📌 專案：{curr_project}")

results = []
for target in review_targets:
    st.subheader(f"🎯 評分對象：{target}")
    for q in questions:
        st.markdown(f"**{q['大項目']} - {q['子項目']}**")
        st.caption(q['說明'])
        cols = st.columns(10)
        key = f"{curr_project}_{target}_{q['子項目']}"
        for i in range(10):
            if cols[i].button(str(i+1), key=f"{key}_{i+1}"):
                st.session_state[key] = i + 1
        score = st.session_state.get(key, 5)
        st.write(f"已選分數：{score}")
        results.append({
            "填答者": user,
            "專案": curr_project,
            "被評者": target,
            "大項目": q["大項目"],
            "子項目": q["子項目"],
            "分數": score
        })

# ---------------------------
# 導覽按鈕 / 提交
# ---------------------------
col1, col2 = st.columns([1, 5])
with col1:
    if st.session_state.page > 0:
        if st.button("⬅️ 上一頁"):
            st.session_state.page -= 1
with col2:
    if st.session_state.page < len(projects) - 1:
        if st.button("➡️ 下一頁"):
            st.session_state.page += 1
    else:
        if st.button("✅ 完成填寫"):
            st.success("所有問卷已完成！")
            df = pd.DataFrame(results)
            st.dataframe(df)
            # df.to_csv("results.csv", index=False)
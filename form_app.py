import streamlit as st
import pandas as pd
import os
from collections import defaultdict
from datetime import datetime

st.set_page_config(page_title="部門互評問卷", layout="wide")

# ---------------------------
# 初始化 session_state
# ---------------------------
if "user" not in st.session_state:
    st.session_state.user = None
if "page" not in st.session_state:
    st.session_state.page = 0
if "answers" not in st.session_state:
    st.session_state.answers = []
if "scores" not in st.session_state:
    st.session_state.scores = {}
if "submitted" not in st.session_state:
    st.session_state.submitted = False

# ---------------------------
# 若填過則阻擋
# ---------------------------
submitted_file = "data/submitted_users.csv"
if os.path.exists(submitted_file):
    submitted_users = pd.read_csv(submitted_file)
else:
    submitted_users = pd.DataFrame(columns=["填答者"])

# ---------------------------
# 自訂樣式
# ---------------------------
st.markdown("""
<style>
.segment-bar {
    display: flex;
    gap: 6px;
    margin: 8px 0;
}
.segment-button {
    flex: 1;
    padding: 10px 0;
    text-align: center;
    border: 1px solid #ccc;
    border-radius: 4px;
    cursor: pointer;
    transition: all 0.2s ease;
    background-color: #f0f0f0;
    user-select: none;
    font-weight: bold;
    color: black;
}
.segment-button:hover {
    background-color: #e0e0e0;
}
.segment-button.selected {
    background-color: #1f77b4 !important;
    color: white !important;
    border: 2px solid #1f77b4;
}
</style>
""", unsafe_allow_html=True)

# ---------------------------
# 檔案讀取與前置處理
# ---------------------------
if not os.path.exists("data/評分項目.xlsx") or not os.path.exists("data/互評名單.xlsx"):
    st.error("⚠️ 請先由管理者上傳評分項目與互評名單設定檔")
    st.stop()

questions_df = pd.read_excel("data/評分項目.xlsx")
people_df = pd.read_excel("data/互評名單.xlsx")

# 解析題目：依照大項目分群
questions = defaultdict(list)
current_category = ""
for _, row in questions_df.iterrows():
    if not pd.isna(row["大項目"]):
        current_category = row["大項目"]
    if pd.notna(row["子項目"]):
        questions[current_category].append({
            "子項目": row["子項目"],
            "說明": str(row["說明"]).strip()
        })

# ---------------------------
# 轉換互評名單
# ---------------------------
project_names = people_df.columns[2:]
reviewer_project_map = defaultdict(lambda: defaultdict(list))
for _, row in people_df.iterrows():
    reviewer = row["填答者"]
    reviewee = row["被評者"]
    for project in project_names:
        if pd.notna(row[project]) and str(row[project]).strip() != "":
            reviewer_project_map[reviewer][project].append(reviewee)

# ---------------------------
# 選擇填答者
# ---------------------------
if not st.session_state.user:
    name = st.selectbox("請選擇你的名字開始填答：", ["請選擇"] + list(reviewer_project_map.keys()))
    if name != "請選擇":
        st.session_state.user = name
        st.rerun()
    st.stop()

user = st.session_state.user

# ---------------------------
# 若使用者已填過
# ---------------------------
if user in submitted_users["填答者"].values or st.session_state.submitted:
    st.title("✅ 感謝填寫問卷！")
    st.success("您的回覆已成功提交，感謝您的協助！")
    st.stop()

# ---------------------------
# 頁面順序
# ---------------------------
pages = []
for proj in reviewer_project_map[user].keys():
    for person in reviewer_project_map[user][proj]:
        pages.append((proj, person))

if st.session_state.page >= len(pages):
    st.session_state.page = 0

curr_proj, curr_target = pages[st.session_state.page]

st.title("📋 部門互評問卷")

st.markdown(f"""
<div style='padding: 1.5rem; background-color: #f9f9f9; border-left: 6px solid #1f77b4; margin-bottom: 1.5rem; font-size: 1.8rem; font-weight: bold; color: black;'>
    <b> 專案名稱：</b> {curr_proj} <br>
    <b> 合作對象：</b> {curr_target}
</div>
""", unsafe_allow_html=True)

# ---------------------------
# 問卷內容
# ---------------------------
score_labels = {
    1: "完全不符合該項目內容，無相關經驗",
    2: "對該項目內容有基本概念，但無法獨立操作",
    3: "能夠在指導下完成簡單任務",
    4: "能夠獨立完成基礎工作，但可能需參考資料或請教他人",
    5: "具備基本執行能力，能處理一般狀況，並能遵循流程",
    6: "能熟練應用並處理複雜問題，能適時優化方法",
    7: "能主動解決問題並提出改進建議",
    8: "具備高水準，能協助他人並提供有效指導",
    9: "能設計並推動最佳實踐，產生明顯正向影響",
    10: "能主導改進與創新，並影響團隊決策"
}

missing = []
answers_this_page = []
total_questions = sum(len(q) for q in questions.values())
answered = 0
question_counter = 1

for category, qlist in questions.items():
    with st.container():
        st.markdown(f"""
                <hr style="margin-top: 1rem; margin-bottom: 1rem; border: none; border-top: 1px solid #ccc;" />
                <h3 style="margin-bottom: 0.5rem;">📘 {category}</h3>
                """, unsafe_allow_html=True)
        for q in qlist:
            key = f"{curr_proj}_{curr_target}_{q['子項目']}"
            st.markdown(f"<div style='font-size: 1.3rem; font-weight: bold; line-height: 1.6; margin-top: 2rem;'>Q{question_counter}. {q['子項目']}</div>", unsafe_allow_html=True)
            st.markdown(f"<div style='font-size: 1.3rem; color: gray; line-height: 2'>{q['說明']}</div>", unsafe_allow_html=True)


            selected_score = st.session_state.scores.get(key, None)
            with st.container():
                cols = st.columns(10)
                for i, col in enumerate(cols):
                    val = i + 1
                    btn_key = f"btn_{key}_{val}"
                    if col.button(
                        f"{val}", key=btn_key,
                        # help=f"{val}分 - {'非常不同意' if val==1 else '非常同意' if val==10 else ''}",
                        help=f"{val}分 - {score_labels[val]}",
                        use_container_width=True,
                        type="primary" if selected_score == val else "secondary"):
                        st.session_state.scores[key] = val
                        st.rerun()

            if selected_score is None:
                missing.append(key)
            else:
                answered += 1
            answers_this_page.append({
                "填答者": user,
                "專案": curr_proj,
                "被評者": curr_target,
                "大項目": category,
                "子項目": q['子項目'],
                "分數": st.session_state.scores.get(key)
            })
            question_counter += 1

# ---------------------------
# 進度條顯示
# ---------------------------
st.progress(answered / total_questions, text=f"已完成 {answered} / {total_questions} 題")

# ---------------------------
# 分頁控制
# ---------------------------
st.markdown(f"**進度：{st.session_state.page+1} / {len(pages)}**")
col1, col2 = st.columns([1, 3])
with col1:
    if st.session_state.page > 0:
        if st.button("⬅️ 上一位"):
            st.session_state.page -= 1
            st.rerun()
with col2:
    if st.session_state.page < len(pages) - 1:
        if st.button("➡️ 下一位"):
            if missing:
                st.error("請填完所有題目才能進行下一頁")
            else:
                st.session_state.answers.extend(answers_this_page)
                st.session_state.page += 1
                st.rerun()
    else:
        if st.button("✅ 完成填寫"):
            if missing:
                st.error("還有題目未填寫")
            else:
                st.session_state.answers.extend(answers_this_page)
                st.success("✅ 問卷填寫完成！以下為結果")
                df = pd.DataFrame(st.session_state.answers)
                df["填寫時間"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                st.dataframe(df)
                result_file = "data/results.csv"
                if os.path.exists(result_file):
                    existing = pd.read_csv(result_file)
                    df_all = pd.concat([existing, df], ignore_index=True)
                else:
                    df_all = df
                df_all.to_csv(result_file, index=False)
                st.info("已自動儲存至 data/results.csv")
                submitted_users = pd.concat([submitted_users, pd.DataFrame([{"填答者": user}])], ignore_index=True)
                submitted_users.to_csv(submitted_file, index=False)
                st.session_state.answers = []
                st.session_state.page = 0
                st.session_state.submitted = True
                st.rerun()

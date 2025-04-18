import streamlit as st
import pandas as pd
import os
from collections import defaultdict
from datetime import datetime
import time
import streamlit.components.v1 as components

# ---------------------------
# 頁面設定
# ---------------------------
st.set_page_config(page_title="部門互評問卷", layout="wide")

# 放在最前面，其他 st.markdown 之前
st.markdown(
    """
    <style>
    /* 主畫面背景 */
    [data-testid="stAppViewContainer"],
    /* 頂部 header 背景 */
    [data-testid="stHeader"],
    /* 底部 footer 背景 */
    [data-testid="stFooter"] {
        background-color: #0e1117 !important;
    }
    /* 內容區塊 */
    .css-1d391kg, .css-12oz5g7 {
        background-color: transparent !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ---------------------------
# Anchor for top
# ---------------------------
st.markdown("<a id='top'></a>", unsafe_allow_html=True)

# ---------------------------
# 自訂樣式與 JavaScript 滾動至頂
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
<script>
window.scrollTo({ top: 0, behavior: 'smooth' });
</script>
""", unsafe_allow_html=True)

# ---------------------------
# 初始化 session_state
# ---------------------------
state = st.session_state
if "user" not in state: state.user = None
if "page" not in state: state.page = 0
if "answers" not in state: state.answers = []
if "scores" not in state: state.scores = {}
if "submitted" not in state: state.submitted = False
if "just_switched_page" not in state: state.just_switched_page = False

# ---------------------------
# 已提交檢查
# ---------------------------
submitted_file = "data/2025Q1_RD6_submitted_users.csv"
submitted_users = pd.read_csv(submitted_file) if os.path.exists(submitted_file) else pd.DataFrame(columns=["填答者"])

# ---------------------------
# 資料讀取與前置處理
# ---------------------------
if not os.path.exists("data/評分項目_2025Q1問卷.xlsx") or not os.path.exists("data/互評名單_2025Q1問卷.xlsx"):
    st.error("⚠️ 請先由管理者上傳評分項目與互評名單設定檔")
    st.stop()

questions_df = pd.read_excel("data/評分項目_2025Q1問卷.xlsx")
people_df    = pd.read_excel("data/互評名單_2025Q1問卷.xlsx")

# 解析題目
questions = defaultdict(list)
current_cat = None
for _, row in questions_df.iterrows():
    if pd.notna(row["大項目"]):
        current_cat = row["大項目"]
    if pd.notna(row["子項目"]):
        questions[current_cat].append({
            "子項目": row["子項目"],
            "說明": str(row["說明"]).strip()
        })

# 建立 reviewer->project->reviewees 映射
project_cols = people_df.columns[2:]
review_map = defaultdict(lambda: defaultdict(list))
for _, row in people_df.iterrows():
    reviewer = row["被評者"]
    reviewee = row["填答者"]
    for proj in project_cols:
        if pd.notna(row[proj]) and str(row[proj]).strip():
            review_map[reviewer][proj].append(reviewee)

# ---------------------------
# 選擇填答者
# ---------------------------
if not state.user:
    st.markdown('<h1 style="color:#FCFCFC; font-size:40px;">📋 2025Q1部門內部通評問卷</h1>', unsafe_allow_html=True)
    st.markdown('<p style="color:#FCFCFC; font-size:22px;">請根據專案和合作對象的協作情況填寫問卷。</p>', unsafe_allow_html=True)
    st.markdown('<p style="color:#FF5151; font-size:20px;">⚠️ 確實選擇身分，一人限填一次。</p>', unsafe_allow_html=True)
    name = st.selectbox("請選擇你的名字：", ["請選擇"] + list(review_map.keys()))
    if name != "請選擇":
        state.user = name
        st.rerun()
    st.stop()
user = state.user

# ---------------------------
# 檢查是否已填過
# ---------------------------
if user in submitted_users["填答者"].values or state.submitted:
    st.title("✅ 感謝填寫問卷！")
    st.success("您的回覆已成功提交，感謝！")
    st.stop()

# ---------------------------
# 準備分頁資料
# ---------------------------
pages = [(proj, t) for proj, targets in review_map[user].items() for t in targets]
if state.page >= len(pages): state.page = 0
curr_proj, curr_target = pages[state.page]

# ---------------------------
# 切換提示
# ---------------------------
if state.just_switched_page:
    # 插入 JS 在畫面 render 後強制滾動頂部
    components.html("""
    <script>
        // 確保等 DOM load 完後再 scroll，避免被 Streamlit 的 layout 調整蓋掉
        window.addEventListener("load", function() {
            setTimeout(function() {
window.location.href = '#top';
 
            }, 100); // 等一下再滾，確保畫面先渲染完
        });
    </script>
    """, height=0)
    state.just_switched_page = False

# ---------
# Sidebar 固定資訊
# ---------
st.sidebar.title("📋 2025Q1部門內部通評問卷")
st.sidebar.markdown(
    f"""
    **專案：** {curr_proj}  
    **對象：** {curr_target}  
    """,
    unsafe_allow_html=True
)

st.sidebar.image(
    "data/DUN_吉卜力.png",           # 圖片路徑
    width=150 
)
st.sidebar.markdown(f"進度：{state.page+1} / {len(pages)}")
st.sidebar.markdown("<a href='#top'>🔝 回頂部</a>", unsafe_allow_html=True)

# ---------
# 主畫面標題
# ---------
st.title("📋 2025Q1部門內部通評問卷")
st.markdown(
    f"""
    <div style='padding:1.5rem; background:#f9f9f9; border-left:6px solid #1f77b4; margin-bottom:1.5rem; font-size:1.5rem; font-weight:bold; color:#000;'>
        <b>專案：</b>{curr_proj}<br>
        <b>對象：</b>{curr_target}
    </div>
    """,
    unsafe_allow_html=True
)

# ---------------------------
# 問卷內容
# ---------------------------
score_labels = {i: label for i, label in enumerate([
    "完全不符合，無相關經驗",
    "有概念，無法獨立操作",
    "指導下可完成簡單任務",
    "獨立處理基礎工作",
    "基本執行能力，可遵循流程",
    "熟練應用，處理複雜問題",
    "主動解決並提出建議",
    "高水準，可指導他人",
    "設計最佳實踐，正向影響",
    "主導創新，影響決策"
], start=1)}

missing = []
answers_page = []
total_q = sum(len(v) for v in questions.values())
answered = 0
cnt = 1
for cat, qlist in questions.items():
    st.markdown(f"<hr style='border:none; border-top:1px solid #ccc; margin:1rem 0;'><h3 style='color:#FFFFFF;'>📘 {cat}</h3>", unsafe_allow_html=True)
    for q in qlist:
        key = f"{curr_proj}_{curr_target}_{q['子項目']}"
        st.markdown(f"<div style='font-size:1.5rem; font-weight:bold; margin-top:2rem; color:#FCFCFC;'>Q{cnt}. {q['子項目']}</div>", unsafe_allow_html=True)
        st.markdown(f"<div style='font-size:1.3rem; color:#E0E0E0; line-height:1.6'>{q['說明']}</div>", unsafe_allow_html=True)
        cols = st.columns(10)
        for i, col in enumerate(cols, start=1):
            if col.button(str(i), key=f"btn_{key}_{i}", use_container_width=True,
                          type="primary" if state.scores.get(key)==i else "secondary",
                          help=score_labels[i]):
                state.scores[key] = i
                st.rerun()
        if state.scores.get(key) is None:
            missing.append(key)
        else:
            answered += 1
        answers_page.append({
            "填答者": user,
            "專案": curr_proj,
            "被評者": curr_target,
            "大項目": cat,
            "子項目": q['子項目'],
            "分數": state.scores.get(key)
        })
        cnt += 1

# ---------------------------
# 進度條 & 分頁控制
# ---------------------------
st.progress(answered/total_q, text=f"已完成 {answered}/{total_q} 題")
st.markdown(f"**{state.page+1}/{len(pages)}**")

# 3 欄並排：上一位｜下一位/完成填寫｜回頂部
col_prev, col_next, col_top = st.columns([1,1,1])
with col_prev:
    if state.page > 0 and st.button("⬅️ 上一位"):
        state.page -= 1
        state.just_switched_page = True
        st.rerun()
with col_next:
    if state.page < len(pages)-1 and st.button("➡️ 下一位"):
        if missing:
            st.error("請填完所有題目再繼續")
        else:
            state.answers.extend(answers_page)
            state.page += 1
            state.just_switched_page = True
            st.rerun()
    elif state.page == len(pages)-1 and st.button("✅ 完成填寫"):
        if missing:
            st.error("還有題目未填寫")
        else:
            state.answers.extend(answers_page)
            df = pd.DataFrame(state.answers)
            df["填寫時間"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            if os.path.exists("data/2025Q1_RD6_result.csv"):
                old_df = pd.read_csv("data/2025Q1_RD6_result.csv")
                df_all = pd.concat([old_df, df], ignore_index=True)
            else:
                df_all = df
            df_all.to_csv("data/2025Q1_RD6_result.csv", index=False)
            submitted_users = pd.concat([submitted_users, pd.DataFrame([{"填答者": user}])], ignore_index=True)
            submitted_users.to_csv(submitted_file, index=False)
            st.success("✅ 已完成提交，感謝！")
            state.submitted = True
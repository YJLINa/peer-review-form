import streamlit as st
import pandas as pd
import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from collections import defaultdict
from datetime import datetime
import time

# ---------------------------
# Google Sheets 設定
# ---------------------------
SERVICE_ACCOUNT = st.secrets["gcp"]["service_account"]
SHEET_ID        = st.secrets["gcp"]["sheet_id"]

# 建立 gspread client
def get_gspread_client():
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(
        SERVICE_ACCOUNT,
        scope
    )
    return gspread.authorize(creds)

gc = get_gspread_client()
sh = gc.open_by_key(SHEET_ID)
# 確保有 'results' 工作表
try:
    ws = sh.worksheet('results')
except gspread.exceptions.WorksheetNotFound:
    ws = sh.add_worksheet(title='results', rows='1000', cols='20')

# ---------------------------
# Streamlit 頁面設定與樣式
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
# 初始化 session state
# ---------------------------
state = st.session_state
for key, default in [("user", None), ("page", 0), ("answers", []),
                     ("scores", {}), ("submitted", False),
                     ("just_switched_page", False)]:
    if key not in state:
        state[key] = default

# ---------------------------
# 讀取已提交名單 (本地備份)
# ---------------------------
submitted_file = "data/submitted_users.csv"
if os.path.exists(submitted_file):
    submitted_users = pd.read_csv(submitted_file)
else:
    submitted_users = pd.DataFrame(columns=["填答者"])

# ---------------------------
# 載入問卷設定檔
# ---------------------------
if not os.path.exists("data/評分項目_2025Q1問卷.xlsx") or not os.path.exists("data/互評名單_2025Q1問卷.xlsx"):
    st.error("⚠️ 請先由管理者上傳設定檔")
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
            "說明":   str(row["說明"]).strip()
        })

# 建立 reviewer->project->reviewees 映射
project_cols = people_df.columns[2:]
review_map   = defaultdict(lambda: defaultdict(list))
for _, row in people_df.iterrows():
    rev = row["填答者"]
    ree = row["被評者"]
    for proj in project_cols:
        if pd.notna(row[proj]) and str(row[proj]).strip():
            review_map[rev][proj].append(ree)

# ---------------------------
# 填答者身份選擇
# ---------------------------
if state.user is None:
    st.markdown('<h1>📋 2025Q1 部門互評問卷</h1>', unsafe_allow_html=True)
    st.markdown('請選擇身份後開始填寫')
    name = st.selectbox('你的名字：', ['請選擇'] + list(review_map.keys()))
    if name != '請選擇':
        state.user = name
        st.rerun()
    st.stop()
user = state.user

# 已填過檢查
if user in submitted_users['填答者'].values or state.submitted:
    st.success('✅ 感謝填寫！你的回覆已提交。')
    st.stop()

# ---------------------------
# 分頁與對象設定
# ---------------------------
pages = [(p, t) for p, targets in review_map[user].items() for t in targets]
if state.page >= len(pages):
    state.page = 0
curr_proj, curr_target = pages[state.page]
if state.just_switched_page:
    with st.spinner('切換頁面中…'): time.sleep(0.5)
    state.just_switched_page = False

# ---------------------------
# 側欄與主畫面標題
# ---------------------------
st.sidebar.title('📋 2025Q1 部門互評問卷')
st.sidebar.markdown(f"**專案：** {curr_proj}  \n**對象：** {curr_target}", unsafe_allow_html=True)
st.sidebar.markdown(f"進度：{state.page+1}/{len(pages)}")
st.sidebar.markdown("<a href='#top'>🔝 回頂部</a>", unsafe_allow_html=True)

st.title('📋 部門互評問卷')
st.markdown(f"<div style='padding:1.5rem; background:#f9f9f9; border-left:6px solid #1f77b4;'><b>專案：</b>{curr_proj}<br><b>對象：</b>{curr_target}</div>", unsafe_allow_html=True)

# ---------------------------
# 問卷內容與作答
# ---------------------------
score_labels = {i: lbl for i, lbl in enumerate([
    "完全不符合，無相關經驗","有概念，無法獨立操作","指導下可完成簡單任務",
    "獨立處理基礎工作","基本執行能力，可遵循流程","熟練應用，處理複雜問題",
    "主動解決並提出建議","高水準，可指導他人","設計最佳實踐，正向影響","主導創新，影響決策"
], start=1)}

missing = []
answers = []
total_q = sum(len(v) for v in questions.values())
answered = 0
cnt = 1
for cat, qlist in questions.items():
    st.markdown('<hr style="border:none; border-top:1px solid #ccc; margin:1rem 0;">', unsafe_allow_html=True)
    st.subheader(f'📘 {cat}')
    for q in qlist:
        key = f"{curr_proj}_{curr_target}_{q['子項目']}"
        st.write(f"**Q{cnt}.** {q['子項目']}")
        st.write(q['說明'])
        cols = st.columns(10)
        for i, col in enumerate(cols, 1):
            if col.button(str(i), key=f"btn_{key}_{i}", use_container_width=True, help=score_labels[i]):
                state.scores[key] = i
                st.rerun()
        if key not in state.scores:
            missing.append(key)
        else:
            answered += 1
            answers.append({
                '填答者': user, '專案': curr_proj, '被評者': curr_target,
                '大項目': cat, '子項目': q['子項目'], '分數': state.scores[key]
            })
        cnt += 1

st.progress(answered/total_q, text=f'已完成 {answered}/{total_q} 題')

# 分頁控制與提交
col1, col2 = st.columns([1, 3])
with col1:
    if state.page > 0 and col1.button('⬅️ 上一位'):
        state.page -= 1
        state.just_switched_page = True
        st.rerun()
with col2:
    if state.page < len(pages)-1 and col2.button('➡️ 下一位'):
        if missing:
            st.error('請填完所有題目再繼續')
        else:
            state.page += 1
            state.just_switched_page = True
            state.answers.extend(answers)
            st.rerun()
    elif state.page == len(pages)-1 and col2.button('✅ 完成填寫'):
        if missing:
            st.error('還有題目未填寫')
        else:
             # 收集所有答案DataFrame
            df = pd.DataFrame(answers_page)
            df["填寫時間"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            # 清空 Google Sheets 然後寫入
            ws.clear()
            rows = [df.columns.tolist()] + df.values.tolist()
            ws.append_rows(rows, value_input_option='RAW')
            # 更新 submitted_users 本地檔
            submitted_users = pd.concat([
                submitted_users,
                pd.DataFrame([{"填答者": user}])
            ], ignore_index=True)
            submitted_users.to_csv(submitted_file, index=False)
            st.success("✅ 已成功將問卷結果上傳至 Google 試算表！")
            state.submitted = True

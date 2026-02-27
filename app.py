import streamlit as st
import pandas as pd
import datetime
from supabase import create_client, Client

# ==================== 页面布局 ====================
st.set_page_config(layout="wide")

# ==================== 页面纯净化 ====================
st.markdown("""
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
.stDeployButton {display:none !important;}
[data-testid="stToolbar"] {visibility: hidden !important;}
[data-testid="stDecoration"] {visibility: hidden !important;}
[data-testid="stStatusWidget"] {visibility: hidden !important;}

/* 尝试缩小 manage app 按钮 */
button[aria-label="Manage app"] {
    transform: scale(0.1);  /* 将按钮缩小 */
    opacity: 0.1;  /* 降低透明度，使其不那么显眼 */
}
</style>
""", unsafe_allow_html=True)

# ==================== 配置 ====================
DEBUG = False   # 本地调试=True，云端部署=False

# Supabase 配置
SUPABASE_URL = "https://zmkcwvfvkrswechxoxwb.supabase.co"
SUPABASE_KEY = "sb_publishable_SpD8P1R_L_kYjnvpQ3wEOA_EdRSbGB6"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ==================== 身份识别 ====================
query_params = st.query_params
expert_token = query_params.get("token")

experts_df = pd.read_excel("experts.xlsx")

if DEBUG and not expert_token:
    expert_name = st.selectbox("🛠 本地调试 - 选择专家身份", experts_df["expert_name"].tolist())
    st.info("当前为开发调试模式")
else:
    if not expert_token:
        st.error("⚠️ 请使用专属评审链接访问")
        st.stop()

    match = experts_df[experts_df["token"] == expert_token]
    if match.empty:
        st.error("⚠️ 专家身份验证失败")
        st.stop()

    expert_name = match.iloc[0]["expert_name"]

# ==================== 加载数据 ====================
@st.cache_data
def load_data():
    return pd.read_excel("data_final_v3.xlsx")

df = load_data()
raw_options = df['ID'].astype(str).tolist()

# ==================== Session ====================
if 'current_index' not in st.session_state:
    st.session_state.current_index = 0

def on_doc_change():
    st.session_state.current_index = (
        st.session_state.display_ids.index(st.session_state.doc_selector)
    )

# ==================== 已评审 ====================
if DEBUG:
    reviewed = []
else:
    try:
        reviewed = [r['paper_id'] for r in supabase.table("reviews")
                    .select("paper_id")
                    .eq("expert_name", expert_name)
                    .execute().data]
    except:
        reviewed = []

st.session_state.display_ids = [
    f"{oid} {'✅' if oid in reviewed else '⏳'}" for oid in raw_options
]

# ==================== 评审工作台 ====================
col_title, col_btn = st.columns([8, 2])

with col_title:
    st.markdown("## 👨‍🔬 评审工作台")

with col_btn:
    show_guide = st.button("📘 评审工作指南")

if show_guide:
    with st.expander("📘 评审工作指南", expanded=True):
        st.markdown("""
### 评审目标
系统评估 AI 推演结论与人类专家判断的一致性、可靠性和科学价值。

### 评审流程
1. 阅读原始证据  
2. 阅读 AI 推演  
3. 阅读原文结论  
4. 进行科研能力评分  
5. 给出人机对比评价  

### 评分原则
- 基于科学严谨性
- 避免极端打分
- 真实反映判断

### 评分用途
用于 AI 推演系统评估与科研论文发表。
""")

col1, col2, col3 = st.columns([2,5,3])

with col1:
    st.metric("当前专家", expert_name)

with col2:
    st.selectbox("选择文献",
                 options=st.session_state.display_ids,
                 index=st.session_state.current_index,
                 key="doc_selector",
                 on_change=on_doc_change)

with col3:
    st.metric("评审进度", f"{len(reviewed)} / {len(raw_options)}")

st.progress(len(reviewed)/len(raw_options))
st.divider()

# ==================== 当前文献 ====================
current_doc_id = raw_options[st.session_state.current_index]
row = df.iloc[st.session_state.current_index]

# ==================== 内容展示 ====================
tab_evid, tab_ai, tab_author, tab_score = st.tabs(
    ["📄 原始证据", "🧠 AI 推演", "📖 原文结论", "✍️ 评估量表"]
)

with tab_evid:
    st.text_area("原始证据", row['Evidence'], height=520, disabled=True)

with tab_ai:
    st.text_area("AI 推演", row['AI_Report'], height=520, disabled=True)

with tab_author:
    st.markdown(row['Author_Conclusion'])

# ==================== 评分表 ====================
with tab_score:
    with st.form("review_form"):

        st.subheader("第一部分：科研能力评分")

        st.markdown("**逻辑严密性**：逻辑结构是否严谨、推理是否连贯")
        s1 = st.slider("逻辑严密性", 0, 10, 0)

        st.markdown("**生物学合理性**：是否符合生物学机理与共识")
        s2 = st.slider("生物学合理性", 0, 10, 0)

        st.markdown("**证据整合力**：证据链是否系统完整")
        s3 = st.slider("证据整合力", 0, 10, 0)

        st.markdown("**转化洞察力**：是否具备转化应用潜力")
        s4 = st.slider("转化洞察力", 0, 10, 0)

        st.subheader("第二部分：人机对比评分")
        s_human = st.slider("AI 相对人类专家水平", 0.0, 10.0, 0.0, step=0.1)

        st.subheader("第三部分：定性评价")
        consistency = st.selectbox("一致性评价", ["高度一致", "基本一致", "存在偏差", "严重违背"])
        highlights = st.text_area("亮点分析")
        risks = st.text_area("局限与风险")
        value = st.text_area("科学价值建议")

        st.subheader("第四部分：综合判断")
        turing_test = st.radio("图灵测试倾向", ["肯定会", "可能会", "中立", "不太可能", "绝无可能"], horizontal=True)

        submit_button = st.form_submit_button("🚀 提交评分")

# ==================== 提交逻辑 ====================
if submit_button:

    if (s1 + s2 + s3 + s4 + s_human) == 0:
        st.error("评分不能全为 0")
        st.stop()

    if current_doc_id in reviewed:
        st.error("该文献已提交")
        st.stop()

    review_entry = {
        "expert_name": expert_name,
        "paper_id": current_doc_id,
        "score_1": s1,
        "score_2": s2,
        "score_3": s3,
        "score_4": s4,
        "human_comparison": s_human,
        "consistency": consistency,
        "highlights": highlights,
        "risks": risks,
        "value": value,
        "turing_test": turing_test,
        "submit_time": datetime.datetime.utcnow().isoformat()
    }

    try:
        supabase.table("reviews").insert(review_entry).execute()
        st.success("✅ 评分提交成功！")
        st.balloons()
        st.experimental_rerun()
    except Exception as e:
        st.error(f"提交失败：{e}")




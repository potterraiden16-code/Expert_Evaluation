import streamlit as st
import pandas as pd
import datetime
from supabase import create_client, Client

# ================= 页面配置 =================
st.set_page_config(layout="wide")

# ================= 页面纯净化 =================
st.markdown("""
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
.stDeployButton {display:none !important;}
[data-testid="stToolbar"] {visibility: hidden !important;}
[data-testid="stDecoration"] {visibility: hidden !important;}
[data-testid="stStatusWidget"] {visibility: hidden !important;}

.block-evidence {background:#F8FBFF;padding:12px;border-radius:10px;}
.block-ai {background:#FFF7EE;padding:12px;border-radius:10px;}
.block-author {background:#F7FFF7;padding:12px;border-radius:10px;}
</style>
""", unsafe_allow_html=True)

# ================= 配置 =================
DEBUG = False   # 本地调试=True，云端部署=False

SUPABASE_URL = "https://zmkcwvfvkrswechxoxwb.supabase.co"
SUPABASE_KEY = "sb_publishable_SpD8P1R_L_kYjnvpQ3wEOA_EdRSbGB6"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ================= 身份识别 =================
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
        st.error("⚠️ 专家身份无效")
        st.stop()
    expert_name = match.iloc[0]["expert_name"]

# ================= 加载数据 =================
@st.cache_data
def load_data():
    return pd.read_excel("data_final_v3.xlsx")

df = load_data()
raw_options = df['ID'].astype(str).tolist()

# ================= Session =================
if 'current_index' not in st.session_state:
    st.session_state.current_index = 0

def on_doc_change():
    st.session_state.current_index = st.session_state.display_ids.index(st.session_state.doc_selector)

# ================= 已评审 =================
if DEBUG:
    reviewed = []
else:
    reviewed = [r['paper_id'] for r in supabase.table("reviews")
                .select("paper_id")
                .eq("expert_name", expert_name)
                .execute().data]

st.session_state.display_ids = [f"{oid} {'✅' if oid in reviewed else '⏳'}" for oid in raw_options]

# ================= 工作台 =================
col1, col2, col3 = st.columns([2,5,3])

with col1:
    st.metric("当前专家", expert_name)

with col2:
    st.selectbox("选择文献",
                 st.session_state.display_ids,
                 index=st.session_state.current_index,
                 key="doc_selector",
                 on_change=on_doc_change)

with col3:
    st.metric("评审进度", f"{len(reviewed)} / {len(raw_options)}")

st.divider()

# ================= 当前文献 =================
current_doc_id = raw_options[st.session_state.current_index]
row = df.iloc[st.session_state.current_index]

# ===== 文献切换 → 评分清空 =====
if "last_doc" not in st.session_state:
    st.session_state.last_doc = current_doc_id

if st.session_state.last_doc != current_doc_id:
    for k in list(st.session_state.keys()):
        if k.startswith("score_") or k.startswith("text_"):
            del st.session_state[k]
    st.session_state.last_doc = current_doc_id
    st.rerun()

# ================= Tabs =================
tab_read, tab_score = st.tabs(["📚 证据与结论对比", "✍️ 评估量表"])

# ================= 阅读区 =================
with tab_read:
    c1, c2, c3 = st.columns(3)

    with c1:
        st.markdown("### 📄 原始证据")
        st.markdown(f"<div class='block-evidence'>", unsafe_allow_html=True)
        st.text_area("", row['Evidence'], height=520, disabled=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with c2:
        st.markdown("### 🧠 AI 推演")
        st.markdown(f"<div class='block-ai'>", unsafe_allow_html=True)
        st.text_area("", row['AI_Report'], height=520, disabled=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with c3:
        st.markdown("### 📖 原文结论")
        st.markdown(f"<div class='block-author'>", unsafe_allow_html=True)
        st.text_area("", row['Author_Conclusion'], height=520, disabled=True)
        st.markdown("</div>", unsafe_allow_html=True)

# ================= 评分表 =================
with tab_score:
    with st.form("review_form"):

        st.subheader("科研能力评分")
        s1 = st.slider("逻辑严密性", 0, 10, 0, key="score_s1")
        s2 = st.slider("生物学合理性", 0, 10, 0, key="score_s2")
        s3 = st.slider("证据整合力", 0, 10, 0, key="score_s3")
        s4 = st.slider("转化洞察力", 0, 10, 0, key="score_s4")

        st.subheader("人机对比")
        s_human = st.slider("AI 相对人类水平", 0.0, 10.0, 0.0, 0.1, key="score_human")

        st.subheader("定性评价")
        consistency = st.selectbox("一致性评价", ["高度一致", "基本一致", "存在偏差", "严重违背"], key="text_consistency")
        highlights = st.text_area("亮点分析", key="text_highlights")
        risks = st.text_area("局限与风险", key="text_risks")
        value = st.text_area("科学价值建议", key="text_value")

        turing_test = st.radio("图灵测试倾向",
                               ["肯定会", "可能会", "中立", "不太可能", "绝无可能"],
                               horizontal=True, key="text_turing")

        submit_button = st.form_submit_button("🚀 提交评分")

# ================= 提交 =================
if submit_button:

    if (s1+s2+s3+s4+s_human)==0:
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

    supabase.table("reviews").insert(review_entry).execute()
    st.success("✅ 评分提交成功！")
    st.balloons()
    st.rerun()

import streamlit as st
import pandas as pd
import datetime
from supabase import create_client, Client

st.set_page_config(layout="wide")

# ==================== 页面纯净化 ====================
st.markdown("""
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
.stDeployButton {display:none !important;}

/* 右下角 manage app */
button[title="Manage app"] {display: none !important;}
iframe {display: none !important;}

/* 顶部工具栏 */
[data-testid="stToolbar"] {visibility: hidden !important;}
[data-testid="stDecoration"] {visibility: hidden !important;}
[data-testid="stStatusWidget"] {visibility: hidden !important;}
</style>
""", unsafe_allow_html=True)

# ==================== 配置 ====================
DEBUG = True   # 本地调试=True，云端部署=False

# Supabase 配置
SUPABASE_URL = "https://zmkcwvfvkrswechxoxwb.supabase.co"
SUPABASE_KEY = "sb_publishable_SpD8P1R_L_kYjnvpQ3wEOA_EdRSbGB6"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ==================== 身份识别 ====================
query_params = st.query_params
expert_token = query_params.get("token")

experts_df = pd.read_excel("experts.xlsx")

if DEBUG and not expert_token:
    expert_name = st.selectbox(
        "🛠 本地调试 - 选择专家身份",
        experts_df["expert_name"].tolist()
    )
    st.info("当前为开发调试模式（无 token）")
else:
    if not expert_token:
        st.error("⚠️ 无效访问链接，请使用专属评审链接")
        st.stop()

    match = experts_df[experts_df["token"] == expert_token]
    if match.empty:
        st.error("⚠️ 无效专家身份")
        st.stop()

    expert_name = match.iloc[0]["expert_name"]
    st.success(f"当前专家：{expert_name}")

# ==================== 加载文献数据 ====================
@st.cache_data
def load_data():
    return pd.read_excel("data_final_v3.xlsx")

df = load_data()
if df.empty:
    st.error("文献数据加载失败")
    st.stop()

# ==================== Session 初始化 ====================
if 'current_index' not in st.session_state:
    st.session_state.current_index = 0

def on_doc_change():
    st.session_state.current_index = (
        st.session_state.all_display_options
        .index(st.session_state.doc_selector)
    )

# ==================== 评审工作台 ====================
st.markdown("## 👨‍🔬 评审工作台")

raw_options = df['ID'].astype(str).tolist()

# 读取云端已评审列表
if DEBUG:
    reviewed = []
else:
    try:
        reviewed = [r['paper_id'] for r in supabase.table("reviews")
                    .select("paper_id")
                    .eq("expert_name", expert_name)
                    .execute()
                    .data]
    except Exception:
        reviewed = []
        st.warning("⚠️ 当前无法连接评审数据库，进度暂不可用")

st.session_state.all_display_options = [
    f"{oid} {'✅' if oid in reviewed else '⏳'}"
    for oid in raw_options
]

col1, col2, col3 = st.columns([2, 5, 3])

with col1:
    st.metric("当前专家", expert_name)

with col2:
    st.selectbox(
        "选择文献",
        options=st.session_state.all_display_options,
        index=st.session_state.current_index,
        key="doc_selector",
        on_change=on_doc_change
    )

with col3:
    st.metric("评审进度", f"{len(reviewed)} / {len(raw_options)}")

st.progress(len(reviewed) / len(raw_options))
st.divider()

# ==================== 当前文献 ====================
current_doc_id = raw_options[st.session_state.current_index]
row = df.iloc[st.session_state.current_index]

if current_doc_id in reviewed:
    st.warning("⚠️ 该文献你已完成评审，如需修改请谨慎操作")

# ==================== 文献显示 ====================
tab_evid, tab_ai, tab_author, tab_score = st.tabs(
    ["📄 原始证据", "🧠 AI 推演", "📖 原文结论", "✍️ 评估量表"]
)

with tab_evid:
    st.text_area("原始证据", value=row['Evidence'], height=520, disabled=True)

with tab_ai:
    st.text_area("AI 推演", value=row['AI_Report'], height=520, disabled=True)

with tab_author:
    st.markdown(row['Author_Conclusion'])

# ==================== 评分表单 ====================
with tab_score:
    with st.form("delphi_form"):
        st.subheader("第一部分：科研能力评分 (1–10)")
        s1 = st.slider("逻辑严密性", 0, 10, 0)
        s2 = st.slider("生物学合理性", 0, 10, 0)
        s3 = st.slider("证据整合力", 0, 10, 0)
        s4 = st.slider("转化洞察力", 0, 10, 0)

        st.subheader("第二部分：人机对比评分")
        s_human = st.slider("人机水平评分", 0.0, 10.0, 0.0, step=0.1)

        st.subheader("第三部分：定性评价")
        consistency = st.selectbox("一致性评价", ["高度一致", "基本一致", "存在偏差", "严重违背"])
        highlights = st.text_area("亮点分析")
        risks = st.text_area("局限与风险")
        value = st.text_area("科学价值建议")

        st.subheader("第四部分：综合标定")
        turing_test = st.radio("图灵测试倾向", ["肯定会", "可能会", "中立", "不太可能", "绝无可能"], horizontal=True)

        submit_button = st.form_submit_button("🚀 提交评分")

# ==================== 提交评分（调试版） ====================
if submit_button:

    st.write("⚡ 表单已触发提交")  # 检查表单是否触发

    if (s1 + s2 + s3 + s4 + s_human) == 0:
        st.error("⚠️ 评分不能全为 0")
        st.stop()

    if current_doc_id in reviewed:
        st.error("⚠️ 该文献你已提交过，禁止重复提交")
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

    # 🔹 输出调试信息
    st.subheader("🔹 Debug: Review Entry")
    st.json(review_entry)

    if DEBUG:
        st.info("⚡ DEBUG 模式 - 模拟插入 Supabase，不会写入数据库")
    else:
        try:
            result = supabase.table("reviews").insert(review_entry).execute()
            st.subheader("🔹 Debug: Supabase 返回")
            st.write(result)

            if result.get("status_code") in [200, 201]:
                st.success("✅ 评分提交成功！")
                st.balloons()
            else:
                st.error(f"⚠️ 插入失败，返回状态码: {result.get('status_code')}")
        except Exception as e:
            st.error(f"提交异常：{e}")

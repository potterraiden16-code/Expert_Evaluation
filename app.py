import streamlit as st
import pandas as pd
import datetime
from supabase import create_client, Client

# ==================== 配置 ====================
DEBUG = False   # 本地调试=True，生产部署=False

# Supabase 配置
SUPABASE_URL = "https://zmkcwvfvkrswechxoxwb.supabase.co"
SUPABASE_KEY = "sb_publishable_SpD8P1R_L_kYjnvpQ3wEOA_EdRSbGB6"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ==================== 身份识别 ====================
query_params = st.query_params  # 新版 API
expert_token = query_params.get("token", [None])[0]  # 取列表第一个值

experts_df = pd.read_excel("experts.xlsx")  # 本地存储专家名单

if DEBUG and not expert_token:
    # 本地调试模式可选专家
    expert_name = st.sidebar.selectbox(
        "🛠 本地调试 - 选择专家身份",
        experts_df["expert_name"].tolist()
    )
    st.sidebar.info("当前为开发模式（无 token）")
else:
    if not expert_token:
        st.error("⚠️ 无效访问链接，请使用专属评审链接")
        st.stop()
    match = experts_df[experts_df["token"] == expert_token]
    if match.empty:
        st.error("⚠️ 无效专家身份")
        st.stop()
    expert_name = match.iloc[0]["expert_name"]
    st.sidebar.success(f"当前专家：{expert_name}")

# ==================== 加载文献数据（本地） ====================
@st.cache_data
def load_data():
    try:
        return pd.read_excel("data_final_v3.xlsx")
    except Exception as e:
        st.error(f"无法读取文献数据: {e}")
        return pd.DataFrame()

df = load_data()
if df.empty:
    st.stop()

# ==================== 当前文献选择 ====================
if 'current_index' not in st.session_state:
    st.session_state.current_index = 0

def on_doc_change():
    st.session_state.current_index = st.session_state.all_display_options.index(st.session_state.doc_selector)

with st.sidebar:
    st.title("👨‍🔬 评审工作台")
    raw_options = df['ID'].astype(str).tolist()
    # 查询云端已提交的文献ID
    reviewed = [r['paper_id'] for r in supabase.table("reviews").select("paper_id").eq("expert_name", expert_name).execute().data]
    st.session_state.all_display_options = [f"{oid} {'✅' if oid in reviewed else '⏳'}" for oid in raw_options]

    selected_display = st.selectbox(
        "选择文献：",
        options=st.session_state.all_display_options,
        index=st.session_state.current_index,
        key="doc_selector",
        on_change=on_doc_change
    )

current_doc_id = raw_options[st.session_state.current_index]
row = df.iloc[st.session_state.current_index]

st.write(f"总体进度: **{len([r for r in reviewed if r])} / {len(raw_options)}**")

# ==================== 文献显示 ====================
tab_evid, tab_ai, tab_author, tab_score = st.tabs(
    ["📄 原始证据", "🧠 AI 推演", "📖 原文结论", "✍️ 评估量表"]
)

with tab_evid:
    st.text_area("原始证据", value=row['Evidence'], height=400, disabled=True)

with tab_ai:
    st.text_area("AI 推演", value=row['AI_Report'], height=400, disabled=True)

with tab_author:
    st.markdown(row['Author_Conclusion'])

# ==================== 评分表单 ====================
with tab_score:
    with st.form("delphi_form"):
        st.subheader("第一部分：科研能力评分 (1-10)")
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

# ==================== 提交评分到云端 ====================
if submit_button:
    if (s1 + s2 + s3 + s4 + s_human) == 0:
        st.error("⚠️ 评分项不能全为0")
    else:
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
        except Exception as e:
            st.error(f"提交失败：{e}")

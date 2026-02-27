import streamlit as st
import pandas as pd
import datetime
from supabase import create_client, Client

st.set_page_config(layout="wide")

# ==================== 页面纯净化 ====================
st.markdown("""
<style>
#MainMenu, footer, header {visibility: hidden;}
[data-testid="stToolbar"] {visibility: hidden;}
iframe {display:none;}
</style>
""", unsafe_allow_html=True)

# ==================== 配置 ====================
DEBUG = False

SUPABASE_URL = "https://zmkcwvfvkrswechxoxwb.supabase.co"
SUPABASE_KEY = "sb_publishable_SpD8P1R_L_kYjnvpQ3wEOA_EdRSbGB6"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ==================== 身份 ====================
query_params = st.query_params
expert_token = query_params.get("token")

experts_df = pd.read_excel("experts.xlsx")

if DEBUG and not expert_token:
    expert_name = st.selectbox("🛠 调试模式 - 选择专家", experts_df["expert_name"].tolist())
else:
    if not expert_token:
        st.error("⚠️ 访问无效")
        st.stop()
    match = experts_df[experts_df["token"] == expert_token]
    if match.empty:
        st.error("⚠️ 专家身份无效")
        st.stop()
    expert_name = match.iloc[0]["expert_name"]

# ==================== 数据 ====================
@st.cache_data
def load_data():
    return pd.read_excel("data_final_v3.xlsx")

df = load_data()

# ==================== Session ====================
if "current_index" not in st.session_state:
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
                    .execute()
                    .data]
    except:
        reviewed = []

# ==================== 顶部 ====================
raw_ids = df['ID'].astype(str).tolist()
st.session_state.display_ids = [
    f"{oid} {'✅' if oid in reviewed else '⏳'}" for oid in raw_ids
]

c1, c2, c3 = st.columns([2,6,2])
with c1:
    st.metric("专家", expert_name)
with c2:
    st.selectbox("选择文献",
                 st.session_state.display_ids,
                 index=st.session_state.current_index,
                 key="doc_selector",
                 on_change=on_doc_change)
with c3:
    st.metric("进度", f"{len(reviewed)} / {len(raw_ids)}")

# ==================== 当前文献 ====================
doc_id = raw_ids[st.session_state.current_index]
row = df.iloc[st.session_state.current_index]
doc_key = f"doc_{doc_id}_"

# ==================== Tabs ====================
tab_read, tab_score = st.tabs(["📊 证据对比阅读", "✍️ 评估量表"])

# ==================== 阅读 ====================
with tab_read:
    st.markdown("""
    <style>
    .block {border-radius:12px;padding:14px;height:520px;overflow-y:auto;font-size:15px;line-height:1.6;}
    .evid {background:#f7fbff;color:#0f172a;}
    .ai {background:#f0fdf4;color:#064e3b;}
    .author {background:#fff7ed;color:#7c2d12;}
    </style>
    """, unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("### 📄 原始证据")
        st.markdown(f"<div class='block evid'>{row['Evidence']}</div>", unsafe_allow_html=True)
    with c2:
        st.markdown("### 🧠 AI 推演")
        st.markdown(f"<div class='block ai'>{row['AI_Report']}</div>", unsafe_allow_html=True)
    with c3:
        st.markdown("### 📖 原文结论")
        st.markdown(f"<div class='block author'>{row['Author_Conclusion']}</div>", unsafe_allow_html=True)


# ==================== 评分 ====================
with tab_score:

    st.markdown("## ✍️ 评估量表")

    if doc_id in reviewed:
        st.warning("⚠️ 该文献你已完成评审，禁止重复提交")

    with st.form("score_form"):

        # ---------- 第一部分 ----------
        st.markdown("### 🧪 第一部分：科研能力维度定量评分（1–10分）")

        st.markdown("""
        **1. 逻辑严密性与简约性**  
        *因果链条闭环程度与逻辑效率*  
        **1–2分：** 存在逻辑断层、循环论证或路径冗长  
        **5分：** 逻辑通顺，因果合理，符合常规科研推导  
        **9–10分：** 因果链极度精致、简洁，无冗余推导
        """)
        s1 = st.slider("评分", 1, 10, 5, key=doc_key+"s1")

        st.markdown("""
        **2. 生物学合理性与深度**  
        *知识准确性 + 是否出现 AI 幻觉*  
        **1–2分：** 出现基础常识错误或生化过程误述  
        **5分：** 符合教科书与权威综述描述  
        **9–10分：** 引入准确前沿/跨学科机制，深度极高
        """)
        s2 = st.slider("评分", 1, 10, 5, key=doc_key+"s2")

        st.markdown("""
        **3. 证据整合力（含负向结果）**  
        *对输入线索的利用率及复杂结果解释能力*  
        **1–2分：** 忽略关键数据，尤其是阴性结果  
        **5分：** 合理整合主要指标，解释显著结果  
        **9–10分：** 挖掘隐性关联，解释复杂非线性关系
        """)
        s3 = st.slider("评分", 1, 10, 5, key=doc_key+"s3")

        st.markdown("""
        **4. 转化洞察力与可行性**  
        *假说原创性 + 干预建议具体性*  
        **1–2分：** 纯属复述，或“正确的废话”  
        **5分：** 解释合理，建议符合临床常规  
        **9–10分：** 提出挑战性新假说，建议极具转化潜力
        """)
        s4 = st.slider("评分", 1, 10, 5, key=doc_key+"s4")

        # ---------- 第二部分 ----------
        st.markdown("### 🧠 第二部分：与人类科学家水平对比（1–10分）")

        st.markdown("""
        **评分参考锚点：**  
        **9.0–10：卓越 (Exceptional)** — 顶级期刊讨论水平  
        **7.0–8.9：优秀 (Senior Expert)** — 资深教授水平  
        **5.0–6.9：合格 (Competent)** — 博士 / 副教授水平  
        **3.0–4.9：欠佳 (Developing)** — 初级研究助理水平  
        **1.0–2.9：不合格 (Flawed)** — 存在严重幻觉或科学错误
        """)
        s_human = st.slider("人机对比评分", 1.0, 10.0, 6.0, 0.1, key=doc_key+"s5")

        # ---------- 第三部分 ----------
        st.markdown("### 📝 第三部分：定性专家评估")

        consistency = st.radio(
            "一致性评价：对比该领域公认科学逻辑，AI 推论整体表现为：",
            ["高度一致", "基本一致", "存在偏差", "严重违背"],
            key=doc_key+"s6"
        )

        highlights = st.text_area(
            "亮点分析：请说明 AI 在哪些环节展现出超越人类专家基准线的洞察力（可不填）",
            key=doc_key+"s7"
        )

        risks = st.text_area(
            "局限与风险（含幻觉检测）：请指出是否存在过度推断、忽略现实干扰或科学性错误",
            key=doc_key+"s8"
        )

        value = st.text_area(
            "科学价值与转化建议：是否值得进一步开展动物实验、临床验证或政策试点？",
            key=doc_key+"s9"
        )

        # ---------- 第四部分 ----------
        st.markdown("### 🧬 第四部分：科学图灵测试")

        turing_test = st.radio(
            "若完全双盲，您是否会认为该推论出自深耕本领域 ≥10 年的资深科学家？",
            ["肯定会", "可能会", "中立", "不太可能", "绝无可能"],
            horizontal=True,
            key=doc_key+"s10"
        )

        submit = st.form_submit_button("🚀 提交评分")

# ==================== 提交 ====================
if submit:

    if doc_id in reviewed:
        with tab_score:
            st.error("⚠️ 请勿重复提交")
        st.stop()

    total = s1 + s2 + s3 + s4 + s_human
    if total == 0:
        with tab_score:
            st.error("⚠️ 评分不能全为 0")
        st.stop()

    review_entry = {
        "expert_name": expert_name,
        "paper_id": doc_id,
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
        st.success("✅ 提交成功")
        st.rerun()
    except Exception as e:
        with tab_score:
            st.error(f"❌ 提交失败：{e}")


import streamlit as st
import pandas as pd
import datetime
import os
import json
import re
from supabase import create_client, Client

# =========================================================
# 页面配置
# =========================================================
st.set_page_config(layout="wide")

st.markdown("""
<style>
#MainMenu, footer, header {visibility: hidden;}
[data-testid="stToolbar"] {visibility: hidden;}
iframe {display:none;}
</style>
""", unsafe_allow_html=True)

# =========================================================
# 全局配置
# =========================================================
DEBUG = False

SUPABASE_URL = "https://zmkcwvfvkrswechxoxwb.supabase.co"
SUPABASE_KEY = "sb_publishable_SpD8P1R_L_kYjnvpQ3wEOA_EdRSbGB6"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# =========================================================
# Markdown 工具
# =========================================================
def split_markdown_sections(md_text):
    pattern = r'(#{1,6} .*)'
    parts = re.split(pattern, md_text)

    sections = []
    current_title = "总览"
    current_content = ""

    for part in parts:
        if re.match(r'#{1,6} ', part):
            if current_content.strip():
                sections.append((current_title, current_content.strip()))
            current_title = part.replace("#", "").strip()
            current_content = ""
        else:
            current_content += part

    if current_content.strip():
        sections.append((current_title, current_content.strip()))

    return sections


def render_markdown_blocks(md_text):
    sections = split_markdown_sections(md_text)
    for title, content in sections:
        with st.expander(title, expanded=(title == "总览")):
            st.markdown(content)

# =========================================================
# 工具函数
# =========================================================
def paper_sort_key(name):
    nums = re.findall(r'\d+', name)
    return int(nums[0]) if nums else 0


def load_md(path):
    if not os.path.exists(path):
        return "⚠️ 文件缺失"
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

# =========================================================
# 数据索引
# =========================================================
@st.cache_data
def load_dataset(root="dataset"):
    records = []
    for domain in sorted(os.listdir(root)):
        domain_path = os.path.join(root, domain)
        if not os.path.isdir(domain_path):
            continue

        for paper_id in sorted(os.listdir(domain_path), key=paper_sort_key):
            paper_path = os.path.join(domain_path, paper_id)
            if not os.path.isdir(paper_path):
                continue

            meta_path = os.path.join(paper_path, "meta.json")
            if not os.path.exists(meta_path):
                continue

            with open(meta_path, "r", encoding="utf-8") as f:
                meta = json.load(f)

            records.append({
                "domain": domain,
                "paper_id": paper_id,
                "title": meta.get("title", ""),
                "author": meta.get("author", ""),
                "path": paper_path,
                "order": paper_sort_key(paper_id)
            })

    df = pd.DataFrame(records)
    return df.sort_values(by=["domain", "order"]).reset_index(drop=True)

df = load_dataset()
if df.empty:
    st.error("⚠️ 数据集为空")
    st.stop()

# =========================================================
# 专家身份认证
# =========================================================
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

# =========================================================
# Session
# =========================================================
if "current_index" not in st.session_state:
    st.session_state.current_index = 0

def on_doc_change():
    st.session_state.current_index = (
        st.session_state.display_ids.index(st.session_state.doc_selector)
    )

# =========================================================
# 已评审
# =========================================================
if DEBUG:
    reviewed = []
else:
    try:
        reviewed = [
            r["paper_id"] for r in
            supabase.table("reviews")
            .select("paper_id")
            .eq("expert_name", expert_name)
            .execute()
            .data
        ]
    except:
        reviewed = []

# =========================================================
# 顶部
# =========================================================
raw_ids = df["paper_id"].astype(str).tolist()
st.session_state.display_ids = [
    f"{oid} {'✅' if oid in reviewed else '⏳'}" for oid in raw_ids
]

c1, c2, c3 = st.columns([2, 6, 2])
with c1:
    st.metric("专家", expert_name)
with c2:
    st.selectbox(
        "选择文献",
        st.session_state.display_ids,
        index=st.session_state.current_index,
        key="doc_selector",
        on_change=on_doc_change
    )
with c3:
    st.metric("进度", f"{len(reviewed)} / {len(raw_ids)}")
with st.expander("📜 项目说明 | 给专家的介绍信（点击展开）", expanded=False):

    st.markdown("""
尊敬的专家：  

您好！  

非常荣幸能邀请您参与 **“德尔菲专家法评估表型大模型科研发现能力”** 的评估工作。  

随着人工智能在生物医学领域的飞速发展，评估大模型是否具备如人类科学家般的 **“科研发现能力”** 已成为前沿课题。本研究旨在通过 **模拟人类科学家的科研流程**，对特定表型大模型在复杂生物医学背景下的 **逻辑推演与科学发现能力** 进行系统化、定量化标定。  

---

## 一、评估原理与设计思路  

我们选取 **节律生物学与心脏病学领域** 的高质量论文（初步共 20 篇）作为评估基石。  

评估核心遵循 **“信息隔离 + 双盲推演”** 原则：  

**1. 事实剥离**  
利用成熟的商业化 AI 从论文中提取 **【客观背景知识】与【实验事实】**，严格剔除任何作者主观推论或结论。  

**2. 独立推演**  
将这些纯粹的数据与背景输入待测 **表型大模型**，要求其仅基于这些线索，独立推导科学结论。  

**3. 金标准对比**  
以原论文作者结论作为 **“黄金标准”**，交由专家对 **AI 推演结果与人类结论** 进行系统比较与评价。  

---

## 二、专家任务说明  

作为评审专家，您需查阅 **“证据对比阅读”** 标签，并完成 **评估量表**，包括：  

### 1. 定量评分（1–10分）  
- 逻辑严密性与简约性  
- 生物学合理性（是否存在 AI 幻觉）  
- 证据整合力（尤其对阴性/复杂结果的解释能力）  
- 转化洞察力与可行性  

### 2. 学术水平定标  
参照评分锚点，判定模型整体推理水平相当于：  
**初级研究助理 / 博士或副教授 / 资深教授**  

### 3. 定性分析  
指出 AI 推演中的：  
- **亮点**（如超越人类的洞察）  
- **局限**（如过度推断、科学性错误）  

### 4. 科学图灵测试  
在完全双盲条件下，判断该推论 **是否像出自一位深耕本领域 ≥10 年的资深科学家之手**。  

---

## 三、注意事项  

1. 请勿重复提交评估  
2. 评分前请确认您打开的是 **专属评审链接**  
3. 页面左上角显示的专家姓名应为 **您的姓名**  

---

您的专业判断对于 **准确评估 AI 的科研潜力** 至关重要。  

衷心感谢您的参与与宝贵时间！  

如对评估流程有任何疑问，欢迎随时联系研究团队。  
""")

# =========================================================
# 当前文献
# =========================================================
row = df.iloc[st.session_state.current_index]
doc_id = row["paper_id"]
paper_path = row["path"]
doc_key = f"doc_{doc_id}_"

evidence = load_md(os.path.join(paper_path, "A.md"))
author_conclusion = load_md(os.path.join(paper_path, "B.md"))
ai_report = load_md(os.path.join(paper_path, "C.md"))

st.markdown(f"""
### 📄 {row['title']}
**作者：** {row['author']}  
**领域：** {row['domain']}  
""")

# =========================================================
# Tabs
# =========================================================
tab_read, tab_score = st.tabs(["📊 证据对比阅读", "✍️ 评估量表"])

# =========================================================
# 阅读区
# =========================================================
with tab_read:

    c1, c2, c3 = st.columns(3)

    with c1:
        st.markdown("### 📄 原始证据")
        with st.container(height=520):
            render_markdown_blocks(evidence)

    with c2:
        st.markdown("### 🧠 AI 推演")
        with st.container(height=520):
            render_markdown_blocks(ai_report)

    with c3:
        st.markdown("### 📖 原文结论")
        with st.container(height=520):
            render_markdown_blocks(author_conclusion)

# =========================================================
# 评分区（完整锚点保留）
# =========================================================
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

# =========================================================
# 提交
# =========================================================
if submit:

    if doc_id in reviewed:
        st.error("⚠️ 请勿重复提交")
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
        st.error(f"❌ 提交失败：{e}")


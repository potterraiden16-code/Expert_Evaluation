import streamlit as st
import pandas as pd
import datetime
import os

# --- 1. 页面配置 ---
st.set_page_config(
    page_title="德尔菲法专家评价系统 v3.0",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义样式：增强科研质感与状态显示
st.markdown("""
    <style>
    .stSlider {padding-bottom: 20px;}
    .section-header {color: #1f77b4; border-bottom: 2px solid #1f77b4; padding-bottom: 5px; margin-top: 25px; margin-bottom: 15px; font-weight: bold; font-size: 1.2rem;}
    .anchor-text {font-size: 0.85rem; color: #555; background: #f0f2f6; padding: 8px 12px; border-radius: 5px; margin-bottom: 10px; border-left: 3px solid #1f77b4;}
    .status-box {padding: 15px; border-radius: 8px; margin-bottom: 20px; text-align: center; font-weight: bold;}
    .pending {background-color: #fff3cd; color: #856404; border: 1px solid #ffeeba;}
    .completed {background-color: #d4edda; color: #155724; border: 1px solid #c3e6cb;}
    .stTextArea textarea {font-family: 'Courier New', Courier, monospace; font-size: 14px !important;}
    </style>
    """, unsafe_allow_html=True)


# --- 2. 数据处理与状态检查 ---
@st.cache_data
def load_data():
    try:
        return pd.read_excel("data_final_v3.xlsx")
    except Exception as e:
        st.error(f"无法读取原始数据文件: {e}")
        return pd.DataFrame()


def get_reviewed_ids():
    results_file = "expert_evaluations.csv"
    if os.path.exists(results_file):
        try:
            rdf = pd.read_csv(results_file, encoding='utf-8-sig')
            return rdf['文献ID'].unique().tolist()
        except:
            return []
    return []


df = load_data()
reviewed_ids = get_reviewed_ids()

# --- 3. 侧边栏：评审工作台 ---
with st.sidebar:
    st.title("👨‍🔬 德尔菲评审台")
    expert_name = st.text_input("评审专家姓名：", placeholder="请输入您的姓名")

    st.divider()
    if not df.empty:
        raw_options = df['ID'].tolist()
        display_options = [f"{oid} {'✅' if oid in reviewed_ids else '⏳'}" for oid in raw_options]
        option_map = dict(zip(display_options, raw_options))
        selected_display = st.selectbox("选择文献：", options=display_options)
        current_doc_id = option_map[selected_display]
        row = df[df['ID'] == current_doc_id].iloc[0]

        # 真实进度统计
        total_count = len(raw_options)
        reviewed_count = len(reviewed_ids)
        st.progress(reviewed_count / total_count)
        st.write(f"总体进度: **{reviewed_count} / {total_count}**")

    st.divider()
    results_file = "expert_evaluations.csv"
    if os.path.exists(results_file):
        with open(results_file, "rb") as f:
            st.download_button("💾 下载德尔菲汇总表", f, "delphi_results.csv", "text/csv", use_container_width=True)

# --- 4. 主界面：顶部状态提示 ---
if current_doc_id in reviewed_ids:
    st.markdown(f'<div class="status-box completed">✅ 您已提交过对此文献的评价（ID: {current_doc_id}）</div>',
                unsafe_allow_html=True)
else:
    st.markdown(f'<div class="status-box pending">⏳ 待处理：您尚未提交对此文献的专家评价，请在阅读后完成量表。</div>',
                unsafe_allow_html=True)

# --- 5. 文献内容展示 (标签化设计) ---
st.title(f"🔍 {current_doc_id}")
st.caption(f"文献标题: {row['Title']}")

# 恢复您喜欢的标签化内容展示
tab_evid, tab_ai, tab_author = st.tabs(
    ["📄 原始证据 (Evidence)", "🧠 AI 推演报告 (AI Report)", "📖 原文讨论 (Author Conclusion)"])

with tab_evid:
    st.text_area("evidence_content", value=row['Evidence'], height=500, disabled=True, label_visibility="collapsed")

with tab_ai:
    st.info("模型生成的逻辑推演报告如下：")
    st.text_area("ai_report_content", value=row['AI_Report'], height=450, disabled=True, label_visibility="collapsed")

with tab_author:
    st.warning("以下为原论文讨论部分结论，供对比参考：")
    st.markdown(row['Author_Conclusion'])

st.divider()

# --- 6. 德尔菲评分表单 ---
st.header("✍️ 德尔菲法专家评分量表")

with st.form("delphi_complete_form"):
    # 第一部分
    st.markdown('<div class="section-header">第一部分：具体科研能力定量评分 (1-10分)</div>', unsafe_allow_html=True)

    # 维度1
    st.markdown("**1. 逻辑严密性与简约性** (评价重点：因果链条的闭环程度与逻辑效率)")
    st.markdown('<div class="anchor-text">锚点：1-2分存在逻辑断层；5分逻辑通顺符合常规；9-10分链条细致优雅且简洁。</div>',
                unsafe_allow_html=True)
    s1 = st.slider("评分_逻辑", 0, 10, 0, key="s1", label_visibility="collapsed")

    # 维度2
    st.markdown("**2. 生物学合理性与深度** (评价重点：知识准确性及是否包含“幻觉”)")
    st.markdown(
        '<div class="anchor-text">锚点：1-2分基础常识错误；5分符合主流病理生理描述；9-10分调用准确前沿/跨学科机制。</div>',
        unsafe_allow_html=True)
    s2 = st.slider("评分_合理性", 0, 10, 0, key="s2", label_visibility="collapsed")

    # 维度3
    st.markdown("**3. 证据整合力** (评价重点：线索利用率，尤其是对阴性/非线性结果的解释)")
    st.markdown(
        '<div class="anchor-text">锚点：1-2分忽略关键数据；5分利用主要指标合理解释；9-10分挖掘隐性关联，对复杂数据给出自洽推论。</div>',
        unsafe_allow_html=True)
    s3 = st.slider("评分_整合力", 0, 10, 0, key="s3", label_visibility="collapsed")

    # 维度4
    st.markdown("**4. 转化洞察力与可行性** (评价重点：假说原创性及干预建议的具体操作性)")
    st.markdown(
        '<div class="anchor-text">锚点：1-2分纯数据复述或废话；5分建议符合临床常规；9-10分提供具挑战性新假说且具体。</div>',
        unsafe_allow_html=True)
    s4 = st.slider("评分_洞察力", 0, 10, 0, key="s4", label_visibility="collapsed")

    # 第二部分
    st.markdown('<div class="section-header">第二部分：您觉得与人类科学家相比本模型处于什么水准 (1-10分)</div>',
                unsafe_allow_html=True)
    st.markdown(
        '<div class="anchor-text">参考：9-10卓越(NSC级)；7-8优秀(资深教授)；5-6合格(博士/副高)；3-4欠佳(助理)；1-2不合格(幻觉严重)。</div>',
        unsafe_allow_html=True)
    s_human = st.slider("人类对比评分", 0, 10, 0, key="sh", label_visibility="collapsed")

    # 第三部分
    st.markdown('<div class="section-header">第三部分：定性评估</div>', unsafe_allow_html=True)
    consistency = st.selectbox("1. 一致性评价对比该领域公认逻辑，整体表现为：",
                               ["高度一致（几乎无偏差）", "基本一致（逻辑成立，细节略有出入）",
                                "存在偏差（存在关键逻辑断裂或误读）", "严重违背（存在基础科学性错误）"])

    highlights = st.text_area("2. 亮点分析：哪个环节展现了超越“人类科学家基准线”的洞察力？")
    risks = st.text_area("3. 局限与风险：是否存在过度推断、忽略现实因素或“幻觉”环节？")
    value = st.text_area("4. 科学价值与转化建议：基于此假说，是否值得启动进一步实验或政策试点？")

    # 第四部分
    st.markdown('<div class="section-header">第四部分：综合标定 (科学图灵测试)</div>', unsafe_allow_html=True)
    turing_test = st.radio(
        "如果您在完全双盲的情况下阅读此推论，您是否倾向于认为这出自一位深耕该领域 10 年以上的资深科学家之手？",
        ["肯定会", "可能会", "中立", "不太可能", "绝无可能"], horizontal=True)

    submit_button = st.form_submit_button("🚀 提交完整德尔菲评价表", use_container_width=True)

# --- 7. 保存逻辑 ---
if submit_button:
    if not expert_name:
        st.error("⚠️ 请在左侧填写您的姓名后再提交。")
    elif (s1 + s2 + s3 + s4 + s_human) == 0:
        st.error("⚠️ 请完成定量评分（分值不能全部为0）。")
    else:
        new_entry = {
            "专家": expert_name, "文献ID": current_doc_id,
            "提交时间": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
            "1_逻辑严密性": s1, "2_生物学合理性": s2, "3_证据整合力": s3, "4_转化洞察力": s4,
            "人机对比评分": s_human, "一致性": consistency, "亮点分析": highlights,
            "局限风险": risks, "科学价值": value, "图灵测试倾向": turing_test
        }
        rdf = pd.DataFrame([new_entry])
        if not os.path.isfile(results_file):
            rdf.to_csv(results_file, index=False, encoding='utf-8-sig')
        else:
            rdf.to_csv(results_file, mode='a', header=False, index=False, encoding='utf-8-sig')

        st.balloons()
        st.cache_data.clear()
        st.success(f"【{current_doc_id}】德尔菲评价提交成功！状态已更新。")
        st.rerun()

st.divider()
st.caption("德尔菲法专家评分系统 v3.0 | 标签化内容展示 | 自动状态跟踪")
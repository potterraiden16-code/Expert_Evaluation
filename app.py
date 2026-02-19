import streamlit as st
import pandas as pd
import datetime
import os

# --- 1. 页面配置 ---
st.set_page_config(page_title="德尔菲法专家评分系统", layout="wide")

# 自定义 CSS 增加科研质感
st.markdown("""
    <style>
    .stSlider {padding-bottom: 20px;}
    .report-card {background-color: #f8f9fa; padding: 20px; border-radius: 10px; border-left: 5px solid #007bff; margin-bottom: 20px;}
    .section-header {color: #1f77b4; border-bottom: 2px solid #1f77b4; padding-bottom: 5px; margin-top: 20px; margin-bottom: 15px; font-weight: bold;}
    .anchor-text {font-size: 0.85rem; color: #666; font-style: italic; background: #eee; padding: 5px 10px; border-radius: 5px;}
    </style>
    """, unsafe_allow_html=True)


# --- 2. 数据处理与状态检查 ---
@st.cache_data
def load_data():
    try:
        return pd.read_excel("data_final_v3.xlsx")
    except:
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

# --- 3. 侧边栏布局 ---
with st.sidebar:
    st.title("🧪 德尔菲法评审台")
    expert_name = st.text_input("评审专家姓名：", placeholder="请输入您的姓名")

    st.divider()
    if not df.empty:
        raw_options = df['ID'].tolist()
        display_options = [f"{oid} {'✅' if oid in reviewed_ids else '⏳'}" for oid in raw_options]
        option_map = dict(zip(display_options, raw_options))
        selected_display = st.selectbox("选择文献进行评审：", options=display_options)
        current_doc_id = option_map[selected_display]
        row = df[df['ID'] == current_doc_id].iloc[0]

        # 统计进度
        reviewed_count = len(reviewed_ids)
        st.progress(reviewed_count / len(raw_options))
        st.write(f"已完成: **{reviewed_count} / {len(raw_options)}**")

    st.divider()
    # 下载导出
    results_file = "expert_evaluations.csv"
    if os.path.exists(results_file):
        with open(results_file, "rb") as f:
            st.download_button("💾 下载德尔菲评价汇总表", f, "delphi_results.csv", "text/csv", use_container_width=True)

# --- 4. 主界面布局 ---
st.title(f"德尔菲法专家评分：{current_doc_id}")
if current_doc_id in reviewed_ids:
    st.success("✅ 此文献您已提交过评价，如有更新可再次提交覆盖原记录。")

tab_content, tab_rating = st.tabs(["📖 阅读内容", "✍️ 填写德尔菲量表"])

with tab_content:
    st.markdown("#### 文献标题")
    st.info(row['Title'])
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("**📚 原始证据池 (Evidence)**")
        st.text_area("e", row['Evidence'], height=500, disabled=True, label_visibility="collapsed")
    with col_b:
        st.markdown("**🧠 AI 推演报告 (AI Report)**")
        st.text_area("r", row['AI_Report'], height=500, disabled=True, label_visibility="collapsed")
        with st.expander("对比参考：原作者结论"):
            st.markdown(row['Author_Conclusion'])

with tab_rating:
    with st.form("delphi_form"):
        # --- 第一部分 ---
        st.markdown('<div class="section-header">第一部分：具体科研能力定量评分 (1-10分)</div>', unsafe_allow_html=True)

        # 维度1
        st.markdown("**1. 逻辑严密性与简约性** (评价重点：因果链闭环与效率)")
        st.markdown('<div class="anchor-text">锚点参考：1-2分逻辑断层；5分常规推导；9-10分细致且优雅简洁</div>',
                    unsafe_allow_html=True)
        s1 = st.slider("评分_逻辑", 0, 10, 0, label_visibility="collapsed")

        # 维度2
        st.markdown("**2. 生物学合理性与深度** (评价重点：知识准确性及幻觉检测)")
        st.markdown('<div class="anchor-text">锚点参考：1-2分基础常识错误；5分教科书级准确；9-10分前沿跨学科深度</div>',
                    unsafe_allow_html=True)
        s2 = st.slider("评分_合理性", 0, 10, 0, label_visibility="collapsed")

        # 维度3
        st.markdown("**3. 证据整合力** (评价重点：对线索利用率，尤其是阴性/非线性结果)")
        st.markdown(
            '<div class="anchor-text">锚点参考：1-2分忽略关键数据；5分利用主要指标；9-10分挖掘隐性关联及非线性机理</div>',
            unsafe_allow_html=True)
        s3 = st.slider("评分_整合力", 0, 10, 0, label_visibility="collapsed")

        # 维度4
        st.markdown("**4. 转化洞察力与可行性** (评价重点：假说原创性与建议操作性)")
        st.markdown('<div class="anchor-text">锚点参考：1-2分纯复述废话；5分符合临床常规；9-10分具转化潜力的新假说</div>',
                    unsafe_allow_html=True)
        s4 = st.slider("评分_洞察力", 0, 10, 0, label_visibility="collapsed")

        # --- 第二部分 ---
        st.markdown('<div class="section-header">第二部分：与人类科学家相比本模型的综合水准 (1-10分)</div>',
                    unsafe_allow_html=True)
        st.markdown("""
        - **9-10 [卓越]**: 顶级期刊（NSC）讨论部分深度，捕捉人类易忽略逻辑。
        - **7-8 [优秀]**: 资深教授水平，逻辑完整，转化价值强。
        - **5-6 [合格]**: 博士/副教授水平，中规中矩，与原论文讨论吻合。
        - **3-4 [欠佳]**: 初级研究助理，简单归纳，无法处理复杂变量。
        - **1-2 [不合格]**: 严重“AI幻觉”或科学常识错误。
        """)
        s_human = st.slider("人类对比评分", 0, 10, 0, label_visibility="collapsed")

        # --- 第三部分 ---
        st.markdown('<div class="section-header">第三部分：定性评估</div>', unsafe_allow_html=True)

        consistency = st.selectbox("1. 一致性评价对比该领域公认逻辑，整体表现为：",
                                   ["高度一致（几乎无偏差）", "基本一致（逻辑成立，细节略有出入）",
                                    "存在偏差（存在关键逻辑断裂或误读）", "严重违背（存在基础科学性错误）"])

        highlights = st.text_area("2. 亮点分析：哪个环节展现了超越“人类科学家基准线”的洞察力？")
        risks = st.text_area("3. 局限与风险：是否存在过度推断或“一本正经胡说八道”？")
        value = st.text_area("4. 科学价值与转化建议：是否值得启动进一步实验或临床观察？")

        # --- 第四部分 ---
        st.markdown('<div class="section-header">第四部分：综合标定 (科学图灵测试)</div>', unsafe_allow_html=True)
        st.markdown("如果您在**完全双盲**的情况下阅读，是否倾向于认为这出自一位**资深科学家**之手？")
        turing_test = st.radio("倾向性：", ["肯定会", "可能会", "中立", "不太可能", "绝无可能"], horizontal=True)

        submit_button = st.form_submit_button("🚀 提交完整德尔菲评价表", use_container_width=True)

# --- 5. 保存逻辑 ---
if submit_button:
    if not expert_name:
        st.error("⚠️ 请输入专家姓名后再提交")
    elif (s1 + s2 + s3 + s4 + s_human) == 0:
        st.error("⚠️ 请完成所有评分项（分值不能全部为0）")
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
        st.success(f"【{current_doc_id}】评价已成功提交！")
        st.rerun()
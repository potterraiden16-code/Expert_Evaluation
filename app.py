import streamlit as st
import pandas as pd
import datetime
import os

# --- 1. 页面配置 ---
st.set_page_config(
    page_title="德尔菲法专家评价系统 v4.0",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义样式
st.markdown("""
    <style>
    .stSlider {padding-bottom: 20px;}
    .section-header {color: #1f77b4; border-bottom: 2px solid #1f77b4; padding-bottom: 5px; margin-top: 5px; margin-bottom: 15px; font-weight: bold; font-size: 1.1rem;}
    .status-box {padding: 12px; border-radius: 8px; margin-bottom: 15px; text-align: center; font-weight: bold; font-size: 0.9rem;}
    .pending {background-color: #fff3cd; color: #856404; border: 1px solid #ffeeba;}
    .completed {background-color: #d4edda; color: #155724; border: 1px solid #c3e6cb;}
    </style>
    """, unsafe_allow_html=True)


# --- 2. 数据处理与状态检查 ---
@st.cache_data
def load_data():
    try:
        return pd.read_excel("data_final_v3.xlsx")
    except Exception as e:
        st.error(f"无法读取数据文件: {e}")
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

# --- 3. 侧边栏 ---
with st.sidebar:
    st.title("👨‍🔬 评审工作台")
    expert_name = st.text_input("评审专家姓名：", placeholder="请输入您的姓名")
    st.divider()
    if not df.empty:
        raw_options = df['ID'].tolist()
        display_options = [f"{oid} {'✅' if oid in reviewed_ids else '⏳'}" for oid in raw_options]
        option_map = dict(zip(display_options, raw_options))
        selected_display = st.selectbox("选择文献：", options=display_options)
        current_doc_id = option_map[selected_display]
        row = df[df['ID'] == current_doc_id].iloc[0]
        st.write(f"总体进度: **{len(reviewed_ids)} / {len(raw_options)}**")

    st.divider()
    results_file = "expert_evaluations.csv"
    if os.path.exists(results_file):
        with open(results_file, "rb") as f:
            st.download_button("💾 下载评价汇总表", f, "delphi_results.csv", "text/csv", use_container_width=True)

# --- 4. 主界面：状态提示 ---
if current_doc_id in reviewed_ids:
    st.markdown(f'<div class="status-box completed">✅ 文献 {current_doc_id} 已评价（数据已保存）</div>',
                unsafe_allow_html=True)
else:
    st.markdown(f'<div class="status-box pending">⏳ 待处理：阅读内容后请切换至“量表”标签完成评分</div>',
                unsafe_allow_html=True)

# --- 5. 四标签沉浸式布局 ---
tab_evid, tab_ai, tab_author, tab_score = st.tabs(["📄 原始证据", "🧠 AI 推演", "📖 原文结论", "✍️ 评估量表"])

with tab_evid:
    st.text_area("e_c", value=row['Evidence'], height=600, disabled=True, label_visibility="collapsed")

with tab_ai:
    st.text_area("a_c", value=row['AI_Report'], height=600, disabled=True, label_visibility="collapsed")

with tab_author:
    st.markdown(row['Author_Conclusion'])

with tab_score:
    with st.form("delphi_full_form"):
        st.markdown('<div class="section-header">第一部分：定量评分 (1-10分)</div>', unsafe_allow_html=True)

        # 维度1
        st.write("1. **逻辑严密性与简约性**")
        s1 = st.slider("逻辑评分", 0, 10, 0, help="1-2分:逻辑断层; 5分:常规推导; 9-10分:细致且优雅简洁",
                       label_visibility="collapsed")

        # 维度2
        st.write("2. **生物学合理性与深度**")
        s2 = st.slider("合理性评分", 0, 10, 0, help="1-2分:基础常识错误; 5分:符合权威综述; 9-10分:调用准确前沿机制",
                       label_visibility="collapsed")

        # 维度3
        st.write("3. **证据整合力（含负向结果）**")
        s3 = st.slider("整合力评分", 0, 10, 0,
                       help="1-2分:忽略关键数据; 5分:合理解释显著指标; 9-10分:挖掘隐性关联及非线性机理",
                       label_visibility="collapsed")

        # 维度4
        st.write("4. **转化洞察力与可行性**")
        s4 = st.slider("洞察力评分", 0, 10, 0, help="1-2分:数据复述或废话; 5分:符合临床常规; 9-10分:具转化潜力新假说",
                       label_visibility="collapsed")

        st.markdown('<div class="section-header">第二部分：人类对比水准 (1-10分)</div>', unsafe_allow_html=True)
        s_human = st.slider("人机评分", 0, 10, 0,
                            help="9-10卓越(NSC级); 7-8优秀(资深专家); 5-6合格(博士级); 3-4欠佳; 1-2不合格",
                            label_visibility="collapsed")

        st.markdown('<div class="section-header">第三部分：定性评估</div>', unsafe_allow_html=True)
        consistency = st.selectbox("1. 一致性评价：", ["高度一致", "基本一致", "存在偏差", "严重违背"])
        highlights = st.text_area("2. 亮点分析（超越人类基准线的洞察）：")
        risks = st.text_area("3. 局限与风险（幻觉检测）：")
        value = st.text_area("4. 科学价值与建议：")

        st.markdown('<div class="section-header">第四部分：科学图灵测试</div>', unsafe_allow_html=True)
        turing_test = st.radio("是否倾向于认为这出自深耕该领域10年以上的资深科学家？",
                               ["肯定会", "可能会", "中立", "不太可能", "绝无可能"], horizontal=True)

        # 修复此处的潜在断行错误
        submit_button = st.form_submit_button("🚀 提交完整德尔菲评价表", use_container_width=True)

# --- 6. 保存逻辑 ---
if submit_button:
    if not expert_name:
        st.error("⚠️ 请在左侧填写姓名")
    elif (s1 + s2 + s3 + s4 + s_human) == 0:
        st.error("⚠️ 评分不能全为0")
    else:
        new_entry = {
            "专家": expert_name, "文献ID": current_doc_id,
            "提交时间": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
            "1_逻辑": s1, "2_合理性": s2, "3_整合力": s3, "4_转化洞察": s4,
            "人机水准": s_human, "一致性": consistency, "亮点": highlights,
            "风险": risks, "价值": value, "图灵测试": turing_test
        }
        rdf = pd.DataFrame([new_entry])
        if not os.path.isfile(results_file):
            rdf.to_csv(results_file, index=False, encoding='utf-8-sig')
        else:
            rdf.to_csv(results_file, mode='a', header=False, index=False, encoding='utf-8-sig')

        st.balloons()
        st.cache_data.clear()
        st.success("✅ 提交成功！")
        st.rerun()
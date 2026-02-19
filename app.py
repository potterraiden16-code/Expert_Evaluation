import streamlit as st
import pandas as pd
import datetime
import os

# --- 1. 页面配置：增加隐藏菜单的逻辑 ---
st.set_page_config(
    page_title="德尔菲法专家评价系统 v4.2",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义 CSS：除了美化，还隐藏了 Streamlit 官方的各种标签
st.markdown("""
    <style>
    /* 隐藏右上角的菜单按钮和底部的 Made with Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    .stSlider {padding-bottom: 20px;}
    .section-header {color: #1f77b4; border-bottom: 2px solid #1f77b4; padding-bottom: 5px; margin-top: 5px; margin-bottom: 15px; font-weight: bold; font-size: 1.1rem;}
    .status-box {padding: 12px; border-radius: 8px; margin-bottom: 15px; text-align: center; font-weight: bold; font-size: 0.9rem;}
    .pending {background-color: #fff3cd; color: #856404; border: 1px solid #ffeeba;}
    .completed {background-color: #d4edda; color: #155724; border: 1px solid #c3e6cb;}
    .anchor-box {background-color: #f9f9f9; padding: 10px; border-radius: 5px; border-left: 4px solid #1f77b4; font-size: 0.85rem; margin-bottom: 5px;}
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
results_file = "expert_evaluations.csv"

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
    if os.path.exists(results_file):
        with open(results_file, "rb") as f:
            st.download_button("💾 下载评价汇总表", f, "delphi_results.csv", "text/csv", use_container_width=True)

# --- 4. 主界面：状态提示 ---
if current_doc_id in reviewed_ids:
    st.markdown(f'<div class="status-box completed">✅ 文献 {current_doc_id} 已评价（数据已保存）</div>', unsafe_allow_html=True)
else:
    st.markdown(f'<div class="status-box pending">⏳ 待处理：阅读内容后请切换至“评估量表”标签完成评分</div>', unsafe_allow_html=True)

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

        st.write("1. **逻辑严密性与简约性**")
        st.markdown('<div class="anchor-box"><b>锚点：</b>1-2分逻辑断层；5分常规推导合理；9-10分链条极度细致优雅且路径简洁。</div>', unsafe_allow_html=True)
        s1 = st.slider("维度1评分", 0, 10, 0, label_visibility="collapsed")

        st.write("2. **生物学合理性与深度**")
        st.markdown('<div class="anchor-box"><b>锚点：</b>1-2分基础常识错误（AI幻觉）；5分符合主流权威描述；9-10分准确调用前沿机制，深度极高。</div>', unsafe_allow_html=True)
        s2 = st.slider("维度2评分", 0, 10, 0, label_visibility="collapsed")

        st.write("3. **证据整合力（含负向结果）**")
        st.markdown('<div class="anchor-box"><b>锚点：</b>1-2分忽略关键数据；5分利用主要指标合理解释；9-10分挖掘隐性关联，对复杂数据给出自洽推论。</div>', unsafe_allow_html=True)
        s3 = st.slider("维度3评分", 0, 10, 0, label_visibility="collapsed")

        st.write("4. **转化洞察力与可行性**")
        st.markdown('<div class="anchor-box"><b>锚点：</b>1-2分纯数据复述（废话）；5分建议符合临床常规；9-10分提供具转化潜力的新假说且具体。</div>', unsafe_allow_html=True)
        s4 = st.slider("维度4评分", 0, 10, 0, label_visibility="collapsed")

        st.markdown('<div class="section-header">第二部分：人类对比水准 (1-10分)</div>', unsafe_allow_html=True)
        st.markdown('<div class="anchor-box">9-10卓越(NSC级讨论深度)；7-8.9优秀(资深教授)；5-6.9合格(博士/副教授)；3-4.9欠佳；1-2.9不合格。</div>', unsafe_allow_html=True)
        s_human = st.slider("人机对比评分", 0.0, 10.0, 0.0, step=0.1, label_visibility="collapsed")

        st.markdown('<div class="section-header">第三部分：定性评估</div>', unsafe_allow_html=True)
        consistency = st.selectbox("1. 一致性评价：", ["高度一致", "基本一致", "存在偏差", "严重违背"])
        highlights = st.text_area("2. 亮点分析：哪个环节展现了超越人类基准线的洞察力？")
        risks = st.text_area("3. 局限与风险：是否存在幻觉、过度推断或胡说八道？")
        value = st.text_area("4. 科学价值与建议：是否值得启动进一步验证？")

        st.markdown('<div class="section-header">第四部分：科学图灵测试</div>', unsafe_allow_html=True)
        turing_test = st.radio("您是否认为此推论出自深耕该领域10年以上的资深科学家之手？", ["肯定会", "可能会", "中立", "不太可能", "绝无可能"], horizontal=True)

        submit_button = st.form_submit_button("🚀 提交完整德尔菲评价表", use_container_width=True)

# --- 6. 保存逻辑 ---
if submit_button:
    if not expert_name:
        st.error("⚠️ 请在左侧填写姓名")
    elif (s1 + s2 + s3 + s4 + s_human) == 0:
        st.error("⚠️ 评分不能全为0")
    else:
        new_entry = {
            "专家": expert_name, "文献ID": current_doc_id, "提交时间": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
            "1_逻辑": s1, "2_合理性": s2, "3_整合力": s3, "4_转化洞察": s4,
            "人机水准": s_human, "一致性": consistency, "亮点": highlights,
            "风险": risks, "价值": value, "图灵测试": turing_test
        }
        rdf = pd.DataFrame([new_entry])
        try:
            if not os.path.isfile(results_file):
                rdf.to_csv(results_file, index=False, encoding='utf-8-sig')
            else:
                rdf.to_csv(results_file, mode='a', header=False, index=False, encoding='utf-8-sig')
            st.balloons()
            st.cache_data.clear()
            st.success("✅ 提交成功！")
            st.rerun()
        except Exception as e:
            st.error(f"保存失败：{e}")

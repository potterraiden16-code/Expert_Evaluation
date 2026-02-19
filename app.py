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

        # --- 维度 1 ---
        st.write("1. **逻辑严密性与简约性**")
        # 直接显示的精简版标准（让专家一眼看到）
        st.caption("⚓ 1-2: 逻辑断层 | 5: 常规推导合理 | 9-10: 链条细致且简洁优雅")
        s1 = st.slider("逻辑评分", 0, 10, 0, help="""
        【评价重点】：因果链条的闭环程度与逻辑效率
        【完整标准】：
        1-2分：存在逻辑断层、循环论证或路径过于冗长。
        5分：逻辑通顺，因果关系合理，符合常规科研推导。
        9-10分：链条极度细致且优雅，无任何因果跳跃，且路径简洁（无冗余推导）。
        """, label_visibility="collapsed")

        # --- 维度 2 ---
        st.write("2. **生物学合理性与深度**")
        st.caption("⚓ 1-2: 基础常识错误 | 5: 符合权威描述 | 9-10: 跨学科机制深度极高")
        s2 = st.slider("合理性评分", 0, 10, 0, help="""
        【评价重点】：知识准确性及是否包含“幻觉”
        【完整标准】：
        1-2分：出现基础常识错误或生化过程误述（即AI幻觉）。
        5分：符合主流教科书及权威综述的病理生理学描述。
        9-10分：调用了准确的前沿/跨学科机制（如生物钟受体亚型等），深度极高。
        """, label_visibility="collapsed")

        # --- 维度 3 ---
        st.write("3. **证据整合力（含负向结果）**")
        st.caption("⚓ 1-2: 忽略关键数据 | 5: 显著指标合理解释 | 9-10: 挖掘隐性/非线性关联")
        s3 = st.slider("整合力评分", 0, 10, 0, help="""
        【评价重点】：对输入线索的利用率，尤其是对阴性/非线性结果的解释
        【完整标准】：
        1-2分：忽略关键数据，尤其是忽略了阴性结果（如出血性中风无关联）。
        5分：能利用主要指标，对显著性结果进行合理解释。
        9-10分：挖掘出隐性关联，能对“无交互作用”或“非线性”等复杂数据给出高度自洽的机理推论。
        """, label_visibility="collapsed")

        # --- 维度 4 ---
        st.write("4. **转化洞察力与可行性**")
        st.caption("⚓ 1-2: 纯复述/废话 | 5: 符合临床常规 | 9-10: 具挑战性新假说且极其具体")
        s4 = st.slider("洞察力评分", 0, 10, 0, help="""
        【评价重点】：假说的原创性及干预建议的具体操作性
        【完整标准】：
        1-2分：纯属数据复述，或给出的建议是“正确的废话”。
        5分：解释合理，建议符合临床常规方案。
        9-10分：提供具有挑战性的新假说，建议极其具体且具转化潜力（如具体的照明波长）。
        """, label_visibility="collapsed")

        # --- 第二部分：人类对比 ---
        st.markdown('<div class="section-header">第二部分：人类对比水准 (1-10分)</div>', unsafe_allow_html=True)
        st.caption("⚓ 9-10: NSC级卓越 | 7-8: 资深教授 | 5-6: 博士/副教授 | 3-4: 欠佳 | 1-2: 不合格")
        s_human = st.slider("人机评分", 0, 10, 0, help="""
        9.0-10 [卓越]: 顶级期刊(NSC)讨论深度，发现人类易忽略逻辑。
        7.0-8.9 [优秀]: 资深教授水平，具很强转化价值。
        5.0-6.9 [合格]: 博士/副教授水平，逻辑自洽，创新中规中矩。
        3.0-4.9 [欠佳]: 初级研究助理，无法处理复杂多变量关系。
        1.0-2.9 [不合格]: 存在严重AI幻觉或科学常识错误。
        """, label_visibility="collapsed")

        # ... 后续代码保持不变 ...

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
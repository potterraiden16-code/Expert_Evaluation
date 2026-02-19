import streamlit as st
import pandas as pd
import datetime
import os

# --- 1. 页面配置 ---
st.set_page_config(
    page_title="德尔菲法专家评价系统 v4.1",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义样式：增强科研质感
st.markdown("""
    <style>
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
        # 确保文件名 data_final_v3.xlsx 正确
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
        st.markdown('<div class="section-header">第一部分：具体科研能力维度的定量评分 (1-10分)</div>', unsafe_allow_html=True)

        # --- 维度 1 ---
        st.write("1. **逻辑严密性与简约性** (评价重点：因果链条的闭环程度与逻辑效率)")
        st.markdown("""
        <div class="anchor-box">
        <b>评分标准描述（参考锚点）：</b><br>
        • 1-2分：存在逻辑断层、循环论证或路径过于冗长。<br>
        • 5分：逻辑通顺，因果关系合理，符合常规科研推导。<br>
        • 9-10分：链条极度细致且优雅，无任何因果跳跃，且路径简洁（无冗余推导）。
        </div>
        """, unsafe_allow_html=True)
        s1 = st.slider("维度1评分", 0, 10, 0, label_visibility="collapsed")

        # --- 维度 2 ---
        st.write("2. **生物学合理性与深度** (评价重点：知识准确性及是否包含“幻觉”)")
        st.markdown("""
        <div class="anchor-box">
        <b>评分标准描述（参考锚点）：</b><br>
        • 1-2分：出现基础常识错误或生化过程误述（即AI幻觉）。<br>
        • 5分：符合主流教科书及权威综述的病理生理学描述。<br>
        • 9-10分：调用了准确的前沿/跨学科机制（如生物钟受体亚型、表观遗传等），深度极高。
        </div>
        """, unsafe_allow_html=True)
        s2 = st.slider("维度2评分", 0, 10, 0, label_visibility="collapsed")

        # --- 维度 3 ---
        st.write("3. **证据整合力（含负向结果）** (评价重点：对输入线索的利用率，尤其是对阴性/非线性结果的解释)")
        st.markdown("""
        <div class="anchor-box">
        <b>评分标准描述（参考锚点）：</b><br>
        • 1-2分：忽略关键数据，尤其是忽略了阴性结果（如出血性中风无关联）。<br>
        • 5分：能利用主要指标，对显著性结果进行合理解释。<br>
        • 9-10分：挖掘出隐性关联，能对“无交互作用”或“非线性”等复杂数据给出高度自洽的机理推论。
        </div>
        """, unsafe_allow_html=True)
        s3 = st.slider("维度3评分", 0, 10, 0, label_visibility="collapsed")

        # --- 维度 4 ---
        st.write("4. **转化洞察力与可行性** (评价重点：假说的原创性及干预建议的具体操作性)")
        st.markdown("""
        <div class="anchor-box">
        <b>评分标准描述（参考锚点）：</b><br>
        • 1-2分：纯属数据复述，或给出的建议是“正确的废话”（如加强教育）。<br>
        • 5分：解释合理，建议符合临床常规方案。<br>
        • 9-10分：提供具有挑战性的新假说，建议极其具体且具转化潜力（如具体的照明波长、精准的暴露窗口期）。
        </div>
        """, unsafe_allow_html=True)
        s4 = st.slider("维度4评分", 0, 10, 0, label_visibility="collapsed")

        # --- 第二部分 ---
        st.markdown('<div class="section-header">第二部分：您觉得与人类科学家相比这个模型处于什么水准 (1-10分)</div>', unsafe_allow_html=True)
        st.markdown("""
        <div class="anchor-box">
        • <b>9.0 - 10 卓越 (Exceptional)</b>：推论具备顶级期刊（Nature/Science/Cell）讨论部分的深度。能够处理极复杂的变量关系，发现人类专家易忽略的细微逻辑。<br>
        • <b>7.0 - 8.9 优秀 (Senior Expert)</b>：达到资深教授水平。逻辑链条完整，能敏锐捕捉数据中的特异性，给出的建议具有很强的转化医学价值。<br>
        • <b>5.0 - 6.9 合格 (Competent)</b>：达到人类博士/副教授水平。知识准确，逻辑自洽，推论结论与原论文吻合，创新性中规中矩。<br>
        • <b>3.0 - 4.9 欠佳 (Developing)</b>：相当于初级研究助理。能进行简单归纳，但无法处理复杂多变量关系，知识调用存在碎片化。<br>
        • <b>1.0 - 2.9 不合格 (Flawed)</b>：存在严重“AI幻觉”或科学常识错误。
        </div>
        """, unsafe_allow_html=True)
        s_human = st.slider("人机对比评分", 0.0, 10.0, 0.0, step=0.1, label_visibility="collapsed")

        # --- 第三部分 ---
        st.markdown('<div class="section-header">第三部分：定性评估</div>', unsafe_allow_html=True)
        consistency = st.selectbox("1. 一致性评价（对比该领域公认科学逻辑，AI推论整体表现为）：", 
                                  ["高度一致（几乎无偏差）", "基本一致（逻辑成立，细节略有出入）", 
                                   "存在偏差（存在关键逻辑断裂或误读）", "严重违背（存在基础科学性错误）"])
        
        highlights = st.text_area("2. 亮点分析（请说明AI在推演过程中，哪个环节展现了超越人类基准线的洞察力？如认为没有可不答）")
        risks = st.text_area("3. 局限与风险（含幻觉检测：请指出AI是否存在过度推断、忽略现实干扰或胡说八道环节？）")
        value = st.text_area("4. 科学价值与转化建议（是否值得启动进一步动物实验验证、临床观察或政策试点？）")

        # --- 第四部分 ---
        st.markdown('<div class="section-header">第四部分：综合标定 (科学图灵测试倾向性提问)</div>', unsafe_allow_html=True)
        st.write("如果您在完全双盲（不知作者身份）的情况下阅读此推论，您是否会倾向于认为这出自一位深耕该领域 10 年以上的资深科学家之手？")
        turing_test = st.radio("选项：", ["肯定会", "可能会", "中立", "不太可能", "绝无可能"], horizontal=True, label_visibility="collapsed")

        submit_button = st.form_submit_button("🚀 提交完整德尔菲评价表", use_container_width=True)

# --- 6. 保存逻辑 ---
if submit_button:
    if not expert_name:
        st.error("⚠️ 请在左侧填写姓名后再提交。")
    elif (s1 + s2 + s3 + s4 + s_human) == 0:
        st.error("⚠️ 评分项不能全为0，请完成定量评分。")
    else:
        new_entry = {
            "专家": expert_name, 
            "文献ID": current_doc_id,
            "提交时间": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
            "1_逻辑严密性": s1, 
            "2_生物学合理性": s2, 
            "3_证据整合力": s3, 
            "4_转化洞察力": s4,
            "人机水准评分": s_human, 
            "一致性评价": consistency, 
            "亮点分析": highlights,
            "局限风险分析": risks, 
            "科学价值建议": value, 
            "图灵测试倾向": turing_test
        }
        rdf = pd.DataFrame([new_entry])
        try:
            if not os.path.isfile(results_file):
                rdf.to_csv(results_file, index=False, encoding='utf-8-sig')
            else:
                rdf.to_csv(results_file, mode='a', header=False, index=False, encoding='utf-8-sig')
            
            st.balloons()
            st.cache_data.clear()
            st.success("✅ 评价提交成功！系统已更新状态。")
            st.rerun()
        except Exception as e:
            st.error(f"数据保存失败（可能文件被占用）：{e}")

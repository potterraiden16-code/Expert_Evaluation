import streamlit as st
import pandas as pd
import datetime
import os
import time

# --- 1. 页面配置 ---
st.set_page_config(
    page_title="德尔斐法专家评价系统 v4.2",
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
    .anchor-box {background-color: #f9f9f9; padding: 10px; border-radius: 5px; border-left: 4px solid #1f77b4; font-size: 0.85rem; margin-bottom: 5px;}
    </style>
    """, unsafe_allow_html=True)

# --- 2. 数据处理与存储逻辑 ---
@st.cache_data
def load_data():
    try:
        return pd.read_excel("data_final_v3.xlsx")
    except Exception as e:
        st.error(f"无法读取数据文件: {e}")
        return pd.DataFrame()

def get_expert_dir(name):
    if not name or name.strip() == "":
        return None
    safe_name = "".join([c for c in name if c.isalnum() or c in (" ", "_")]).strip()
    path = f"results_{safe_name}"
    if not os.path.exists(path):
        os.makedirs(path)
    return path

def get_reviewed_ids(expert_name):
    path = get_expert_dir(expert_name)
    if not path:
        return []
    reviewed = []
    if os.path.exists(path):
        for file in os.listdir(path):
            if file.endswith(".csv"):
                # 提取文件名中第一个下划线前的内容作为ID
                doc_id = file.split("_")[0]
                reviewed.append(doc_id)
    return list(set(reviewed))

df = load_data()

# 初始化 Session State 用于锁定当前选中文献
if 'current_index' not in st.session_state:
    st.session_state.current_index = 0

# --- 3. 侧边栏 ---
with st.sidebar:
    st.title("👨‍🔬 评审工作台")
    expert_name = st.text_input("评审专家姓名：", placeholder="请输入您的姓名")
    
    reviewed_ids = get_reviewed_ids(expert_name)
    
    st.divider()
    current_doc_id = None
    row = None
    
    if not df.empty:
        raw_options = df['ID'].astype(str).tolist()
        display_options = [f"{oid} {'✅' if oid in reviewed_ids else '⏳'}" for oid in raw_options]
        
        # 使用 index 参数来锁定当前位置，防止重置
        selected_display = st.selectbox(
            "选择文献：", 
            options=display_options, 
            index=st.session_state.current_index,
            key="doc_selector"
        )
        
        # 更新 session_state
        new_index = display_options.index(selected_display)
        st.session_state.current_index = new_index
        
        current_doc_id = raw_options[new_index]
        row = df.iloc[new_index]
        st.write(f"您的评审进度: **{len(reviewed_ids)} / {len(raw_options)}**")

    st.divider()
    expert_path = get_expert_dir(expert_name)
    if expert_path:
        files = [os.path.join(expert_path, f) for f in os.listdir(expert_path) if f.endswith(".csv")]
        if files:
            # 合并数据并解决乱码
            data_list = [pd.read_csv(f) for f in files]
            expert_all_data = pd.concat(data_list)
            # 使用 utf-8-sig 防止 Excel 乱码
            csv_buffer = expert_all_data.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label=f"💾 下载您的评价汇总",
                data=csv_buffer,
                file_name=f"delphi_{expert_name}.csv",
                mime="text/csv",
                use_container_width=True
            )

# --- 4. 主界面：状态提示 ---
if current_doc_id and str(current_doc_id) in reviewed_ids:
    st.markdown(f'<div class="status-box completed">✅ 文献 {current_doc_id} 您已评价（数据已保存在专属目录）</div>',
                unsafe_allow_html=True)
else:
    st.markdown(f'<div class="status-box pending">⏳ 待处理：请阅读原始证据和AI推理结果后，对照原文结论，填写“评估量表”标签完成评分</div>',
                unsafe_allow_html=True)

# --- 5. 四标签沉浸式布局 ---
if row is not None:
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
            
            st.write("1. **逻辑严密性与简约性**")
            st.markdown('<div class="anchor-box">评分参考：1-2分逻辑断层；5分逻辑通顺；9-10分链条细致优雅且简洁。</div>', unsafe_allow_html=True)
            s1 = st.slider("维度1评分", 0, 10, 5, label_visibility="collapsed")

            st.write("2. **生物学合理性与深度**")
            st.markdown('<div class="anchor-box">评分参考：1-2分基础常识错误；5分符合主流描述；9-10分调用准确前沿机制。</div>', unsafe_allow_html=True)
            s2 = st.slider("维度2评分", 0, 10, 5, label_visibility="collapsed")

            st.write("3. **证据整合力（含负向结果）**")
            st.markdown('<div class="anchor-box">评分参考：1-2分忽略关键数据；5分能利用主要指标；9-10分挖掘隐性关联及非线性推论。</div>', unsafe_allow_html=True)
            s3 = st.slider("维度3评分", 0, 10, 5, label_visibility="collapsed")

            st.write("4. **转化洞察力与可行性**")
            st.markdown('<div class="anchor-box">评分参考：1-2分数据复述；5分符合临床常规；9-10分提供具挑战性的新假说及具体建议。</div>', unsafe_allow_html=True)
            s4 = st.slider("维度4评分", 0, 10, 5, label_visibility="collapsed")

            st.markdown('<div class="section-header">第二部分：人机对比评分 (0.0 - 10.0分)</div>', unsafe_allow_html=True)
            s_human = st.slider("人机对比评分", 0.0, 10.0, 5.0, step=0.1, label_visibility="collapsed")

            st.markdown('<div class="section-header">第三部分：定性评估</div>', unsafe_allow_html=True)
            consistency = st.selectbox("1. 一致性评价：", ["高度一致（几乎无偏差）", "基本一致（逻辑成立，细节略有出入）", "存在偏差", "严重违背"])
            highlights = st.text_area("2. 亮点分析")
            risks = st.text_area("3. 局限与风险")
            value = st.text_area("4. 科学价值与转化建议")

            st.markdown('<div class="section-header">第四部分：综合标定</div>', unsafe_allow_html=True)
            st.write("您是否会倾向于认为这出自一位深耕该领域 10 年以上的资深科学家之手？")
            turing_test = st.radio("选项：", ["肯定会", "可能会", "中立", "不太可能", "绝无可能"], horizontal=True, label_visibility="collapsed")

            submit_button = st.form_submit_button("🚀 提交完整德尔菲评价表", use_container_width=True)

    # --- 6. 保存逻辑 ---
    if submit_button:
        if not expert_name or expert_name.strip() == "":
            st.error("⚠️ 请在左侧填写姓名后再提交。")
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
            
            try:
                expert_dir = get_expert_dir(expert_name)
                # 使用时间戳文件名
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{current_doc_id}_{timestamp}.csv"
                filepath = os.path.join(expert_dir, filename)
                
                pd.DataFrame([new_entry]).to_csv(filepath, index=False, encoding='utf-8-sig')

                st.balloons()
                st.success(f"✅ 提交成功！")
                
                # 清除缓存强制更新状态，但保持页面索引
                st.cache_data.clear()
                time.sleep(1)
                st.rerun()
            except Exception as e:
                st.error(f"保存失败：{e}")
else:
    st.info("💡 请在左侧输入姓名并选择文献。")

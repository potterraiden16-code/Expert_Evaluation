import streamlit as st
import pandas as pd
import datetime
import os
import time
import io

# --- 1. 页面配置 ---
st.set_page_config(
    page_title="德尔斐法专家评价系统 v4.1",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义样式：完全保留原始样式
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
        return pd.read_excel("data_final_v3.xlsx")
    except Exception as e:
        st.error(f"无法读取数据文件: {e}")
        return pd.DataFrame()

def get_expert_dir(name):
    if not name or name.strip() == "": return None
    safe_name = "".join([c for c in name if c.isalnum() or c in (" ", "_")]).strip()
    path = f"results_{safe_name}"
    if not os.path.exists(path): os.makedirs(path)
    return path

def get_reviewed_ids(expert_name):
    path = get_expert_dir(expert_name)
    if not path: return []
    reviewed = []
    if os.path.exists(path):
        for file in os.listdir(path):
            if file.endswith(".csv"):
                reviewed.append(file.split("_")[0])
    return list(set(reviewed))

df = load_data()

# 初始化 Session State
if 'current_index' not in st.session_state:
    st.session_state.current_index = 0

# --- 3. 核心修改：切换逻辑回调函数 ---
def on_doc_change():
    # 从 selectbox 的 key 中获取新值并同步到索引
    new_display_value = st.session_state.doc_selector
    st.session_state.current_index = st.session_state.all_display_options.index(new_display_value)

# --- 4. 侧边栏 ---
with st.sidebar:
    st.title("👨‍🔬 评审工作台")
    expert_name = st.text_input("评审专家姓名：", placeholder="请输入您的姓名")
    
    reviewed_ids = get_reviewed_ids(expert_name)

    st.divider()
    if not df.empty:
        raw_options = df['ID'].astype(str).tolist()
        # 将选项存入 session_state 供回调函数比对
        st.session_state.all_display_options = [f"{oid} {'✅' if oid in reviewed_ids else '⏳'}" for oid in raw_options]
        
        # 使用 on_change 回调函数确保切换即时生效
        selected_display = st.selectbox(
            "选择文献：", 
            options=st.session_state.all_display_options, 
            index=st.session_state.current_index,
            key="doc_selector",
            on_change=on_doc_change
        )
        
        current_doc_id = raw_options[st.session_state.current_index]
        row = df.iloc[st.session_state.current_index]
        st.write(f"总体进度: **{len(reviewed_ids)} / {len(raw_options)}**")

    st.divider()
    expert_path = get_expert_dir(expert_name)
    if expert_path:
        files = [os.path.join(expert_path, f) for f in os.listdir(expert_path) if f.endswith(".csv")]
        if files:
            combined_df = pd.concat([pd.read_csv(f) for f in files])
            output = io.BytesIO()
            combined_df.to_csv(output, index=False, encoding='utf-8-sig')
            processed_data = output.getvalue()
            
            st.download_button(
                label="💾 下载评价汇总表",
                data=processed_data,
                file_name=f"delphi_results_{expert_name}.csv",
                mime="text/csv",
                use_container_width=True
            )

# --- 5. 主界面：状态提示 ---
if str(current_doc_id) in reviewed_ids:
    st.markdown(f'<div class="status-box completed">✅ 文献 {current_doc_id} 已评价（数据已保存）</div>',
                unsafe_allow_html=True)
else:
    st.markdown(f'<div class="status-box pending">⏳ 待处理：请阅读原始证据和AI推理结果后，对照原文结论，填写“评估量表”标签完成评分</div>',
                unsafe_allow_html=True)

# --- 6. 四标签沉浸式布局 ---
tab_evid, tab_ai, tab_author, tab_score = st.tabs(["📄 原始证据", "🧠 AI 推演", "📖 原文结论", "✍️ 评估量表"])

with tab_evid:
    st.text_area("e_c", value=row['Evidence'], height=600, disabled=True, label_visibility="collapsed")

with tab_ai:
    st.text_area("a_c", value=row['AI_Report'], height=600, disabled=True, label_visibility="collapsed")

with tab_author:
    st.markdown(row['Author_Conclusion'])

with tab_score:
    with st.form("delphi_full_form"):
        st.markdown('<div class="section-header">第一部分：具体科研能力维度的定量评分 (1-10分)</div>',
                    unsafe_allow_html=True)

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

        st.write("4. **转化洞察力与可行性** (评价重点：假说的原创性及干预建议的具体操作性)")
        st.markdown("""
        <div class="anchor-box">
        <b>评分标准描述（参考锚点）：</b><br>
        • 1-2分：纯属数据复述，或给出的建议是“正确的废话”（如加强教育）。<br>
        • 5分：解释合理，建议符合临床常规方案。<br>
        • 9-10分：提供具有挑战性的新假说，建议极其具体且具转化潜力（如具体的照明波长、精准的暴露窗口期）。
        </div>
        """, unsafe

import streamlit as st
import pandas as pd
import datetime
import os

# --- 1. 页面配置 ---
st.set_page_config(
    page_title="表型大模型专家评价系统",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义 CSS 优化移动端间距和文本排版
st.markdown("""
    <style>
    .main .block-container {padding-top: 2rem;}
    .stTextArea textarea {font-family: 'Courier New', Courier, monospace; font-size: 14px !important;}
    div[data-testid="stExpander"] div[role="button"] p {font-weight: bold; color: #1f77b4;}
    </style>
    """, unsafe_allow_html=True)


# --- 2. 数据加载函数 ---
@st.cache_data
def load_data():
    # 确保 data_final_v3.xlsx 已上传至 GitHub 仓库根目录
    try:
        df = pd.read_excel("data_final_v3.xlsx")
        return df
    except Exception as e:
        st.error(f"无法读取数据文件: {e}")
        return pd.DataFrame()


df = load_data()

# --- 3. 侧边栏：专家信息与全局操作 ---
with st.sidebar:
    st.title("👨‍🔬 评审工作台")
    expert_name = st.text_input("评审专家姓名：", placeholder="请输入您的姓名")

    st.divider()

    if not df.empty:
        doc_options = df['ID'].tolist()
        current_doc_id = st.selectbox("选择待评审文献：", options=doc_options)
        row = df[df['ID'] == current_doc_id].iloc[0]

        # 进度显示
        progress = (doc_options.index(current_doc_id) + 1) / len(doc_options)
        st.progress(progress)
        st.caption(f"进度：{doc_options.index(current_doc_id) + 1} / {len(doc_options)}")
    else:
        st.warning("请上传数据文件后再操作。")
        st.stop()

    st.divider()

    # 评分数据下载逻辑
    st.markdown("### 📥 数据导出")
    results_file = "expert_evaluations.csv"
    if os.path.exists(results_file):
        with open(results_file, "rb") as f:
            st.download_button(
                label="💾 下载已保存的评价汇总表",
                data=f,
                file_name=f"evaluation_results_{datetime.datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True
            )
        st.caption("提示：完成所有评价后请下载并发送回研究员。")
    else:
        st.info("尚未有提交记录，提交首篇评价后即可下载。")

# --- 4. 主界面布局：响应式标签页 ---
st.title(f"🔍 {row['ID']} 评估任务")
st.markdown(f"**当前处理：** `{row['Title']}`")

# 使用 Tabs 替代 Columns 以完美适配移动端
tab_evid, tab_ai, tab_score = st.tabs(["📄 原始证据", "🧠 AI推演报告", "⭐ 专家评分"])

with tab_evid:
    st.markdown("#### 📚 原始证据池 (Evidence)")
    # 使用 text_area 并禁用编辑，以获得更好的移动端滚动体验
    st.text_area(
        label="证据池内容",
        value=row['Evidence'],
        height=500,
        disabled=True,
        label_visibility="collapsed"
    )

with tab_ai:
    st.markdown("#### 🤖 大模型推演报告 (AI Report)")
    st.success("模型生成的逻辑推演报告：")
    st.text_area(
        label="AI报告内容",
        value=row['AI_Report'],
        height=400,
        disabled=True,
        label_visibility="collapsed"
    )

    # 将作者结论放在折叠框中作为对照
    with st.expander("📖 查看原作者结论 (Benchmark)", expanded=False):
        st.markdown(row['Author_Conclusion'])

with tab_score:
    st.markdown("#### ✍️ 评价指标评分")
    st.caption("请根据阅读内容，在下方滑动滑块进行打分。")

    with st.form("score_form"):
        s1 = st.slider("1. 逻辑严密性", 1, 10, 5, help="推演链条是否严丝合缝，是否存在逻辑断层。")
        s2 = st.slider("2. 生物学合理性", 1, 10, 5, help="推论是否符合生物学第一性原理，有无科学常识性幻觉。")
        s3 = st.slider("3. 证据整合力", 1, 10, 5, help="模型对原始文献中复杂、冲突或细微数据的提取和整合程度。")
        s4 = st.slider("4. 转化洞察力", 1, 10, 5, help="推论给出的未来研究建议或转化医学假说是否有价值。")

        st.divider()

        turing = st.radio(
            "🕵️ 科学图灵测试：您认为此推论更有可能出自？",
            ["资深科学家 (Senior Scientist)", "初级研究员 (Junior Researcher)", "AI模型 (AI Model)"],
            horizontal=True
        )

        feedback = st.text_area("综合评语与洞察（选填）", placeholder="请输入您的评价或针对AI推论的改进建议...")

        # 针对移动端优化按钮宽度
        submit_button = st.form_submit_button("🚀 提交本篇评估", use_container_width=True)

# --- 5. 评分保存逻辑 ---
if submit_button:
    if not expert_name:
        st.error("⚠️ 请在左侧边栏填写您的姓名后再提交评价。")
        st.sidebar.warning("请输入姓名")
    else:
        # 封装当前评价
        result_entry = {
            "专家": expert_name,
            "文献ID": current_doc_id,
            "提交时间": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
            "1_逻辑严密性": s1,
            "2_生物学合理性": s2,
            "3_证据整合力": s3,
            "4_转化洞察力": s4,
            "图灵测试猜想": turing,
            "评语": feedback
        }

        results_df = pd.DataFrame([result_entry])

        # 增量保存至服务器本地 CSV
        try:
            if not os.path.isfile(results_file):
                results_df.to_csv(results_file, index=False, encoding='utf-8-sig')
            else:
                results_df.to_csv(results_file, mode='a', header=False, index=False, encoding='utf-8-sig')

            st.balloons()
            st.success(f"✅ 【{current_doc_id}】评价提交成功！")

            # 强制刷新以更新侧边栏下载按钮状态
            st.rerun()

        except Exception as e:
            st.error(f"保存失败，请检查服务器权限: {e}")

# 页脚
st.divider()
st.caption("表型大模型科研评价系统 v2.0 | 基于响应式 UI 框架构建")
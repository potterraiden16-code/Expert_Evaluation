import streamlit as st
import pandas as pd
import datetime
import os

# --- 页面配置 ---
st.set_page_config(page_title="表型大模型专家评价系统", layout="wide")


# --- 加载提取好的数据 ---
@st.cache_data
def load_data():
    df = pd.read_excel("data_final_v3.xlsx")
    return df


df = load_data()

# --- 侧边栏：进度与说明 ---
with st.sidebar:
    st.title("👨‍🔬 评审说明")
    expert_name = st.text_input("评审专家姓名：", placeholder="请输入您的姓名")
    st.info("""
    **评分标准 (1-10分):**
    - 5分：博士/副教授水平
    - 9分+：顶尖科学家水平
    """)

    st.divider()
    # 进度条
    doc_options = df['ID'].tolist()
    current_doc_id = st.selectbox("选择评审文献：", options=doc_options)

    # 查找当前行数据
    row = df[df['ID'] == current_doc_id].iloc[0]

# --- 主界面布局 ---
st.title(f"🔍 {row['ID']} 评估任务")
st.subheader(row['Title'])

# 创建三栏布局
col1, col2, col3 = st.columns([2, 2, 1.5])

with col1:
    st.markdown("### 📚 原始证据池 (Evidence)")
    # 使用 container 保持排版并支持内部滚动
    with st.container(height=600):
        st.text(row['Evidence'])

with col2:
    st.markdown("### 🤖 大模型推演报告 (AI Report)")
    with st.container(height=600):
        st.info("模型推演逻辑如下：")
        st.text(row['AI_Report'])

    # 可选：展示原作者结论作为参考
    with st.expander("查看原作者结论 (Benchmark)"):
        st.write(row['Author_Conclusion'])

with col3:
    st.markdown("### ✍️ 专家评分表")
    with st.form("score_form"):
        s1 = st.slider("1. 逻辑严密性", 1, 10, 5, help="因果链条是否闭环，有无逻辑断层。")
        s2 = st.slider("2. 生物学合理性", 1, 10, 5, help="是否符合病理生理学描述，有无幻觉。")
        s3 = st.slider("3. 证据整合力", 1, 10, 5, help="对阴性/非线性结果的解释能力。")
        s4 = st.slider("4. 转化洞察力", 1, 10, 5, help="假说的原创性与干预建议的可行性。")

        st.divider()

        turing = st.radio("🕵️ 科学图灵测试：您认为此推论出自？",
                          ["资深科学家", "初级研究员", "AI模型"], horizontal=True)

        feedback = st.text_area("综合评语 (选填):", placeholder="请输入您的洞察或修改意见...")

        submit_button = st.form_submit_button("提交本篇评估")

# --- 保存评分逻辑 ---
if submit_button:
    if not expert_name:
        st.error("请输入您的姓名后再提交。")
    else:
        # 构建保存结果
        result_entry = {
            "专家": expert_name,
            "文献ID": current_doc_id,
            "时间": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
            "逻辑": s1, "合理性": s2, "整合力": s3, "洞察力": s4,
            "图灵测试猜想": turing,
            "评语": feedback
        }

        # 保存到 CSV (增量保存)
        results_file = "expert_evaluations.csv"
        results_df = pd.DataFrame([result_entry])

        if not os.path.isfile(results_file):
            results_df.to_csv(results_file, index=False, encoding='utf-8-sig')
        else:
            results_df.to_csv(results_file, mode='a', header=False, index=False, encoding='utf-8-sig')

        st.balloons()
        st.success(f"【{current_doc_id}】评价已成功提交！您可以切换下一篇进行评估。")
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os

# ==========================================
# 1. 配置与全局设置
# ==========================================

Base_folder_path = "RQ1/rq3_evaluation_results/"
Output_Directory = "graphical_outputs_paper"

# 确保输出目录存在
if not os.path.exists(Output_Directory):
    os.makedirs(Output_Directory)

# 设置论文绘图风格
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans'] # 优先使用 Arial (学术常用)
plt.rcParams['axes.unicode_minus'] = False # 解决负号显示问题
plt.rcParams['figure.dpi'] = 300 # 设置高分辨率
plt.rcParams['savefig.dpi'] = 300

Languages = ["EN", "NL"]
Strategies = ["standard", "few_shot", "cot", "refine"]
# 图例显示的名称映射（首字母大写，去掉下划线）
Strategy_Labels = {s: s.replace("_", " ").title() for s in Strategies}
Strategy_Colors = ["#d7191c", "#fdae61", "#abdda4", "#2b83ba"] # 红-橙-绿-蓝 配色

Metric_Types = ["fact_checking", "fact_alignment"]

# 全部 8 个模型
Model_Names = [
    "Gemini-2.5-Flash", 
    "Gemini-2.5-Flash-Lite",
    "Gemini-2.5-Pro", 
    "Gemini-2.5-Pro-Thinking",
    "Llama-3.1-8B", 
    "Llama-3.1-70B", 
    "Llama-Reasoning-70B",
    "Llama-3.1-405B"
]

# ==========================================
# 2. 数据读取 (保持不变)
# ==========================================

records = []
for lang in Languages:
    for model in Model_Names:
        for strategy in Strategies:
            for metric in Metric_Types:
                try:
                    file_name = f"{model}_{strategy}_{metric}.csv"
                    path = f"{Base_folder_path}{lang}/{file_name}"
                    df_raw = pd.read_csv(path)
                    if 'Case_ID' in df_raw.columns:
                        df_raw.set_index('Case_ID', inplace=True)
                    for case_id, row_data in df_raw.iterrows():
                        records.append({
                            "Language": lang, "Model": model, "Strategy": strategy,
                            "Metric": metric, "Case": case_id,
                            "Overall": row_data.get("Overall_Score", 0),
                            "Subjective": row_data.get("Subjective", 0),
                            "Objective": row_data.get("Objective", 0),
                            "Assessment": row_data.get("Assessment", 0),
                            "Plan": row_data.get("Plan", 0)
                        })
                except FileNotFoundError:
                    continue

df_all = pd.DataFrame(records)

# --- 生成模拟数据 (如果文件缺失) ---
if df_all.empty:
    print("No data found. Generating Mock Data...")
    mock_records = []
    cases = ["Earache", "Constipation", "Sore Throat", "Dizziness", "Skin Lesion", 
             "Eye Infection", "Migraine", "Back Pain", "Fatigue", "Burnout", "Average"]
    for l in Languages:
        for m in Model_Names:
            for s in Strategies:
                for mt in Metric_Types:
                    for c in cases:
                        base = 60
                        if "Pro" in m or "405B" in m: base += 10
                        if "Thinking" in m or "Reasoning" in m: base += 15
                        if s == "cot": base += 5
                        if s == "self_correction": base += 8
                        if mt == "fact_checking": base -= 5
                        val = min(100, max(0, base + np.random.randn()*3))
                        mock_records.append({
                            "Language": l, "Model": m, "Strategy": s, "Metric": mt, "Case": c,
                            "Overall": val, "Subjective": val, "Objective": val, "Assessment": val, "Plan": val
                        })
    df_all = pd.DataFrame(mock_records)

print(f"Data Loaded: {len(df_all)} records.")


# ==========================================
# 3. 绘图函数: Matplotlib Hero Plot
# ==========================================

def plot_hero_matplotlib(data, metric_name, title_suffix):
    """绘制分组柱状图 (Hero Plot)"""
    # 筛选数据
    df_view = data[(data['Case'] == 'Average') & 
                   (data['Language'] == 'EN') & 
                   (data['Metric'] == metric_name)].copy()
    
    # 准备绘图数据矩阵
    # Rows: Models, Cols: Strategies
    pivot_df = df_view.pivot(index='Model', columns='Strategy', values='Overall')
    # 确保行按照 Model_Names 排序，列按照 Strategies 排序
    pivot_df = pivot_df.reindex(Model_Names)[Strategies]
    
    # 设置画布
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # 参数设置
    x = np.arange(len(Model_Names))
    width = 0.8  # 总柱宽
    bar_width = width / len(Strategies)
    
    # 绘制每一组柱子
    for i, strategy in enumerate(Strategies):
        scores = pivot_df[strategy].values
        # 计算偏移量: 让柱子组居中
        offset = (i - len(Strategies)/2) * bar_width + bar_width/2
        
        ax.bar(x + offset, scores, width=bar_width, label=Strategy_Labels[strategy], 
               color=Strategy_Colors[i], edgecolor='white', linewidth=0.5, zorder=3)

    # 轴设置
    ax.set_title(f"Overall Performance: {title_suffix} (EN)", fontsize=16, pad=15, fontweight='bold')
    ax.set_ylabel("Benchmark Score (%)", fontsize=12)
    ax.set_ylim(0, 115) # 留出顶部空间
    
    ax.set_xticks(x)
    ax.set_xticklabels(Model_Names, rotation=20, ha='right', fontsize=10)
    
    # 网格线 (仅Y轴)
    ax.grid(axis='y', linestyle='--', alpha=0.5, zorder=0)
    
    # 图例设置 (右下角)
    ax.legend(loc='lower right', ncol=2, fontsize=10, frameon=True, 
              facecolor='white', framealpha=0.9, edgecolor='gray')
    
    # 移除顶部和右侧边框 (更符合学术风格)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    plt.tight_layout()
    
    # 保存
    filename = f"{Output_Directory}/HeroPlot_{metric_name}.png"
    plt.savefig(filename)
    print(f"Saved: {filename}")
    plt.close()


# ==========================================
# 4. 绘图函数: Seaborn Heatmap
# ==========================================

def plot_heatmap_seaborn(data, case_name, metric_name, strategy="cot", lang="EN"):
    """绘制热力图"""
    df_heat = data[(data['Case'] == case_name) & 
                   (data['Metric'] == metric_name) &
                   (data['Strategy'] == strategy) & 
                   (data['Language'] == lang)].copy()
    
    if df_heat.empty:
        return

    # 准备数据: Rows=Model, Cols=SOAP
    # 我们只取需要的列
    cols = ["Subjective", "Objective", "Assessment", "Plan"]
    # 将数据转换为以 Model 为索引的格式
    df_heat = df_heat.set_index('Model').reindex(Model_Names)
    heatmap_data = df_heat[cols]
    
    # 设置画布
    fig, ax = plt.subplots(figsize=(6, 5))
    
    # 绘制热力图
    # cmap="RdYlGn": 红到绿 (分数越高越绿)
    # annot=True: 在格子里显示数值
    # fmt=".0f": 显示整数
    sns.heatmap(heatmap_data, ax=ax, cmap="RdYlGn", vmin=40, vmax=100, 
                annot=True, fmt=".0f", linewidths=1, linecolor='white',
                cbar_kws={'label': 'Score (%)'})
    
    ax.set_title(f"Case: {case_name} ({metric_name})", fontsize=12, pad=10)
    ax.set_ylabel("") # 不需要 Y 轴标签 "Model"
    ax.set_xlabel("")
    
    plt.tight_layout()
    
    # 保存
    # 文件名处理: 把 case 名中的空格换成下划线
    safe_case = case_name.replace(" ", "_")
    filename = f"{Output_Directory}/Heatmap_{safe_case}_{metric_name}.png"
    plt.savefig(filename)
    # print(f"Saved: {filename}") # 避免刷屏
    plt.close()

# ==========================================
# 5. 批量执行
# ==========================================

print("Starting Matplotlib plotting...")

# 1. 生成两个主结果图 (Hero Plots)
plot_hero_matplotlib(df_all, "fact_checking", "Fact Checking")
plot_hero_matplotlib(df_all, "fact_alignment", "Fact Alignment")

# 2. 生成所有 Case 的热力图
unique_cases = [c for c in df_all['Case'].unique() if c != 'Average']

print(f"Generating heatmaps for {len(unique_cases)} cases...")
for case in unique_cases:
    # 只生成 Fact Checking 和 Fact Alignment 的 heatmap
    # 默认使用 'cot' 策略和 'EN' 语言作为代表
    plot_heatmap_seaborn(df_all, case, "fact_checking", strategy="cot")
    plot_heatmap_seaborn(df_all, case, "fact_alignment", strategy="cot")

print("All plots generated successfully!")
print(f"Please check the folder: {Output_Directory}")
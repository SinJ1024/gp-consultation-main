import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
from math import pi

# ==========================================
# 1. 配置与全局设置
# ==========================================

Base_folder_path = "RQ1/rq3_evaluation_results/"
Output_Directory = "graphical_outputs_paper"

if not os.path.exists(Output_Directory):
    os.makedirs(Output_Directory)

# 论文绘图风格设置
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['figure.dpi'] = 300
plt.rcParams['savefig.dpi'] = 300

Languages = ["EN", "NL"]
Strategies = ["standard", "few_shot", "cot", "refine"]
Strategy_Labels = {s: s.replace("_", " ").title() for s in Strategies}
Strategy_Colors = ["#d7191c", "#fdae61", "#abdda4", "#2b83ba"]

Metric_Types = ["fact_checking", "fact_alignment"]

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
# 2. 数据读取
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

# --- 模拟数据生成 (仅当文件缺失时) ---
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
                        # 模拟语言差异: NL 比 EN 低
                        if l == "NL": base -= 5
                        
                        val = min(100, max(0, base + np.random.randn()*3))
                        # 模拟 Plan 在 NL 中表现更差
                        plan_val = val - 5 if l == "NL" else val
                        
                        mock_records.append({
                            "Language": l, "Model": m, "Strategy": s, "Metric": mt, "Case": c,
                            "Overall": val, "Subjective": val, "Objective": val, "Assessment": val, "Plan": plan_val
                        })
    df_all = pd.DataFrame(mock_records)

print(f"Data Loaded: {len(df_all)} records.")


# ==========================================
# 3. 绘图函数: Matplotlib Hero Plot
# ==========================================

def plot_hero_matplotlib(data, metric_name, title_suffix):
    """绘制分组柱状图"""
    df_view = data[(data['Case'] == 'Average') & 
                   (data['Language'] == 'EN') & 
                   (data['Metric'] == metric_name)].copy()
    
    pivot_df = df_view.pivot(index='Model', columns='Strategy', values='Overall')
    pivot_df = pivot_df.reindex(Model_Names)[Strategies]
    
    fig, ax = plt.subplots(figsize=(12, 6))
    x = np.arange(len(Model_Names))
    width = 0.8
    bar_width = width / len(Strategies)
    
    for i, strategy in enumerate(Strategies):
        scores = pivot_df[strategy].values
        offset = (i - len(Strategies)/2) * bar_width + bar_width/2
        ax.bar(x + offset, scores, width=bar_width, label=Strategy_Labels[strategy], 
               color=Strategy_Colors[i], edgecolor='white', linewidth=0.5, zorder=3)

    ax.set_title(f"Overall Performance: {title_suffix} (EN)", fontsize=16, pad=15, fontweight='bold')
    ax.set_ylabel("Benchmark Score (%)", fontsize=12)
    ax.set_ylim(0, 115)
    ax.set_xticks(x)
    ax.set_xticklabels(Model_Names, rotation=20, ha='right', fontsize=10)
    ax.grid(axis='y', linestyle='--', alpha=0.5, zorder=0)
    ax.legend(loc='lower right', ncol=2, fontsize=10, frameon=True, facecolor='white', framealpha=0.9)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    plt.tight_layout()
    plt.savefig(f"{Output_Directory}/HeroPlot_{metric_name}.png")
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
    if df_heat.empty: return

    cols = ["Subjective", "Objective", "Assessment", "Plan"]
    df_heat = df_heat.set_index('Model').reindex(Model_Names)
    heatmap_data = df_heat[cols]
    
    fig, ax = plt.subplots(figsize=(6, 5))
    sns.heatmap(heatmap_data, ax=ax, cmap="RdYlGn", vmin=40, vmax=100, 
                annot=True, fmt=".0f", linewidths=1, linecolor='white',
                cbar_kws={'label': 'Score (%)'})
    
    ax.set_title(f"Case: {case_name} ({metric_name})", fontsize=12, pad=10)
    ax.set_ylabel("")
    ax.set_xlabel("")
    plt.tight_layout()
    safe_case = case_name.replace(" ", "_")
    plt.savefig(f"{Output_Directory}/Heatmap_{safe_case}_{metric_name}.png")
    plt.close()


# ==========================================
# 5. [NEW] 绘图函数: Radar Chart (Language Gap)
# ==========================================

def plot_radar_language_comparison(data, strategy="cot", metric="fact_checking"):
    """
    绘制雷达图: 对比 EN vs NL 的平均表现
    展示维度: Subjective, Objective, Assessment, Plan, Overall
    """
    # 筛选数据: Average Case, 特定 Strategy, 特定 Metric
    # 计算所有模型在该条件下的平均分 (Aggregate Performance)
    df_radar = data[(data['Case'] == 'Average') & 
                    (data['Strategy'] == strategy) & 
                    (data['Metric'] == metric)].copy()
    
    if df_radar.empty: return

    # 按语言分组计算均值
    cols = ["Subjective", "Objective", "Assessment", "Plan", "Overall"]
    grouped = df_radar.groupby("Language")[cols].mean()

    # 准备绘图数据
    labels = cols
    num_vars = len(labels)
    
    # 计算角度
    angles = [n / float(num_vars) * 2 * pi for n in range(num_vars)]
    angles += angles[:1] # 闭合回路
    
    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
    
    # 绘制 EN
    values_en = grouped.loc["EN"].tolist()
    values_en += values_en[:1]
    ax.plot(angles, values_en, linewidth=2, linestyle='solid', label="English", color="#1f77b4")
    ax.fill(angles, values_en, color="#1f77b4", alpha=0.25)
    
    # 绘制 NL
    values_nl = grouped.loc["NL"].tolist()
    values_nl += values_nl[:1]
    ax.plot(angles, values_nl, linewidth=2, linestyle='solid', label="Dutch", color="#ff7f0e")
    ax.fill(angles, values_nl, color="#ff7f0e", alpha=0.25)
    
    # 样式设置
    ax.set_theta_offset(pi / 2) # 设置正上方为起点
    ax.set_theta_direction(-1) # 顺时针
    
    plt.xticks(angles[:-1], labels, size=12)
    ax.set_rlabel_position(0)
    plt.yticks([20, 40, 60, 80, 100], ["20", "40", "60", "80", "100"], color="grey", size=8)
    plt.ylim(0, 105)
    
    # 标题和图例
    plt.title(f"Cross-Lingual Gap Analysis\n(Avg across models, Strategy: {Strategy_Labels[strategy]})", 
              size=14, color='black', y=1.1)
    plt.legend(loc='upper right', bbox_to_anchor=(1.1, 1.1))
    
    plt.tight_layout()
    filename = f"{Output_Directory}/Radar_Language_Gap_{metric}.png"
    plt.savefig(filename)
    print(f"Saved: {filename}")
    plt.close()


# ==========================================
# 6. 批量执行
# ==========================================

print("Starting Plot Generation...")

# 1. Hero Plots
plot_hero_matplotlib(df_all, "fact_checking", "Fact Checking")
plot_hero_matplotlib(df_all, "fact_alignment", "Fact Alignment")

# 2. Radar Charts (New!) - 针对 CoT 策略
# 对比两种 Metric 下的语言差异
plot_radar_language_comparison(df_all, strategy="cot", metric="fact_checking")
plot_radar_language_comparison(df_all, strategy="cot", metric="fact_alignment")

# 3. Heatmaps
unique_cases = [c for c in df_all['Case'].unique() if c != 'Average']
print(f"Generating heatmaps for {len(unique_cases)} cases...")
for case in unique_cases:
    plot_heatmap_seaborn(df_all, case, "fact_checking", strategy="cot")
    plot_heatmap_seaborn(df_all, case, "fact_alignment", strategy="cot")

print("All plots generated successfully!")
print(f"Please check the folder: {Output_Directory}")
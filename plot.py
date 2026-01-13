import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
from math import pi


Base_folder_path = "RQ1/rq3_evaluation_results/"
Output_Directory = "graphical_outputs_paper"

if not os.path.exists(Output_Directory):
    os.makedirs(Output_Directory)

plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['figure.dpi'] = 300
plt.rcParams['savefig.dpi'] = 300

Languages = ["EN", "NL"]
Strategies = ["standard", "few_shot", "cot", "refine"]
Strategy_Labels = {s: s.replace("_", " ").title() for s in Strategies}
Strategy_Colors = ["#d7191c", "#fdae61", "#abdda4", "#2b83ba"]
Metric_Types = ["fact_checking", "fact_alignment", "conciseness"]

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


print(f"Data Loaded: {len(df_all)} records.")



def plot_hero_matplotlib(data, metric_name, title_suffix):
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




def plot_heatmap_seaborn(data, case_name, metric_name, strategy="cot", lang="EN"):
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




def plot_radar_language_comparison(data, metric="fact_checking"):
    df_radar = data[(data['Case'] == 'Average') & 
                    (data['Metric'] == metric)].copy()


    cols = ["Subjective", "Objective", "Assessment", "Plan", "Overall"]
    grouped = df_radar.groupby("Language")[cols].mean()

    labels = cols
    num_vars = len(labels)
    
    angles = [n / float(num_vars) * 2 * pi for n in range(num_vars)]
    angles += angles[:1]
    
    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
    
    values_en = grouped.loc["EN"].tolist()
    values_en += values_en[:1]
    ax.plot(angles, values_en, linewidth=2, linestyle='solid', label="English", color="#1f77b4")
    ax.fill(angles, values_en, color="#1f77b4", alpha=0.25)
    
    
    values_nl = grouped.loc["NL"].tolist()
    values_nl += values_nl[:1]
    ax.plot(angles, values_nl, linewidth=2, linestyle='solid', label="Dutch", color="#ff7f0e")
    ax.fill(angles, values_nl, color="#ff7f0e", alpha=0.25)
    
    ax.set_theta_offset(pi / 2)
    ax.set_theta_direction(-1)
    
    plt.xticks(angles[:-1], labels, size=12)
    ax.set_rlabel_position(0)
    plt.yticks([20, 40, 60, 80, 100], ["20", "40", "60", "80", "100"], color="grey", size=8)
    plt.ylim(0, 105)
    
    metric_title = metric.replace("_", " ").title()
    plt.title(f"Cross-Lingual Gap Analysis\n(Avg across All Strategies, {metric_title})", 
              size=14, color='black', y=1.1)
    plt.legend(loc='upper right', bbox_to_anchor=(1.1, 1.1))
    
    plt.tight_layout()
    filename = f"{Output_Directory}/Radar_Language_Gap_AllStrategies_{metric}.png"
    plt.savefig(filename)
    plt.close()









plot_hero_matplotlib(df_all, "fact_checking", "Fact Checking")
plot_hero_matplotlib(df_all, "fact_alignment", "Fact Alignment")
plot_hero_matplotlib(df_all, "conciseness", "Conciseness")


plot_radar_language_comparison(df_all, metric="fact_checking")
plot_radar_language_comparison(df_all, metric="fact_alignment")
plot_radar_language_comparison(df_all, metric="conciseness")


unique_cases = [c for c in df_all['Case'].unique() if c != 'Average']
print(f"Generating heatmaps for {len(unique_cases)} cases...")

for case in unique_cases:
    plot_heatmap_seaborn(df_all, case, "fact_checking", strategy="cot")
    plot_heatmap_seaborn(df_all, case, "fact_alignment", strategy="cot")
    plot_heatmap_seaborn(df_all, case, "conciseness", strategy="cot")


print(f"Output dic: {Output_Directory}")
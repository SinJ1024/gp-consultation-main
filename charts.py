from bokeh.models import ColumnDataSource, ColorBar
from bokeh.plotting import figure, show
from bokeh.transform import linear_cmap
from bokeh.palettes import RdYlGn
from bokeh.layouts import column


import pandas as pd


Output_Directory = "graphical_outputs"
Base_folder_path = "RQ1/rq3_evaluation_results/"
Languages = ["EN", "NL"]
models = [
    "Gemini-2.5-Flash_cot_fact_alignment.csv",
    "Gemini-2.5-Flash_cot_fact_checking.csv",
    "Gemini-2.5-Flash-Lite_cot_fact_alignment.csv",
    "Gemini-2.5-Flash-Lite_cot_fact_checking.csv",
    "Gemini-2.5-Pro_cot_fact_alignment.csv",
    "Gemini-2.5-Pro_cot_fact_checking.csv",
    "Gemini-2.5-Pro-Thinking_cot_fact_alignment.csv",
    "Gemini-2.5-Pro-Thinking_cot_fact_checking.csv",
    "Llama-3.1-8B_cot_fact_alignment.csv",
    "Llama-3.1-8B_cot_fact_checking.csv",
    "Llama-3.1-70B_cot_fact_alignment.csv",
    "Llama-3.1-70B_cot_fact_checking.csv",
    "Llama-Reasoning-70B_cot_fact_alignment.csv",
    "Llama-Reasoning-70B_cot_fact_checking.csv",
    "Llama-3.1-405B_cot_fact_alignment.csv",
    "Llama-3.1-405B_cot_fact_checking.csv",
]


records = []
for lang in Languages:
    for f in models:
        path = Base_folder_path + lang + "/" + f
        df = pd.read_csv(path).set_index('Case_ID')
        overall_score = df['Overall_Score']

        for case, score in overall_score.items():
            model, type, metric = f.partition("_cot_")
            metric = metric.split(".csv")[0]
            records.append({
                "model": model,
                "type": type.split("_")[1],
                "language": lang,
                "case": case,
                "score": score,
                "metric": metric
            })
df_tmp = pd.DataFrame(records)
print(df_tmp)
df = df_tmp[df_tmp['case'] != "Average"]
df_2 = df_tmp[df_tmp['case'] == "Average"]


# 1. Language Comparison
# Bar chart comparing overall score (Y) to Case name (X)
# Problems: Results in 1 graph per model. Could do a grid graph
plots = []
metrics = ["fact_alignment", "fact_checking"]
for metric in metrics:
    for lang in Languages:
        df_m = df[(df['metric'] == metric) & (df['language'] == lang)]
        model = sorted(df_m["model"].unique().tolist())
        cases = sorted(df_m["case"].unique().tolist())
        source = ColumnDataSource(df_m)

        mapper = linear_cmap(
            field_name="score",
            palette=RdYlGn[11][::-1],
            low=0,
            high=100
        )

        p = figure(
            x_range=model,
            y_range=list(reversed(cases)),
            x_axis_location="above",
            width=1000,
            height=500,
            title=f"{metric} Overall_score Heatmap - {lang}",
            tools="hover, save",
            toolbar_location="right"
        )

        p.rect(
            x="model",
            y="case",
            width=1,
            height=1,
            source=source,
            fill_color=mapper,
            line_color="white"
        )

        color_bar = ColorBar(
            color_mapper=mapper["transform"],
            label_standoff=8,
            title="Score (%)"
        )

        p.add_layout(color_bar, "right")

        p.hover.tooltips = [
            ("Model", "@model"),
            ("Case", "@case"),
            ("Accuracy", "@score{0.0}%"),
            ("Language", "@language")
        ]

        plots.append(p)


# 2. Scaling Laws
# Small -> Medium -> Large  (Line Chart)
# Llama has 8B -> 70B -> 405B
# Gemini flash/pro (1.05M input tokens each)

model_labels = {
    "Llama-3.1-8B": "8B",
    "Llama-3.1-70B": "70B",
    "Llama-3.1-405B": "405B",
    "Llama-Reasoning-70B": "70B-Reasoning"
}

# Explicit order for the x-axis
x_axis_order = ["8B", "70B", "405B", "70B-Reasoning"]

df_scale = df_2[df_2['model'].isin(model_labels.keys())].copy()
df_scale['label'] = df_scale['model'].map(model_labels)

# Set categorical type to ensure correct sorting for the line plot
df_scale['label'] = pd.Categorical(df_scale['label'], categories=x_axis_order, ordered=True)
df_scale = df_scale.sort_values('label')

p = figure(
    width=1000,
    height=500,
    title="Scaling Law: LLaMA Model Performance",
    x_axis_label="Model Size (Billion Parameters)",
    y_axis_label="Mean Accuracy (%)",
    x_range=x_axis_order,  # Force categorical x-axis order
    tools="hover,save"
)

colors = {
    ("EN", "fact_alignment"): "firebrick",
    ("EN", "fact_checking"): "forestgreen",
    ("NL", "fact_alignment"): "orange",
    ("NL", "fact_checking"): "blue"
}

for (lang, metric), color in colors.items():
    df_m = df_scale[(df_scale["metric"] == metric) &
                    (df_scale["language"] == lang)]
    
    # Sort by label again to ensure the line connects points in the correct order
    df_m = df_m.sort_values('label')

    source = ColumnDataSource({
        "x": df_m["label"],
        "y": df_m["score"],
        "model": df_m["model"],
        "language": df_m["language"],
        "metric": df_m["metric"]
    })

    # Plot the line
    p.line(
        x="x",
        y="y",
        source=source,
        line_width=3,
        color=color,
        legend_label=f"{metric.replace('_', ' ').title()} - {lang}"
    )

    # Add circles to highlight the specific data points
    p.circle(
        x="x",
        y="y",
        source=source,
        size=8,
        color=color,
        fill_color="white",
        line_width=2
    )

p.hover.tooltips = [
    ("Model", "@model"),
    ("Score", "@y{0.0}%"),
    ("Metric", "@metric"),
    ("Language", "@language")
]

p.legend.location = "bottom_right"
p.legend.click_policy = "hide"
p.y_range.start = 0
p.y_range.end = 100

plots.append(p)

show(column(*plots))
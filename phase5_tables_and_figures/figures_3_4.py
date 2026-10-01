"""Figures 3 and 4: topical keywords and LIS context categories.

Figure 3 shows, for each level, the ten keywords most frequent across both
models combined; percentages are shares of all keywords a model produced at
that level. Figure 4 shows the twelve LIS context options listed in the
classification prompt; percentages are shares of all non-blank LIS outputs.
Writes figure3.png and figure4.png.
"""
from collections import Counter
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from common import clean_file

plt.rcParams["font.family"] = "DejaVu Sans"
PANELS = [("conversation", "Claude"), ("conversation", "Gemini"),
          ("segment", "Claude"), ("segment", "Gemini")]
MODEL_NAME = {"Claude": "Claude 3 Haiku", "Gemini": "Gemini 2.0 Flash"}
data = {p: clean_file(*p) for p in PANELS}

def lighten(ax):
    """Light dotted frame so value labels never collide with a heavy border."""
    for sp in ax.spines.values():
        sp.set_color("#BBBBBB"); sp.set_linestyle(":"); sp.set_linewidth(0.8)


def draw(values, order, filename, color, xlabel, xmax):
    fig, axs = plt.subplots(2, 2, figsize=(10.5, 9.4), sharex="row")
    for n, (ax, p) in enumerate(zip(axs.flat, PANELS)):
        counts, total = values[p]
        labels = order[p[0]]
        y = np.arange(len(labels))[::-1]
        pct = [100 * counts[k] / total for k in labels]
        ax.barh(y, pct, color=color[p[1]])
        for yy, k, v in zip(y, labels, pct):
            ax.text(v + xmax * 0.01, yy, f"{counts[k]:,} ({v:.1f}%)", va="center", fontsize=10.5)
        ax.set_yticks(y); ax.set_yticklabels(labels, fontsize=11.5)
        ax.set_xlim(0, xmax[p[0]] if isinstance(xmax, dict) else xmax)
        ax.set_title(f"{'ABCD'[n]}. {p[0].title()}\n{MODEL_NAME[p[1]]}", fontsize=12, weight="bold", loc="left")
        ax.grid(axis="x", color="#ddd"); ax.set_axisbelow(True)
        lighten(ax)
        if n >= 2: ax.set_xlabel(xlabel, fontsize=11.5)
    plt.tight_layout(); plt.savefig(filename, dpi=400, facecolor="white"); plt.close()


# ---------------- Figure 3 ----------------
kw = {}
for p, d in data.items():
    words = [k.strip() for s in d["keywords"] for k in s.split(";") if k.strip()]
    kw[p] = (Counter(words), len(words))
order3 = {}
for level in ["conversation", "segment"]:
    pooled = kw[(level, "Claude")][0] + kw[(level, "Gemini")][0]
    order3[level] = [k for k, _ in pooled.most_common(10)]
draw(kw, order3, "figure3.png", {"Claude": "#8E44AD", "Gemini": "#B07CC6"},
     "Percentage of keywords (%)", 11)

# ---------------- Figure 4 ----------------
LIS = ["Information Retrieval", "Information Behavior", "Information Literacy", "Other",
       "User Studies", "Digital Libraries", "Archives & Preservation", "Knowledge Management",
       "Metadata & Cataloging", "Scholarly Communication", "Data Science for Libraries", "None"]
lis = {}
for p, d in data.items():
    v = d["lis_context"].str.strip()
    lis[p] = (Counter(v[v != ""]), int((v != "").sum()))
draw(lis, {"conversation": LIS, "segment": LIS}, "figure4.png",
     {"Claude": "#5DADE2", "Gemini": "#2E86C1"}, "Percentage of non-blank outputs (%)", 42)
print("figure3.png and figure4.png written")

"""Figure 2 (cognitive complexity by academic output type) and Figure 5
(query reformulation patterns).

Both figures describe each model's classifications at each level (one row
per valid identifier), after label normalization. Figure 2 shows only cases with
a valid academic output type and Bloom level. Figure 5 shows the eleven valid
reformulation patterns; percentages use all non-blank outputs as the
denominator, and the number of invalid outputs is given in each panel title.
Writes figure2.png and figure5.png.
"""
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from common import clean_file

plt.rcParams["font.family"] = "DejaVu Sans"
PANELS = [("conversation", "Claude"), ("conversation", "Gemini"),
          ("segment", "Claude"), ("segment", "Gemini")]
MODEL_NAME = {"Claude": "Claude 3 Haiku", "Gemini": "Gemini 2.0 Flash"}
data = {p: clean_file(*p) for p in PANELS}
label = lambda s: s.replace("_", " ").title()

def lighten(ax):
    """Light dotted frame so value labels never collide with a heavy border."""
    for sp in ax.spines.values():
        sp.set_color("#BBBBBB"); sp.set_linestyle(":"); sp.set_linewidth(0.8)

# ---------------- Figure 2 ----------------
AO = ["GENERAL_LEARNING", "RESEARCH_PAPER", "REPORT", "ESSAY_PAPER", "CREATIVE_WORK",
      "HOMEWORK_ASSIGNMENT", "PRESENTATION", "EXAM_PREPARATION", "CODING_PROJECT",
      "ADMINISTRATIVE_ACADEMIC"]
BLOOM = ["REMEMBER", "UNDERSTAND", "APPLY", "ANALYZE", "EVALUATE", "CREATE"]
total = {a: sum(((d.AO == a) & d.CC.isin(BLOOM)).sum() for d in data.values()) for a in AO}
AO = sorted(AO, key=lambda a: -total[a])
tabs = {}
for p, d in data.items():
    x = d[d.AO.isin(AO) & d.CC.isin(BLOOM)]
    tabs[p] = pd.crosstab(pd.Categorical(x.AO, AO), pd.Categorical(x.CC, BLOOM), dropna=False).values
vmax = np.log1p(max(t.max() for t in tabs.values()))
fig, axs = plt.subplots(2, 2, figsize=(10, 9.2))
for n, (ax, (p, t)) in enumerate(zip(axs.flat, tabs.items())):
    ax.imshow(np.log1p(t), cmap="YlOrRd", aspect="auto", vmin=0, vmax=vmax)
    for i in range(t.shape[0]):
        for j in range(t.shape[1]):
            ax.text(j, i, str(t[i, j]), ha="center", va="center", fontsize=10.5,
                    color="white" if t[i, j] > 200 else "black")
    ax.set_xticks(range(6)); ax.set_xticklabels([b.title() for b in BLOOM], rotation=35, ha="right", fontsize=11)
    ax.set_yticks(range(len(AO))); ax.set_yticklabels([label(a) for a in AO], fontsize=11)
    ax.set_title(f"{'ABCD'[n]}. {p[0].title()}\n{MODEL_NAME[p[1]]} (n = {t.sum():,})",
                 fontsize=12, weight="bold", loc="left")
    ax.set_xlabel("Bloom's level", fontsize=11.5); ax.set_ylabel("Academic output type", fontsize=11.5)
    ax.set_xticks(np.arange(-.5, 6), minor=True); ax.set_yticks(np.arange(-.5, len(AO)), minor=True)
    ax.grid(which="minor", color="white", lw=1); ax.tick_params(which="minor", length=0)
    lighten(ax)
plt.tight_layout(); plt.savefig("figure2.png", dpi=400, facecolor="white"); plt.close()

# ---------------- Figure 5 ----------------
RF = ["ELABORATION_REQUEST", "SINGLE_QUERY", "SPECIFICATION", "TERM_SUBSTITUTION",
      "NEW_DIRECTION", "ASPECT_SHIFT", "CLARIFICATION_REQUEST", "NOT_REFORMULATION",
      "REPETITION", "GENERALIZATION", "ERROR_CORRECTION"]
fig, axs = plt.subplots(2, 2, figsize=(10.5, 9.4), sharex=True)
for n, (ax, (p, d)) in enumerate(zip(axs.flat, data.items())):
    N = (d.reformulation_pattern.str.strip() != "").sum()
    counts = [(d.QR == r).sum() for r in RF]
    y = np.arange(len(RF))[::-1]
    ax.barh(y, [100 * c / N for c in counts], color="#4C9F8A" if p[1] == "Claude" else "#7FC8B3")
    for yy, c in zip(y, counts):
        ax.text(100 * c / N + 0.8, yy, f"{c:,} ({100 * c / N:.1f}%)", va="center", fontsize=10.5)
    ax.set_yticks(y); ax.set_yticklabels([label(r) for r in RF], fontsize=11.5); ax.set_xlim(0, 95)
    ax.set_title(f"{'ABCD'[n]}. {p[0].title()}, {MODEL_NAME[p[1]]} \n(N = {N:,}; {N - sum(counts)} invalid)",
                 fontsize=12, weight="bold", loc="left")
    ax.grid(axis="x", color="#ddd"); ax.set_axisbelow(True)
    lighten(ax)
for ax in axs[1]: ax.set_xlabel("Percentage of non-blank outputs (%)", fontsize=11.5)
plt.tight_layout(); plt.savefig("figure5.png", dpi=400, facecolor="white"); plt.close()
print("figure2.png and figure5.png written")

"""Table 5: Cohen's kappa between the two human coders and between each coder
and each model, from the human coding workbook humancode_sample1.xlsx.

Coders and models classified the same English segment summaries. Blank
outputs are treated as missing. "None" codes, from coders and models alike,
and invalid model outputs are retained as values, as in Table 3.
Writes table5.csv.
"""
import os
import numpy as np
import pandas as pd
from sklearn.metrics import cohen_kappa_score
from common import DATA_DIR, clean_file

WORKBOOK = os.path.join(DATA_DIR, "humancode_sample1.xlsx")
sheet = lambda name: pd.read_excel(WORKBOOK, name, dtype=str, keep_default_na=False)
cases = sheet("Case List")
cases = cases[cases["Case ID"].str.fullmatch(r"\d+") & (cases["Segment or Convo ID"] != "")]
coder = {n: sheet(f"Coder {n}").set_index("Case ID") for n in (1, 2)}
models = {m: clean_file("segment", m).set_index("segment_id") for m in ("Claude", "Gemini")}

DIMS = [("Academic Output Type", "AO"), ("Cognitive Complexity", "CC"),
        ("Topic and LIS Context", "LIS"), ("Query Reformulation", "QR")]


def human(n, col, dim):
    v = coder[n].loc[cases["Case ID"], col].str.strip()
    return v.values if dim == "LIS" else v.str.upper().str.replace(" ", "_").values


def model(m, dim):
    return np.array([models[m].loc[s, dim] if s in models[m].index else ""
                     for s in cases["Segment or Convo ID"]])


def pair(a, b):
    ok = (a != "") & (b != "")
    return f"{cohen_kappa_score(a[ok], b[ok]):.3f} (n={ok.sum()})"


rows = []
for col, dim in DIMS:
    h1, h2 = human(1, col, dim), human(2, col, dim)
    cl, ge = model("Claude", dim), model("Gemini", dim)
    common = (h1 != "") & (h2 != "") & (cl != "") & (ge != "")
    rows.append({"dimension": col, "coder1_vs_coder2": pair(h1, h2),
                 "coder1_vs_claude": pair(h1, cl), "coder1_vs_gemini": pair(h1, ge),
                 "coder2_vs_claude": pair(h2, cl), "coder2_vs_gemini": pair(h2, ge),
                 "common_n": int(common.sum()),
                 "common_coder1_vs_claude": round(cohen_kappa_score(h1[common], cl[common]), 3),
                 "common_coder1_vs_gemini": round(cohen_kappa_score(h1[common], ge[common]), 3),
                 "common_coder2_vs_claude": round(cohen_kappa_score(h2[common], cl[common]), 3),
                 "common_coder2_vs_gemini": round(cohen_kappa_score(h2[common], ge[common]), 3)})
out = pd.DataFrame(rows)
out.to_csv("table5.csv", index=False)
print(out.to_string(index=False))

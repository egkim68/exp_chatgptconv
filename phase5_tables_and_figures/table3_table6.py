"""Table 3 (inter-model reliability and distributional comparisons) and
Table 6 (sensitivity analysis: kappa recomputed on codebook-valid pairs).

For each dimension and level: cases are matched by identifier, labels are
normalized, pairs with a blank label from either model are dropped, and then
  - percent agreement and Cohen's kappa are computed on the matched pairs;
  - a Stuart-Maxwell test of marginal homogeneity compares the two models'
    label distributions over the same (paired) cases;
  - D, the index of dissimilarity, is half the summed absolute difference
    between the two models' label proportions;
  - Table 6 recomputes kappa on pairs in which both models returned a
    codebook label (invalid, off-list, and multi-category outputs excluded).
Writes table3.csv and table6.csv.
"""
import numpy as np
import pandas as pd
from statsmodels.stats.contingency_tables import SquareTable
import pandas as pd
from sklearn.metrics import cohen_kappa_score
from common import matched, DIM_LABELS


VALID = {
    "AO": {"HOMEWORK_ASSIGNMENT", "ESSAY_PAPER", "RESEARCH_PAPER", "PRESENTATION", "REPORT",
           "EXAM_PREPARATION", "CODING_PROJECT", "CREATIVE_WORK", "GENERAL_LEARNING",
           "ADMINISTRATIVE_ACADEMIC"},
    "CC": {"REMEMBER", "UNDERSTAND", "APPLY", "ANALYZE", "EVALUATE", "CREATE"},
    "LIS": {"Information Retrieval", "Digital Libraries", "Information Literacy",
            "Knowledge Management", "Archives & Preservation", "Data Science for Libraries",
            "User Studies", "Information Behavior", "Metadata & Cataloging",
            "Scholarly Communication", "Other", "None"},
    "QR": {"SPECIFICATION", "GENERALIZATION", "TERM_SUBSTITUTION", "ASPECT_SHIFT",
           "ERROR_CORRECTION", "CLARIFICATION_REQUEST", "ELABORATION_REQUEST",
           "NEW_DIRECTION", "REPETITION", "NOT_REFORMULATION", "SINGLE_QUERY"},
}

rows, rows6 = [], []
for level in ["segment", "conversation"]:
    m = matched(level)
    print(f"{level}: {len(m)} matched cases")
    for dim in ["AO", "CC", "LIS", "QR"]:
        a, b = m[dim + "_gemini"], m[dim + "_claude"]
        ok = (a != "") & (b != "")
        a, b = a[ok], b[ok]
        p_o = (a == b).mean()
        kappa = cohen_kappa_score(a, b)
        cats = sorted(set(a) | set(b))
        paired = pd.crosstab(pd.Categorical(a, cats), pd.Categorical(b, cats), dropna=False).values
        sm = SquareTable(paired, shift_zeros=False).homogeneity(method="stuart_maxwell")
        pa = np.array([(a == c).mean() for c in cats]); pb = np.array([(b == c).mean() for c in cats])
        rows.append({"level": level, "dimension": DIM_LABELS[dim], "n": int(ok.sum()),
                     "stuart_maxwell": round(sm.statistic, 1), "df": int(sm.df), "p": sm.pvalue,
                     "dissimilarity": round(0.5 * np.abs(pa - pb).sum(), 2),
                     "agreement_pct": round(100 * p_o, 1), "kappa": round(kappa, 3)})
        # Table 6: pairs where both models returned a label from the codebook
        if dim == "LIS":
            va = m["lis_context_gemini"].str.strip().isin(VALID[dim])
            vb = m["lis_context_claude"].str.strip().isin(VALID[dim])
        else:
            va, vb = m[dim + "_gemini"].isin(VALID[dim]), m[dim + "_claude"].isin(VALID[dim])
        a6, b6 = m.loc[va & vb, dim + "_gemini"], m.loc[va & vb, dim + "_claude"]
        rows6.append({"level": level, "dimension": DIM_LABELS[dim],
                      "kappa_all": round(kappa, 3),
                      "kappa_valid": round(cohen_kappa_score(a6, b6), 3),
                      "n_valid": int(len(a6))})

res = pd.DataFrame(rows)
res[["level", "dimension", "n", "stuart_maxwell", "df", "p", "dissimilarity", "agreement_pct", "kappa"]].to_csv("table3.csv", index=False)
pd.DataFrame(rows6).to_csv("table6.csv", index=False)
pd.set_option("display.width", 200)
print(res.drop(columns=["p"]).to_string(index=False))
print(pd.DataFrame(rows6).to_string(index=False))

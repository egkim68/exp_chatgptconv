"""Table 1: segment coherence and topic stability, as rated by each model.

Uses one row per valid segment identifier. A segment counts as highly
coherent when its coherence rating is "high" and as stable when its topic
stability rating is "stable". Writes table1.csv.
"""
import pandas as pd
from common import clean_file

rows = []
for model in ["Gemini", "Claude"]:
    d = clean_file("segment", model)
    coherent = d["conversation_coherence"].str.strip().str.lower().eq("high")
    stable = d["topic_stability"].str.strip().str.lower().eq("stable")
    n = len(d)
    for label, mask in [("High segment coherence", coherent),
                        ("Stable topic evolution", stable),
                        ("Both criteria met", coherent & stable)]:
        rows.append({"model": model, "criterion": label, "n": int(mask.sum()),
                     "total": n, "pct": round(100 * mask.sum() / n, 1)})
out = pd.DataFrame(rows)
out.to_csv("table1.csv", index=False)
print(out.to_string(index=False))

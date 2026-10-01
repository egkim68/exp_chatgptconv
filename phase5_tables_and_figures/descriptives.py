"""Descriptive counts reported in the text and Table 2.

Inputs (in DATA_DIR):
  - db_export.csv: one row per segment, exported from the study database with
    the query below (no message or summary text is exported):

      SELECT c.convo_id, m.n_user, m.n_messages,
             (s2.convo_id IS NOT NULL) AS has_summary,
             s.segment_id, s.segment_number, s.total_segments,
             s.turn_start, s.turn_end, c.created_at,
             (SELECT MAX(m2.created_at) FROM messages m2
              WHERE m2.convo_id = c.convo_id) AS last_message
      FROM conversations c
      LEFT JOIN (SELECT convo_id, SUM(role='user') AS n_user, COUNT(*) AS n_messages
                 FROM messages GROUP BY convo_id) m ON m.convo_id = c.convo_id
      LEFT JOIN conversation_summaries s2 ON s2.convo_id = c.convo_id
      LEFT JOIN conversation_segments s ON s.convo_id = c.convo_id
      ORDER BY c.convo_id, s.segment_number;

  - the four model classification files used by common.py.

A turn is one user prompt. Prints the values reported in the manuscript.
"""
import os
from collections import Counter
import pandas as pd
import numpy as np
from common import DATA_DIR, clean_file, read_file

cols = ["convo_id", "n_user", "n_messages", "has_summary", "segment_id",
        "segment_number", "total_segments", "turn_start", "turn_end", "created_at",
        "last_message"]
db = pd.read_csv(os.path.join(DATA_DIR, "db_export.csv"), header=None, dtype=str,
                 keep_default_na=False)
db = db.iloc[:, :len(cols)]
db.columns = cols[:db.shape[1]]
if db.iloc[0]["convo_id"] == "convo_id":  # tolerate an export that includes a header row
    db = db.iloc[1:]
conv = db.drop_duplicates("convo_id").copy()
for c in ["n_user", "n_messages", "total_segments"]:
    conv[c] = conv[c].astype(int)
seg = db.copy()
seg["length"] = seg["turn_end"].astype(int) - seg["turn_start"].astype(int) + 1

per_student = conv["convo_id"].str.split("_").str[0].value_counts()
turns = conv["n_user"]
print("Table 2")
print(f"  conversations {len(conv):,}; students {per_student.size}; messages {conv.n_messages.sum():,}")
print(f"  conversations per student: mean {per_student.mean():.1f}, median {per_student.median()}")
print(f"  top three students: {per_student.head(3).sum():,} ({100 * per_student.head(3).sum() / len(conv):.1f}%)")
print(f"  turns per conversation: median {turns.median():g}, mean {turns.mean():.2f}, "
      f"SD {turns.std():.2f}, range {turns.min()} to {turns.max()}")
print(f"  user prompts {turns.sum():,}; other message records {conv.n_messages.sum() - turns.sum():,}")
print(f"  conversations without a summary: {(conv.has_summary == '0').sum()}")
if "created_at" in conv:
    created = pd.to_datetime(conv["created_at"], format="%Y-%m-%d %H:%M:%S", errors="coerce")
if "created_at" in conv and created.notna().mean() > 0.9:
    start = pd.Timestamp("2025-10-22")
    before = (created < start).sum()
    print(f"  conversation dates: {created.min():%Y-%m-%d} to {created.max():%Y-%m-%d}; "
          f"created before October 22, 2025: {before:,} ({100 * before / len(conv):.1f}%)")
    student = conv["convo_id"].str.split("_").str[0]
    earliest = created.groupby(student).min()
    recent = earliest[earliest >= "2025-10-01"].index
    september = earliest[(earliest >= "2025-09-01") & (earliest < "2025-10-01")].index
    older = earliest[earliest < "2025-09-01"].index
    in_window_only = earliest[earliest >= start].index
    for label, group in [("earliest conversation from October 2025", recent),
                         ("earliest conversation in September 2025", september),
                         ("longer histories (before September 2025)", older)]:
        n = student.isin(group).sum()
        print(f"  students with {label}: {len(group)} "
              f"({n:,} conversations, {100 * n / len(conv):.1f}%)")
    print(f"  students whose conversations all fall in the submission period: {len(in_window_only)}")
    if len(recent):
        print(f"  earliest date among the October group: {earliest[recent].min():%Y-%m-%d}")
    if "last_message" in conv:
        last = pd.to_datetime(conv["last_message"], format="%Y-%m-%d %H:%M:%S", errors="coerce")
        continued = ((created < start) & (last >= start)).sum()
        print(f"  conversations created earlier but continued during the period: {continued}")
print("Segments")
print(f"  segments {len(seg):,}; single-segment conversations {(conv.total_segments == 1).sum():,} "
      f"({100 * (conv.total_segments == 1).mean():.1f}%)")
print(f"  single-prompt conversations {(turns == 1).sum()} ({100 * (turns == 1).mean():.1f}%)")
print(f"  segments of 2 to 4 turns {100 * seg.length.between(2, 4).mean():.1f}%; "
      f"single-turn segments {100 * (seg.length == 1).mean():.1f}%")
print(f"  segments longer than six turns: {(seg.length > 6).sum()}; "
      f"conversations of more than 16 turns: {(turns > 16).sum()}")
print("Model outputs")
for level in ["segment", "conversation"]:
    d = read_file(level, "Claude")
    digits = d["bloom_level"].str.strip().str.fullmatch(r"[1-6]").sum()
    print(f"  Claude Bloom outputs given as digits ({level}): {digits:,} of {len(d):,}")
for level in ["conversation", "segment"]:
    for m in ["Claude", "Gemini"]:
        d = clean_file(level, m)
        words = [k.strip() for s in d["keywords"] for k in s.split(";") if k.strip()]
        print(f"  keywords {level} {m}: {len(words):,} total, {len(Counter(words)):,} distinct, "
              f"{len(words) / len(d):.1f} per unit")

print("Segment validation, split conversations only (Section 3.6)")
split_ids = set(seg.loc[seg["total_segments"].astype(int) > 1, "segment_id"])
for m in ["Gemini", "Claude"]:
    d = clean_file("segment", m)
    d = d[d["segment_id"].isin(split_ids)]
    coherent = d["conversation_coherence"].str.strip().str.lower().eq("high")
    stable = d["topic_stability"].str.strip().str.lower().eq("stable")
    print(f"  {m}: {len(d):,} segments; coherent {100 * coherent.mean():.1f}%; "
          f"stable {100 * stable.mean():.1f}%")

print("Single Query in the human-coded sample (Section 4.5)")
wb = os.path.join(DATA_DIR, "humancode_sample1.xlsx")
sheet = lambda name: pd.read_excel(wb, name, dtype=str, keep_default_na=False)
cases = sheet("Case List")
cases = cases[cases["Case ID"].str.fullmatch(r"\d+") & (cases["Segment or Convo ID"] != "")]
length = seg.set_index("segment_id")["length"].reindex(cases["Segment or Convo ID"]).values
multi = length > 1
print(f"  sampled segments with more than one prompt: {multi.sum()}")
gem = clean_file("segment", "Gemini").set_index("segment_id")["QR"]
gem_sq = gem.reindex(cases["Segment or Convo ID"]).fillna("").values == "SINGLE_QUERY"
print(f"  labeled Single Query among them: Gemini {(gem_sq & multi).sum()}", end="")
for n in (1, 2):
    c = sheet(f"Coder {n}").set_index("Case ID").loc[cases["Case ID"], "Query Reformulation"]
    sq = c.str.strip().str.upper().values == "SINGLE QUERY"
    print(f", coder {n} {(sq & multi).sum()}", end="")
print()

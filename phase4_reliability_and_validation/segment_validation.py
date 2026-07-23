import pandas as pd

# Load segment data
df = pd.read_csv('analysis_results/segment/analysis_results_segment_gemini.csv')

print("=" * 70)
print("SEGMENT VALIDATION ANALYSIS")
print("=" * 70)

# Show column names to check
print("\nColumn names:")
print([col for col in df.columns if 'coherence' in col.lower() or 'stability' in col.lower()])

# Check coherence distribution (without number prefix)
print("\n" + "=" * 70)
print("Conversation Coherence:")
print("=" * 70)
print(df['conversation_coherence'].value_counts())

# Check topic stability
print("\n" + "=" * 70)
print("Topic Stability:")
print("=" * 70)
print(df['topic_stability'].value_counts())

# Calculate percentages for "high" coherence
high_coherence = df['conversation_coherence'].isin(['high', 'HIGH']).sum()
total = len(df)
pct = (high_coherence / total) * 100

print("\n" + "=" * 70)
print("SUMMARY STATISTICS:")
print("=" * 70)
print(f"Total segments: {total}")
print(f"High coherence: {high_coherence} ({pct:.1f}%)")

# Calculate stable topics
stable = df['topic_stability'].isin(['stable', 'STABLE']).sum()
pct_stable = (stable / total) * 100
print(f"Stable topics: {stable} ({pct_stable:.1f}%)")

# Combined score (both high coherence AND stable)
both_good = df[
    (df['conversation_coherence'].isin(['high', 'HIGH'])) & 
    (df['topic_stability'].isin(['stable', 'STABLE']))
].shape[0]
pct_both = (both_good / total) * 100

print(f"Both high coherence AND stable: {both_good} ({pct_both:.1f}%)")

print("\n" + "=" * 70)
print("INTERPRETATION:")
print("=" * 70)
if pct_both >= 80:
    print("✓ EXCELLENT: >80% of segments are coherent and stable")
    print("  → Strong validation of turn-based segmentation approach")
elif pct_both >= 60:
    print("✓ GOOD: 60-80% of segments are coherent and stable")
    print("  → Reasonable validation with acknowledged limitations")
elif pct_both >= 40:
    print("⚠ MODERATE: 40-60% of segments are coherent and stable")
    print("  → Note as limitation, use theoretical justification")
else:
    print("✗ WEAK: <40% of segments are coherent and stable")
    print("  → Do NOT claim empirical validation, use theory only")

print("=" * 70)

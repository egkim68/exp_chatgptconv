"""Draws Figure 1 (analytical workflow diagram). No data required. Writes figure1.png."""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
plt.rcParams['font.family'] = 'DejaVu Sans'
fig, ax = plt.subplots(figsize=(8.6, 11.6))
ax.set_xlim(0, 100); ax.set_ylim(0, 146); ax.axis('off')
TS, SS = 12.5, 10.5


def box(x, y, w, h, title, sub, fc='#E8EEF4', ec='#2F4B66'):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.4,rounding_size=1.2",
                                fc=fc, ec=ec, lw=1.2))
    ax.text(x + w / 2, y + h - 2.1, title, ha='center', va='center', fontsize=TS,
            weight='bold', color='#1B2B3A')
    ax.text(x + w / 2, (y + h - 4.0 + y) / 2, sub, ha='center', va='center', fontsize=SS,
            color='#1B2B3A', linespacing=1.4)


def arrow(x1, y1, x2, y2):
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle='-|>', color='#333333', lw=1.1, mutation_scale=12))


def phase(y, label):
    ax.text(0, y, label, ha='left', va='center', fontsize=12, weight='bold',
            color='#2F4B66', linespacing=1.2)


X, W, C = 20, 78, 59
box(X, 131, W, 13.5, 'Data Collection',
    '42 LIS undergraduates, UIN Alauddin Makassar\nExports submitted October 22 to November 10, 2025\n1,476 ChatGPT conversations; 15,900 messages')
arrow(C, 131, C, 126.5)
box(X, 114.5, W, 11, 'Unit Construction',
    'Conversation level: 1,476 conversations\nSegment level: 2,210 rule-based segments')
arrow(C, 114.5, C, 110)
phase(103.5, 'Phase 1')
box(X, 96, W, 13.5, 'Standardized Summarization (GPT-4o Mini)',
    '300-word English summaries of 1,475 conversations\n(one lacked a summary) and 2,210 segments')
arrow(47, 96, 38, 90.2); arrow(71, 96, 80, 90.2)
phase(82, 'Phases\n2 and 3')
box(X, 74.5, 35, 15, 'Claude 3 Haiku', 'Classifies all\nconversation and\nsegment summaries', fc='#DCEBFA')
box(X + W - 35, 74.5, 35, 15, 'Gemini 2.0 Flash', 'Classifies all\nconversation and\nsegment summaries', fc='#DDF1DD')
arrow(38, 74.5, 51, 69.8); arrow(80, 74.5, 67, 69.8)
box(X, 52, W, 17, 'Four Analytical Dimensions',
    'Academic Output Type (10 categories)\nCognitive Complexity (6 Bloom levels)\nTopical Focus and LIS Context (12 options)\nQuery Reformulation (11 patterns)',
    fc='#F7F7F7', ec='#777777')
arrow(C, 52, C, 47.5)
phase(38.5, 'Phase 4')
box(X, 29.5, W, 17.5, 'Comparative and Validation Analyses',
    "Cohen's κ and percent agreement\nStuart-Maxwell test; index of dissimilarity\nSensitivity analysis: κ on codebook-valid pairs\nModel-rated segment coherence and stability",
    fc='#FFF1D6', ec='#A56A00')
arrow(C, 29.5, C, 25)
box(X, 10, W, 14.5, 'Human Benchmark',
    'Two independent coders, 100 random segments;\nκ between coders and between\neach coder and each model', fc='#F3E6F5', ec='#6B3A78')
plt.savefig('figure1.png', dpi=600, bbox_inches='tight', facecolor='white')

"""Renders the cosine similarity matrix as a heatmap PNG."""

import matplotlib.pyplot as plt
import numpy as np

from vsm import build_similarity_matrix

names, vocab, tfidf_vectors, sim_matrix = build_similarity_matrix("docs")
labels = [n.replace(".txt", "").replace("doc", "d") for n in names]
short = [f"d{i+1}" for i in range(len(names))]

fig, ax = plt.subplots(figsize=(7.5, 6.5))
im = ax.imshow(sim_matrix, cmap="viridis", vmin=0, vmax=1)

ax.set_xticks(range(len(short)))
ax.set_yticks(range(len(short)))
ax.set_xticklabels(short)
ax.set_yticklabels(short)

for i in range(len(short)):
    for j in range(len(short)):
        val = sim_matrix[i, j]
        color = "white" if val < 0.5 else "black"
        ax.text(j, i, f"{val:.2f}", ha="center", va="center", color=color, fontsize=9)

ax.set_title("Cosine Similarity Matrix (TF-IDF Vector Space Model)")
fig.colorbar(im, ax=ax, label="Cosine similarity")
fig.tight_layout()
fig.savefig("screenshots/04_similarity_heatmap.png", dpi=150)
print("wrote screenshots/04_similarity_heatmap.png")

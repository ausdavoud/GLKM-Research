import argparse
import csv
import time
from pathlib import Path

import numpy as np
from scipy import sparse
from scipy.sparse.csgraph import connected_components
from sklearn.cluster import AgglomerativeClustering, KMeans
from sklearn.datasets import make_moons
from sklearn.metrics import normalized_mutual_info_score
from sklearn.neighbors import NearestNeighbors

from GKM import GKM
from LKM.FLK import FLK
from FeiPub import Gfuns, IFuns
from FeiPub.kpp import kpp_warm_start_labels


PALETTE = [
    "#440154",
    "#31688e",
    "#35b779",
    "#fde725",
    "#21918c",
    "#5ec962",
    "#3b528b",
    "#90d743",
    "#472d7b",
    "#20a486",
]


def relabel(y):
    mapping = {}
    out = np.empty(len(y), dtype=np.int32)
    for i, label in enumerate(y):
        if int(label) not in mapping:
            mapping[int(label)] = len(mapping)
        out[i] = mapping[int(label)]
    return out


def two_spirals(n=1200, turns=1.05, noise=0.08, seed=0):
    rng = np.random.default_rng(seed)
    n1 = n // 2
    n2 = n - n1
    theta = np.linspace(0.45, turns * 2 * np.pi, n1)
    radius = theta

    arm1 = np.column_stack([radius * np.cos(theta), radius * np.sin(theta)])
    arm2 = np.column_stack([radius * np.cos(theta + np.pi), radius * np.sin(theta + np.pi)])
    x = np.vstack([arm1, arm2[:n2]])
    x += rng.normal(scale=noise, size=x.shape)

    y = np.ones(len(x), dtype=np.int32)
    y[:n1] = 0
    return x, y


def arc(center, radius, start, stop, n, noise, rng):
    theta = np.linspace(start, stop, n)
    x = np.column_stack([radius * np.cos(theta), radius * np.sin(theta)])
    x += rng.normal(scale=noise, size=x.shape)
    return x + np.asarray(center)


def ring(center, radius, n, width, rng):
    theta = rng.random(n) * 2 * np.pi
    r = radius + rng.normal(scale=width, size=n)
    return np.column_stack([r * np.cos(theta), r * np.sin(theta)]) + np.asarray(center)


def gaussian(center, cov, n, rng):
    return rng.multivariate_normal(np.asarray(center), np.asarray(cov), n)


def compound_blobs(n_per_cluster=180, seed=0):
    rng = np.random.default_rng(seed)
    parts = [
        arc((-3.4, 1.0), 0.9, 0.45 * np.pi, 1.55 * np.pi, n_per_cluster, 0.06, rng),
        gaussian((-1.0, 1.45), [[0.05, 0.0], [0.0, 0.05]], n_per_cluster // 2, rng),
        gaussian((1.4, 1.1), [[0.08, 0.0], [0.0, 0.28]], n_per_cluster, rng),
        gaussian((-1.1, -1.25), [[0.25, 0.0], [0.0, 0.16]], n_per_cluster, rng),
        gaussian((2.3, -0.75), [[0.06, 0.0], [0.0, 0.25]], n_per_cluster, rng),
    ]
    x = np.vstack(parts)
    y = np.concatenate([np.full(len(p), i, dtype=np.int32) for i, p in enumerate(parts)])
    return x, y


def smile(n=1100, seed=0):
    rng = np.random.default_rng(seed)
    outer = arc((0.0, 0.0), 3.2, 1.05 * np.pi, 1.95 * np.pi, n // 2, 0.12, rng)
    inner = arc((0.0, 0.55), 1.45, 1.05 * np.pi, 1.95 * np.pi, n - n // 2, 0.12, rng)
    x = np.vstack([outer, inner])
    y = np.concatenate([np.zeros(len(outer), dtype=np.int32), np.ones(len(inner), dtype=np.int32)])
    return x, y


def ring_and_satellites(n_ring=720, n_sat=110, seed=0):
    rng = np.random.default_rng(seed)
    parts = [ring((0.0, 0.0), 2.0, n_ring, 0.055, rng)]
    for center in [(-3.0, 2.6), (3.0, 2.6), (-3.0, -2.6), (3.0, -2.6)]:
        parts.append(ring(center, 0.55, n_sat, 0.045, rng))
    x = np.vstack(parts)
    y = np.concatenate([np.full(len(p), i, dtype=np.int32) for i, p in enumerate(parts)])
    return x, y


def sparse_spiral(n=110, seed=0):
    return two_spirals(n=n, turns=0.9, noise=0.03, seed=seed)


def toy_datasets(seed=0, scale=1.0):
    def scaled(n):
        return max(40, int(round(n * scale)))

    datasets = []
    datasets.append(("compound",) + compound_blobs(scaled(180), seed=seed + 1))
    x, y = make_moons(n_samples=scaled(1100), noise=0.06, random_state=seed + 2)
    datasets.append(("moons", x.astype(np.float64), y.astype(np.int32)))
    datasets.append(("rings+blobs",) + ring_and_satellites(scaled(720), scaled(110), seed=seed + 3))
    datasets.append(("spirals",) + two_spirals(scaled(1200), turns=1.05, noise=0.08, seed=seed + 4))
    datasets.append(("sparse spiral",) + sparse_spiral(scaled(110), seed=seed + 5))
    return datasets


def build_knn(X, knn):
    NN, NND = Gfuns.knn_nn(X, min(knn, len(X) - 1), squared=True)
    return NN.astype(np.int32), NND.astype(np.float64)


def run_kmeans_pp(X, c, seed):
    return KMeans(n_clusters=c, init="k-means++", n_init=20, random_state=seed).fit_predict(X)


def run_hac_ward(X, c):
    return AgglomerativeClustering(n_clusters=c, linkage="ward").fit_predict(X)


def first_neighbor_partition(X):
    n = len(X)
    nn = NearestNeighbors(n_neighbors=2).fit(X).kneighbors(return_distance=False)
    first = nn[:, 1]
    rows = []
    cols = []

    for i, j in enumerate(first):
        rows.extend([i, int(j)])
        cols.extend([int(j), i])

    groups = {}
    for i, j in enumerate(first):
        groups.setdefault(int(j), []).append(i)
    for members in groups.values():
        root = members[0]
        for member in members[1:]:
            rows.extend([root, member])
            cols.extend([member, root])

    data = np.ones(len(rows), dtype=np.int8)
    graph = sparse.csr_matrix((data, (rows, cols)), shape=(n, n))
    _, labels = connected_components(graph, directed=False)
    return relabel(labels)


def centroids_from_labels(X, labels):
    labels = relabel(labels)
    return np.vstack([X[labels == i].mean(axis=0) for i in range(labels.max() + 1)])


def merge_partition_to_c(X, labels, c):
    labels = relabel(labels)
    k = labels.max() + 1
    if k == c:
        return labels
    if k < c:
        return run_hac_ward(X, c)

    centroids = centroids_from_labels(X, labels)
    merged = run_hac_ward(centroids, c)
    return relabel(merged[labels])


def run_finch_style(X, c):
    # This is a compact FINCH-style baseline. The official FINCH package is not
    # included in this repository, so this reproduces its first-neighbor idea and
    # then merges the hierarchy to the requested number of clusters.
    current_x = X
    original_to_current = np.arange(len(X), dtype=np.int32)
    best_labels = None
    best_k = len(X)

    for _ in range(20):
        step_labels = first_neighbor_partition(current_x)
        k = int(step_labels.max() + 1)
        labels = step_labels[original_to_current]
        if k >= c and k < best_k:
            best_labels = labels
            best_k = k
        if k <= c or k == len(current_x):
            break
        current_x = centroids_from_labels(current_x, step_labels)
        original_to_current = step_labels[original_to_current]

    if best_labels is None:
        best_labels = labels
    return merge_partition_to_c(X, best_labels, c)


def run_graph_kmeans_like(NN, NND, c, init_labels, iterations):
    # Approximation for the paper's missing GK-means baseline: optimize the same
    # sparse graph objective with FLK, initialized by k-means++.
    mod = FLK(NN=NN, NND=NND, max_d=-1, c_true=int(c), debug=False)
    mod.opt(ITER=iterations, init_Y=[relabel(init_labels).astype(np.int32)])
    return relabel(mod.Y[0])


def run_glkm(NN, NND, c, cd_iter):
    obj = GKM(NN=NN, NND=NND, c_true=int(c), debug=0)
    obj.opt()
    y = obj.y_pred.astype(np.int32)
    if cd_iter <= 0:
        return relabel(y)

    mod = FLK(NN=NN, NND=NND, max_d=-1, c_true=int(c), debug=False)
    init_y = np.asarray(IFuns.replace_with_continuous(y), dtype=np.int32)
    mod.opt(ITER=cd_iter, init_Y=[init_y])
    return relabel(mod.Y[0])


def run_glkm_kpp(X, NN, NND, c, cd_iter, factor, seed, n_init):
    init_labels = kpp_warm_start_labels(
        X,
        c_true=int(c),
        factor=factor,
        random_state=seed,
        n_init=n_init,
    )
    obj = GKM(NN=NN, NND=NND, c_true=int(c), debug=0, init_labels=init_labels)
    obj.opt()
    y = obj.y_pred.astype(np.int32)
    if cd_iter <= 0:
        return relabel(y)

    mod = FLK(NN=NN, NND=NND, max_d=-1, c_true=int(c), debug=False)
    init_y = np.asarray(IFuns.replace_with_continuous(y), dtype=np.int32)
    mod.opt(ITER=cd_iter, init_Y=[init_y])
    return relabel(mod.Y[0])


def run_all_methods(X, y_true, knn, seed, cd_iter, gk_iter, kpp_init, kpp_factor, kpp_n_init):
    c = int(len(np.unique(y_true)))
    NN, NND = build_knn(X, knn)
    methods = []

    t0 = time.perf_counter()
    kmeans_labels = relabel(run_kmeans_pp(X, c, seed))
    methods.append(("k-means++", kmeans_labels, time.perf_counter() - t0))

    t0 = time.perf_counter()
    methods.append(("FINCH", run_finch_style(X, c), time.perf_counter() - t0))

    t0 = time.perf_counter()
    methods.append(("GK-means", run_graph_kmeans_like(NN, NND, c, kmeans_labels, gk_iter), time.perf_counter() - t0))

    t0 = time.perf_counter()
    methods.append(("HAC_Ward", relabel(run_hac_ward(X, c)), time.perf_counter() - t0))

    t0 = time.perf_counter()
    methods.append(("GLKM", run_glkm(NN, NND, c, cd_iter), time.perf_counter() - t0))
    if kpp_init:
        t0 = time.perf_counter()
        methods.append((
            f"KPP+GLKM ({kpp_factor:g}k)",
            run_glkm_kpp(X, NN, NND, c, cd_iter, kpp_factor, seed, kpp_n_init),
            time.perf_counter() - t0,
        ))
    return methods


def suggested_knn(X, c, max_knn):
    samples_per_cluster = len(X) / c
    if samples_per_cluster < 80:
        return min(max_knn, max(3, len(X) // (c * 12)))
    return min(max_knn, len(X) - 1)


def nmi(y_true, y_pred):
    return float(normalized_mutual_info_score(y_true, y_pred, average_method="max"))


def scale_points(X, x, y, width, height, pad=8):
    xmin, ymin = X.min(axis=0)
    xmax, ymax = X.max(axis=0)
    xr = xmax - xmin
    yr = ymax - ymin
    if xr == 0:
        xr = 1.0
    if yr == 0:
        yr = 1.0
    scale = min((width - 2 * pad) / xr, (height - 2 * pad) / yr)
    used_w = xr * scale
    used_h = yr * scale
    ox = x + (width - used_w) / 2
    oy = y + (height - used_h) / 2
    px = ox + (X[:, 0] - xmin) * scale
    py = oy + used_h - (X[:, 1] - ymin) * scale
    return px, py


def labels_to_colors(labels):
    labels = relabel(labels)
    return [PALETTE[int(label) % len(PALETTE)] for label in labels]


def svg_text(text):
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def write_svg(results, path):
    panel_w = 145
    panel_h = 145
    gap_x = 14
    gap_y = 38
    left = 28
    top = 38
    label_h = 26
    cols = max(len(item["methods"]) for item in results)
    rows = len(results)
    width = left * 2 + cols * panel_w + (cols - 1) * gap_x
    height = top + rows * (panel_h + label_h) + (rows - 1) * gap_y + 42
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="white" />',
        "<style>",
        'text { font-family: "Times New Roman", Times, serif; fill: #111827; font-size: 14px; }',
        ".caption { font-size: 16px; font-weight: 700; }",
        ".panel-label { font-size: 13px; }",
        "</style>",
    ]

    letter = ord("a")
    for row_i, item in enumerate(results):
        X = item["X"]
        methods = item["methods"]
        y0 = top + row_i * (panel_h + label_h + gap_y)
        for col_i, (method, labels, score) in enumerate(methods):
            x0 = left + col_i * (panel_w + gap_x)
            px, py = scale_points(X, x0, y0, panel_w, panel_h)
            parts.append(f'<rect x="{x0}" y="{y0}" width="{panel_w}" height="{panel_h}" fill="white" stroke="#4b5563" stroke-width="1" />')
            colors = labels_to_colors(labels)
            radius = 1.7 if len(X) > 250 else 2.1
            for xi, yi, color in zip(px, py, colors):
                parts.append(f'<circle cx="{xi:.2f}" cy="{yi:.2f}" r="{radius}" fill="{color}" />')
            label = f"({chr(letter)}) {method}: {score:.3f}"
            parts.append(
                f'<text class="panel-label" x="{x0 + panel_w / 2:.1f}" y="{y0 + panel_h + 19:.1f}" '
                f'text-anchor="middle">{svg_text(label)}</text>'
            )
            letter += 1

    parts.append(
        f'<text class="caption" x="{width / 2:.1f}" y="{height - 16}" text-anchor="middle">'
        "Fig. 4. Visualization of toy datasets with NMI score for each algorithm."
        "</text>"
    )
    parts.append("</svg>")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(parts))


def write_csv(rows, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["dataset", "method", "n_clusters", "nmi", "seconds"])
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(description="Recreate a Figure-4-style toy-dataset comparison grid.")
    parser.add_argument("--out-dir", default="results/fig4")
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--scale", type=float, default=1.0, help="multiply toy dataset sizes; use 0.3 for a quick draft")
    parser.add_argument("--knn", type=int, default=20)
    parser.add_argument("--cd-iter", type=int, default=100, help="FLK refinement iterations after GLKM")
    parser.add_argument("--gk-iter", type=int, default=100, help="FLK iterations for the local GK-means approximation")
    parser.add_argument("--kpp-init", action="store_true", help="include KPP+GLKM in the comparison")
    parser.add_argument("--kpp-factor", type=float, default=4.0)
    parser.add_argument("--kpp-n-init", type=int, default=1)
    args = parser.parse_args()

    figure_rows = []
    table_rows = []
    for dataset_name, X, y_true in toy_datasets(seed=args.seed, scale=args.scale):
        c_true = len(np.unique(y_true))
        effective_knn = suggested_knn(X, c_true, args.knn)
        print(f"dataset={dataset_name} n={len(X)} c={c_true} knn={effective_knn}", flush=True)
        methods = run_all_methods(
            X,
            y_true,
            effective_knn,
            args.seed,
            args.cd_iter,
            args.gk_iter,
            args.kpp_init,
            args.kpp_factor,
            args.kpp_n_init,
        )

        scored_methods = []
        for method_name, labels, seconds in methods:
            score = nmi(y_true, labels)
            scored_methods.append((method_name, labels, score))
            table_rows.append(
                {
                    "dataset": dataset_name,
                    "method": method_name,
                    "n_clusters": int(len(np.unique(labels))),
                    "nmi": f"{score:.6f}",
                    "seconds": f"{seconds:.3f}",
                }
            )
            print(f"  {method_name:9s} nmi={score:.3f}", flush=True)
        figure_rows.append({"name": dataset_name, "X": X, "y_true": y_true, "methods": scored_methods})

    out_dir = Path(args.out_dir)
    svg_path = out_dir / "figure4.svg"
    csv_path = out_dir / "figure4_results.csv"
    write_svg(figure_rows, svg_path)
    write_csv(table_rows, csv_path)
    print(f"Wrote {svg_path}")
    print(f"Wrote {csv_path}")


if __name__ == "__main__":
    main()

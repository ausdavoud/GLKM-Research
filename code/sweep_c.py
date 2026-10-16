import argparse
import csv
import html
import time
from pathlib import Path

import numpy as np

from GKM import GKM
from LKM.FLK import FLK
from FeiPub import Gfuns, IFuns, Mfuns
from FeiPub.kpp import kpp_warm_start_labels, warm_start_cluster_count


def parse_c_values(text):
    if ":" in text:
        parts = [int(p) for p in text.split(":")]
        if len(parts) not in (2, 3):
            raise argparse.ArgumentTypeError("range syntax is start:stop[:step]")
        start, stop = parts[0], parts[1]
        step = parts[2] if len(parts) == 3 else 1
        if step == 0:
            raise argparse.ArgumentTypeError("step cannot be zero")
        return list(range(start, stop + (1 if step > 0 else -1), step))
    return [int(p.strip()) for p in text.split(",") if p.strip()]


def validate_c_values(values, n_samples):
    values = sorted(set(values))
    if not values:
        raise ValueError("at least one cluster count is required")
    if values[0] < 1 or values[-1] > n_samples:
        raise ValueError(f"cluster counts must be between 1 and {n_samples}")
    return values


def estimate_elbow(rows):
    points = sorted({int(row["c"]): float(row["gkm_loss"]) for row in rows}.items())
    if len(points) < 3:
        return None

    xy = np.asarray(points, dtype=np.float64)
    spans = np.ptp(xy, axis=0)
    if np.any(spans == 0):
        return None
    xy = (xy - xy.min(axis=0)) / spans

    chord = xy[-1] - xy[0]
    offsets = xy - xy[0]
    distances = np.abs(chord[0] * offsets[:, 1] - chord[1] * offsets[:, 0]) / np.linalg.norm(chord)
    distances[[0, -1]] = -1
    # ponytail: chord distance is a single-knee heuristic; use Kneedle if noisy curves become common.
    return points[int(np.argmax(distances))][0]


def load_dataset(data_dir, name, knn):
    path = Path(data_dir) / f"{name}.mat"
    if name == "D1":
        X, y_true, NN, NND, knn_time = IFuns.load_toy(str(path))
        return X, y_true.astype(np.int32), NN, NND, float(knn_time)

    X, y_true, N, _, c_true = IFuns.loadmat(str(path))
    t0 = time.perf_counter()
    NN, NND = Gfuns.knn_nn(X, min(knn, N - 1), squared=True)
    return X, y_true.astype(np.int32), NN, NND, time.perf_counter() - t0


def run_once(NN, NND, y_true, c, cd_iter, init_labels=None, init_seconds=0.0):
    total_t0 = time.perf_counter()
    t0 = time.perf_counter()
    obj = GKM(
        NN=NN.astype(np.int32),
        NND=NND.astype(np.float64),
        c_true=int(c),
        debug=0,
        init_labels=init_labels,
    )
    obj.opt()
    gkm_elapsed = time.perf_counter() - t0
    y_pred = obj.y_pred.astype(np.int32)

    if cd_iter > 0:
        init_y = [np.asarray(IFuns.replace_with_continuous(y_pred), dtype=np.int32)]
        mod = FLK(
            NN=NN.astype(np.int32),
            NND=NND.astype(np.float64),
            max_d=-1,
            c_true=int(c),
            debug=False,
        )
        mod.opt(ITER=cd_iter, init_Y=init_y)
        y_pred = mod.Y[0].astype(np.int32)

    return {
        "c": int(c),
        "n_clusters": int(len(np.unique(y_pred))),
        "gkm_loss": float(obj.loss),
        "connected": bool(obj.connected),
        "cd_iter": int(cd_iter),
        "init_elapsed_sec": float(init_seconds),
        "gkm_elapsed_sec": gkm_elapsed,
        "total_elapsed_sec": float(init_seconds) + time.perf_counter() - total_t0,
        "acc": float(Mfuns.accuracy(y_true.copy(), y_pred)),
        "nmi": float(Mfuns.nmi(y_true.copy(), y_pred)),
        "purity": float(Mfuns.purity(y_true.copy(), y_pred)),
        "ari": float(Mfuns.ari(y_true.copy(), y_pred)),
    }


def write_csv(rows, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_svg(rows, path, title, estimated_k=None):
    methods = list(dict.fromkeys(r.get("method", "raw") for r in rows))
    xs = [r["c"] for r in rows]
    ys = [r["gkm_loss"] for r in rows]
    w, h = 880, 520
    ml, mr, mt, mb = 82, 30, 52, 70
    pw, ph = w - ml - mr, h - mt - mb
    xmin, xmax = min(xs), max(xs)
    ymin, ymax = min(ys), max(ys)
    if xmin == xmax:
        xmin -= 1
        xmax += 1
    if ymin == ymax:
        ymin -= 1
        ymax += 1

    def sx(x):
        return ml + (x - xmin) / (xmax - xmin) * pw

    def sy(y):
        return mt + (ymax - y) / (ymax - ymin) * ph

    colors = {"raw": "#2563eb", "kpp+glkm": "#dc2626"}
    series_svg = []
    for method in methods:
        method_rows = [r for r in rows if r.get("method", "raw") == method]
        method_rows.sort(key=lambda r: r["c"])
        color = colors.get(method, "#475569")
        points = " ".join(f"{sx(r['c']):.1f},{sy(r['gkm_loss']):.1f}" for r in method_rows)
        series_svg.append(f'<polyline points="{points}" fill="none" stroke="{color}" stroke-width="2.5" />')
        for row in method_rows:
            series_svg.append(f'<circle cx="{sx(row["c"]):.1f}" cy="{sy(row["gkm_loss"]):.1f}" r="4.5" fill="{color}" />')
    legend_svg = []
    for i, method in enumerate(methods):
        x0 = ml + 12 + i * 130
        y0 = mt - 20
        color = colors.get(method, "#475569")
        legend_svg.append(f'<line x1="{x0}" y1="{y0}" x2="{x0 + 28}" y2="{y0}" stroke="{color}" stroke-width="2.5" />')
        legend_svg.append(f'<text x="{x0 + 36}" y="{y0 + 4}">{method}</text>')
    x_ticks = np.linspace(xmin, xmax, min(8, len(set(xs))))
    y_ticks = np.linspace(ymin, ymax, 6)
    tick_svg = []
    for x in x_ticks:
        px = sx(float(x))
        tick_svg.append(f'<line x1="{px:.1f}" y1="{mt + ph}" x2="{px:.1f}" y2="{mt + ph + 6}" stroke="#475569" />')
        tick_svg.append(f'<text x="{px:.1f}" y="{mt + ph + 25}" text-anchor="middle">{x:.0f}</text>')
    for y in y_ticks:
        py = sy(float(y))
        tick_svg.append(f'<line x1="{ml - 6}" y1="{py:.1f}" x2="{ml}" y2="{py:.1f}" stroke="#475569" />')
        tick_svg.append(f'<text x="{ml - 10}" y="{py + 4:.1f}" text-anchor="end">{y:.3g}</text>')
        tick_svg.append(f'<line x1="{ml}" y1="{py:.1f}" x2="{ml + pw}" y2="{py:.1f}" stroke="#e2e8f0" />')

    elbow_svg = ""
    if estimated_k is not None:
        elbow_x = sx(estimated_k)
        elbow_svg = (
            f'<line x1="{elbow_x:.1f}" y1="{mt}" x2="{elbow_x:.1f}" y2="{mt + ph}" '
            'stroke="#dc2626" stroke-width="2" stroke-dasharray="7 6" />'
            f'<text x="{elbow_x + 8:.1f}" y="{mt + 18}" fill="#dc2626">estimated k = {estimated_k}</text>'
        )

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">
<rect width="100%" height="100%" fill="white" />
<style>
text {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; fill: #0f172a; font-size: 13px; }}
.title {{ font-size: 20px; font-weight: 650; }}
.label {{ font-size: 14px; font-weight: 600; }}
</style>
<text x="{w / 2}" y="30" text-anchor="middle" class="title">{html.escape(title)}</text>
{"".join(tick_svg)}
<line x1="{ml}" y1="{mt}" x2="{ml}" y2="{mt + ph}" stroke="#0f172a" />
<line x1="{ml}" y1="{mt + ph}" x2="{ml + pw}" y2="{mt + ph}" stroke="#0f172a" />
{"".join(legend_svg)}
{"".join(series_svg)}
{elbow_svg}
<text x="{ml + pw / 2}" y="{h - 22}" text-anchor="middle" class="label">number of clusters c</text>
<text x="22" y="{mt + ph / 2}" text-anchor="middle" transform="rotate(-90 22 {mt + ph / 2})" class="label">GLKM objective</text>
</svg>
'''
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(svg)


def main():
    parser = argparse.ArgumentParser(description="Sweep GLKM over cluster counts and save an elbow curve.")
    parser.add_argument("--dataset", default="Gisette", help="dataset name under --data-dir, without .mat")
    parser.add_argument("--data-dir", default="./dataset")
    parser.add_argument("--knn", type=int, default=80, help="KNN graph size for datasets without precomputed NN/NND")
    parser.add_argument("--c-values", required=True, type=parse_c_values, help="comma list or start:stop[:step], e.g. 2:20 or 10,20,30")
    parser.add_argument("--cd-iter", type=int, default=0, help="optional FLK coordinate-descent iterations after GLKM")
    parser.add_argument("--kpp-init", action="store_true", help="run only KPP+GLKM unless --compare-raw is also set")
    parser.add_argument("--kpp-factor", type=float, default=4.0)
    parser.add_argument("--kpp-random-state", type=int, default=0)
    parser.add_argument("--kpp-n-init", type=int, default=1)
    parser.add_argument("--compare-raw", action="store_true", help="write both raw GLKM and KPP+GLKM rows")
    parser.add_argument("--out-dir", default="results/elbow")
    args = parser.parse_args()

    X, y_true, NN, NND, knn_time = load_dataset(args.data_dir, args.dataset, args.knn)
    try:
        c_values = validate_c_values(args.c_values, len(X))
    except ValueError as exc:
        parser.error(str(exc))

    rows = []
    for c in c_values:
        run_raw = args.compare_raw or not args.kpp_init
        run_kpp = args.compare_raw or args.kpp_init

        if run_raw:
            print(f"running raw c={c} ...", flush=True)
            row = run_once(NN, NND, y_true, c, args.cd_iter)
            row["method"] = "raw"
            row["kpp_factor"] = ""
            row["kpp_start_clusters"] = ""
            rows.append(row)
            print(
                f"raw c={row['c']} loss={row['gkm_loss']:.6g} "
                f"nmi={row['nmi']:.3f} acc={row['acc']:.3f} "
                f"time={row['total_elapsed_sec']:.2f}s",
                flush=True,
            )

        if run_kpp:
            print(f"running kpp+glkm c={c} ...", flush=True)
            init_t0 = time.perf_counter()
            init_labels = kpp_warm_start_labels(
                X,
                c_true=c,
                factor=args.kpp_factor,
                random_state=args.kpp_random_state,
                n_init=args.kpp_n_init,
            )
            init_seconds = time.perf_counter() - init_t0
            row = run_once(
                NN,
                NND,
                y_true,
                c,
                args.cd_iter,
                init_labels=init_labels,
                init_seconds=init_seconds,
            )
            row["method"] = "kpp+glkm"
            row["kpp_factor"] = float(args.kpp_factor)
            row["kpp_start_clusters"] = warm_start_cluster_count(c, len(X), factor=args.kpp_factor)
            rows.append(row)
            print(
                f"kpp+glkm c={row['c']} loss={row['gkm_loss']:.6g} "
                f"nmi={row['nmi']:.3f} acc={row['acc']:.3f} "
                f"time={row['total_elapsed_sec']:.2f}s",
                flush=True,
            )

    out_dir = Path(args.out_dir) / args.dataset
    csv_path = out_dir / "sweep_c.csv"
    svg_path = out_dir / "elbow.svg"
    estimate_path = out_dir / "estimated_k.txt"
    # the elbow is read off plain GLKM; warm-started rows would mix two curves
    estimated_k = estimate_elbow([r for r in rows if r.get("method", "raw") == "raw"] or rows)
    write_csv(rows, csv_path)
    write_svg(rows, svg_path, f"{args.dataset}: GLKM elbow curve", estimated_k)
    estimate_path.write_text("unavailable\n" if estimated_k is None else f"{estimated_k}\n")
    print(f"KNN time: {knn_time:.2f}s")
    print(f"Estimated k: {estimated_k if estimated_k is not None else 'unavailable'}")
    print(f"Wrote {csv_path}")
    print(f"Wrote {svg_path}")
    print(f"Wrote {estimate_path}")


if __name__ == "__main__":
    main()

import time

import numpy as np

from GKM import GKM
from LKM.FLK import FLK
from FeiPub import IFuns, Mfuns
from FeiPub.kpp import kpp_warm_start_labels, warm_start_cluster_count


def _as_graph_arrays(NN, NND):
    return NN.astype(np.int32), NND.astype(np.float64)


def refine_with_flk(NN, NND, labels, c_true, cd_iter):
    if cd_iter <= 0:
        return labels.astype(np.int32), 0.0

    init_y = [np.asarray(IFuns.replace_with_continuous(labels), dtype=np.int32)]
    t0 = time.perf_counter()
    mod = FLK(
        NN=NN.astype(np.int32),
        NND=NND.astype(np.float64),
        max_d=-1,
        c_true=int(c_true),
        debug=False,
    )
    mod.opt(ITER=int(cd_iter), init_Y=init_y)
    return mod.Y[0].astype(np.int32), time.perf_counter() - t0


def run_glkm_once(NN, NND, c_true, init_labels=None, cd_iter=0, debug=0, init_seconds=0.0):
    NN, NND = _as_graph_arrays(NN, NND)
    t0 = time.perf_counter()
    obj = GKM(
        NN=NN,
        NND=NND,
        c_true=int(c_true),
        debug=int(debug),
        init_labels=init_labels,
    )
    obj.opt()
    gkm_seconds = time.perf_counter() - t0
    labels, flk_seconds = refine_with_flk(NN, NND, obj.y_pred.astype(np.int32), c_true, cd_iter)

    return {
        "labels": labels,
        "gkm_loss": float(obj.loss),
        "connected": bool(obj.connected),
        "init_seconds": float(init_seconds),
        "gkm_seconds": gkm_seconds,
        "flk_seconds": flk_seconds,
        "total_seconds": float(init_seconds) + gkm_seconds + flk_seconds,
        "start_clusters": int(NN.shape[0] if init_labels is None else len(np.unique(init_labels))),
    }


def add_metrics(result, y_true):
    labels = result["labels"]
    result["acc"] = float(Mfuns.accuracy(y_true.copy(), labels))
    result["nmi"] = float(Mfuns.nmi(y_true.copy(), labels))
    result["purity"] = float(Mfuns.purity(y_true.copy(), labels))
    result["ari"] = float(Mfuns.ari(y_true.copy(), labels))
    result["n_clusters"] = int(len(np.unique(labels)))
    return result


def compare_raw_vs_kpp(
    X,
    y_true,
    NN,
    NND,
    c_true,
    kpp_factor=4,
    kpp_random_state=0,
    kpp_n_init=1,
    cd_iter=0,
    debug=0,
):
    raw = run_glkm_once(NN, NND, c_true, init_labels=None, cd_iter=cd_iter, debug=debug)
    t0 = time.perf_counter()
    init_labels = kpp_warm_start_labels(
        X,
        c_true=c_true,
        factor=kpp_factor,
        random_state=kpp_random_state,
        n_init=kpp_n_init,
    )
    init_seconds = time.perf_counter() - t0
    kpp = run_glkm_once(
        NN,
        NND,
        c_true,
        init_labels=init_labels,
        cd_iter=cd_iter,
        debug=debug,
        init_seconds=init_seconds,
    )

    raw["method"] = "raw"
    raw["kpp_factor"] = None
    raw["kpp_start_clusters"] = None
    kpp["method"] = "kpp+glkm"
    kpp["kpp_factor"] = float(kpp_factor)
    kpp["kpp_start_clusters"] = warm_start_cluster_count(c_true, len(X), factor=kpp_factor)

    return add_metrics(raw, y_true), add_metrics(kpp, y_true)


def print_comparison(rows):
    print()
    print("GLKM comparison")
    print("-" * 104)
    print(
        f"{'method':<16} {'acc':>8} {'nmi':>8} {'purity':>8} {'ari':>8} "
        f"{'loss':>12} {'start':>8} {'clusters':>8} {'time(s)':>10} {'connected':>10}"
    )
    for row in rows:
        print(
            f"{row['method']:<16} {row['acc']:8.3f} {row['nmi']:8.3f} "
            f"{row['purity']:8.3f} {row['ari']:8.3f} {row['gkm_loss']:12.5g} "
            f"{row['start_clusters']:8d} {row['n_clusters']:8d} "
            f"{row['total_seconds']:10.3f} {str(row['connected']):>10}"
        )

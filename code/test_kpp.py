import numpy as np

from FeiPub import Gfuns
from FeiPub.glkm_runner import run_glkm_once
from GKM import GKM


def demo():
    rng = np.random.default_rng(0)
    X = np.vstack([rng.normal(-2, 0.2, (12, 2)), rng.normal(2, 0.2, (12, 2))])
    NN, NND = Gfuns.knn_nn(X, knn=8, squared=True)

    raw = run_glkm_once(NN, NND, c_true=2)
    singleton = run_glkm_once(NN, NND, c_true=2, init_labels=np.arange(len(X), dtype=np.int32))
    assert np.array_equal(raw["labels"], singleton["labels"])
    assert np.isclose(raw["gkm_loss"], singleton["gkm_loss"])

    timed = run_glkm_once(NN, NND, c_true=2, init_seconds=1.25)
    assert np.isclose(timed["total_seconds"], timed["gkm_seconds"] + timed["flk_seconds"] + 1.25)

    try:
        GKM(NN=NN, NND=NND, c_true=3, debug=0, init_labels=np.repeat([0, 1], len(X) // 2))
    except ValueError:
        pass
    else:
        raise AssertionError("fewer initial clusters than c_true must be rejected")


if __name__ == "__main__":
    demo()

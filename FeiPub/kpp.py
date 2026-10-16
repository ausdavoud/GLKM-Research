import math

import numpy as np
from sklearn.cluster import KMeans


def warm_start_cluster_count(c_true, n_samples, factor=4):
    if c_true <= 0:
        raise ValueError("c_true must be positive")
    if n_samples <= 0:
        raise ValueError("n_samples must be positive")
    if factor < 1:
        raise ValueError("factor must be >= 1")

    count = int(math.ceil(float(factor) * int(c_true)))
    return max(int(c_true), min(count, int(n_samples)))


def kpp_warm_start_labels(X, c_true, factor=4, random_state=0, n_init=1):
    X = np.asarray(X, dtype=np.float64)
    count = warm_start_cluster_count(c_true, X.shape[0], factor=factor)
    model = KMeans(
        n_clusters=count,
        init="k-means++",
        n_init=n_init,
        random_state=random_state,
    )
    return model.fit_predict(X).astype(np.int32)

import argparse

import numpy as np

from FeiPub import IFuns
from FeiPub.glkm_runner import add_metrics, compare_raw_vs_kpp, print_comparison, run_glkm_once
from FeiPub.kpp import kpp_warm_start_labels


def parse_args():
    parser = argparse.ArgumentParser(description="Run GLKM on a toy dataset with precomputed NN/NND.")
    parser.add_argument("--data-path", default="./dataset/")
    parser.add_argument("--data-name", default="D1")
    parser.add_argument("--cd-iter", type=int, default=100)
    parser.add_argument("--kpp-init", action="store_true")
    parser.add_argument("--kpp-factor", type=float, default=4.0)
    parser.add_argument("--kpp-random-state", type=int, default=0)
    parser.add_argument("--kpp-n-init", type=int, default=1)
    parser.add_argument("--no-compare-raw", action="store_true")
    return parser.parse_args()


def main():
    args = parse_args()
    X, y_true, NN, NND, knn_time = IFuns.load_toy(f"{args.data_path}{args.data_name}.mat")
    k = len(np.unique(y_true))
    print(f"K is {k}")

    if not args.no_compare_raw:
        raw, kpp = compare_raw_vs_kpp(
            X=X,
            y_true=y_true,
            NN=NN,
            NND=NND,
            c_true=k,
            kpp_factor=args.kpp_factor,
            kpp_random_state=args.kpp_random_state,
            kpp_n_init=args.kpp_n_init,
            cd_iter=args.cd_iter,
        )
        print_comparison([raw, kpp])
        return

    init_labels = None
    method = "raw"
    if args.kpp_init:
        init_labels = kpp_warm_start_labels(
            X,
            c_true=k,
            factor=args.kpp_factor,
            random_state=args.kpp_random_state,
            n_init=args.kpp_n_init,
        )
        method = "kpp+glkm"

    result = run_glkm_once(NN, NND, k, init_labels=init_labels, cd_iter=args.cd_iter)
    result["method"] = method
    add_metrics(result, y_true)
    print_comparison([result])


if __name__ == "__main__":
    main()

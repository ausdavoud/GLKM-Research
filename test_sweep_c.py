from sweep_c import estimate_elbow, parse_c_values, validate_c_values


def demo():
    assert parse_c_values("2:6:2") == [2, 4, 6]
    assert validate_c_values([4, 2, 4, 3], 10) == [2, 3, 4]
    assert estimate_elbow([
        {"c": 2, "gkm_loss": 100},
        {"c": 3, "gkm_loss": 55},
        {"c": 4, "gkm_loss": 40},
        {"c": 5, "gkm_loss": 34},
        {"c": 6, "gkm_loss": 31},
    ]) == 3


if __name__ == "__main__":
    demo()

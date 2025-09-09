from metrics.index import compute_index

def test_compute_index():
    assert compute_index(120, 100) == 20.0
    assert compute_index(100, 100) == 0.0
    assert compute_index(80, 100) == -20.0
    assert compute_index(100, 0) != compute_index(100, 0)  # nan

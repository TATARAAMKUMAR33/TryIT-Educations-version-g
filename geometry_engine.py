import random, math
CANVAS = 100
def _reflect_vertical(p): return (CANVAS - p[0], p[1])
def _reflect_horizontal(p): return (p[0], CANVAS - p[1])
def _points_close(a, b, tol=2.0): return math.hypot(a[0] - b[0], a[1] - b[1]) <= tol
def _dedupe_close(points, tol=2.0):
    out = []
    for p in points:
        if not any(_points_close(p, q, tol) for q in out): out.append(p)
    return out
def generate_paper_fold_geometry(num_folds: int = 2, rng: random.Random = None) -> dict:
    rng = rng or random.Random()
    fold_types = rng.sample(["vertical", "horizontal"], k=min(num_folds, 2))
    if num_folds > 2: fold_types = fold_types + ["vertical"]
    margin = 12; half = CANVAS / (2 if len(fold_types) >= 1 else 1)
    px = rng.uniform(margin, half - margin) if "vertical" in fold_types else rng.uniform(margin, CANVAS - margin)
    py = rng.uniform(margin, half - margin) if "horizontal" in fold_types else rng.uniform(margin, CANVAS - margin)
    punch = (round(px, 1), round(py, 1))
    correct_holes = [punch]
    for fold in fold_types:
        reflector = _reflect_vertical if fold == "vertical" else _reflect_horizontal
        correct_holes = correct_holes + [reflector(p) for p in correct_holes]
    correct_holes = _dedupe_close(correct_holes)
    decoys = []
    only_first = [punch]
    if fold_types:
        reflector = _reflect_vertical if fold_types[0] == "vertical" else _reflect_horizontal
        only_first = only_first + [reflector(p) for p in only_first]
    decoys.append(_dedupe_close(only_first))
    shifted = list(correct_holes)
    if shifted:
        idx = rng.randrange(len(shifted)); sx, sy = shifted[idx]
        shifted[idx] = (round(min(max(sx + rng.choice([-18, 18]), 2), CANVAS - 2), 1), round(min(max(sy + rng.choice([-18, 18]), 2), CANVAS - 2), 1)) 
    decoys.append(shifted)
    options = [correct_holes, decoys[0], decoys[1], decoys[1]]
    rng.shuffle(options); correct_index = options.index(correct_holes)
    return {"correct_answer": correct_index, "diagram_meta": {"fold_sequence": fold_types, "punch_point": punch, "option_holes": options}}

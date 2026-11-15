"""Rotation/flip-invariant near-duplicate grouping for the ceiling dataset (shared by the sampler and the checks).

The Roboflow export contains flipped/rotated copies of the same photo (same source name `<x>_jpg.rf.<hash>`, and also
under different names), so a plain image hash is not enough: compare every pair under all 8 dihedral transforms.
Groups = union of (same Roboflow source name) and near-duplicate pairs: invariant 256-bit dHash distance <= STRICT_BITS,
or <= DUP_BITS when the best-orientation 32x32 pixel correlation is also >= MIN_CORR. (A hash-only threshold of 30 chained
unrelated plain ceilings into one 70-image group via transitive links; the correlation test stops that.)
"""
import io
import itertools
import zipfile

import numpy as np
from PIL import Image

DUP_BITS = 30                      # calibrated by calibrate(): 98% of same-photo pairs, 0.17% of random pairs
STRICT_BITS = 15
MIN_CORR = 0.85


def _dhash_bits(g: Image.Image) -> np.ndarray:
    d = np.asarray(g.resize((17, 16), Image.LANCZOS), dtype=np.int16)
    return (d[:, :-1] > d[:, 1:]).flatten()


def _orientations(data: bytes):
    g = Image.open(io.BytesIO(data)).convert("L").resize((128, 128), Image.LANCZOS)
    for flip in (False, True):
        h = g.transpose(Image.FLIP_LEFT_RIGHT) if flip else g
        for k in range(4):
            yield h.rotate(90 * k, expand=True)


def dihedral_hashes(data: bytes) -> np.ndarray:
    return np.stack([_dhash_bits(o) for o in _orientations(data)])          # (8, 256)


def dihedral_pixels(data: bytes) -> np.ndarray:
    out = []
    for o in _orientations(data):
        v = np.asarray(o.resize((32, 32), Image.LANCZOS), dtype=float).flatten()
        out.append((v - v.mean()) / (v.std() + 1e-6))
    return np.stack(out)                                                     # (8, 1024)


def best_corr(pa: np.ndarray, pb: np.ndarray) -> float:
    return float((pb @ pa[0]).max() / pa.shape[1])


def inv_distance(ha: np.ndarray, hb: np.ndarray) -> int:
    return int((ha[0][None, :] != hb).sum(axis=1).min())   # a fixed, b in all 8 orientations


def groups(items: list[dict], zip_path, threshold: int = DUP_BITS) -> tuple[dict, list]:
    """items need "image" and "source". Returns ({image: group_id}, [(a, b, dist)] near-dup pairs <= threshold)."""
    z = zipfile.ZipFile(zip_path)
    H = {i["image"]: dihedral_hashes(z.read(i["image"])) for i in items}
    P = {i["image"]: dihedral_pixels(z.read(i["image"])) for i in items}
    parent = {i["image"]: i["image"] for i in items}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[max(ra, rb)] = min(ra, rb)

    by_src = {}
    for i in items:
        by_src.setdefault(i["source"], []).append(i["image"])
    for v in by_src.values():
        for b in v[1:]:
            union(v[0], b)
    pairs = []
    for a, b in itertools.combinations([i["image"] for i in items], 2):
        d = inv_distance(H[a], H[b])
        if d <= min(threshold, STRICT_BITS) or (d <= threshold and best_corr(P[a], P[b]) >= MIN_CORR):
            pairs.append((a, b, d))
            union(a, b)
    return {k: find(k) for k in parent}, pairs, H


def calibrate(items, zip_path):
    _, _, H = groups(items, zip_path, threshold=-1)
    by_src = {}
    for i in items:
        by_src.setdefault(i["source"], []).append(i["image"])
    same = [inv_distance(H[a], H[b]) for v in by_src.values() for a, b in itertools.combinations(v, 2)]
    rng = np.random.default_rng(42)
    imgs = [i["image"] for i in items]
    src = {i["image"]: i["source"] for i in items}
    rand = []
    while len(rand) < 3000:
        a, b = rng.choice(len(imgs), 2, replace=False)
        if src[imgs[a]] != src[imgs[b]]:
            rand.append(inv_distance(H[imgs[a]], H[imgs[b]]))
    return np.array(same), np.array(rand)

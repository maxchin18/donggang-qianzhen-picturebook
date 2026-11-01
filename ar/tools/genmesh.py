"""Build closed character shells. Dependencies: Pillow numpy opencv-python scipy mapbox-earcut.

Triangulate the silhouette before inflating it; join front/back with boundary
walls so fins, wings and the back seam stay connected at every angle.
"""
from pathlib import Path
from collections import Counter
import base64
import json
import cv2
import mapbox_earcut
import numpy as np
from PIL import Image
from scipy.ndimage import distance_transform_edt, binary_fill_holes

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'ar/p02'
ASSETS = {'tuna_complete': .18, 'gull1': .13, 'gull2': .13}


def shell(name, thickness):
    image = Image.open(OUT / f'{name}.png').convert('RGBA')
    image = image.crop(image.getbbox())
    if image.width > 768:
        image = image.resize((768, round(image.height * 768 / image.width)), Image.Resampling.LANCZOS)
    rgba = np.array(image)
    h, w = rgba.shape[:2]
    mask = binary_fill_holes(rgba[:, :, 3] >= 100).astype(np.uint8)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contour = max(contours, key=cv2.contourArea)
    contour = cv2.approxPolyDP(contour, max(.5, w / 1000), True).reshape(-1, 2)
    xy = contour.astype(float).tolist()
    mask[:] = 0
    cv2.fillPoly(mask, [contour], 1)
    triangles = mapbox_earcut.triangulate_float64(np.array(xy), np.array([len(xy)], dtype=np.uint32)).reshape(-1, 3).tolist()
    used = sorted({i for tri in triangles for i in tri})
    remap = {old: new for new, old in enumerate(used)}
    xy = [xy[i] for i in used]
    triangles = [tuple(remap[i] for i in tri) for tri in triangles]
    initial_edges = Counter(tuple(sorted((a, b))) for tri in triangles for a, b in zip(tri, tri[1:] + tri[:1]))
    boundary = {edge for edge, count in initial_edges.items() if count == 1}
    boundary_vertices = {i for edge in boundary for i in edge}
    for _ in range(2):
        mids, new_boundary = {}, set()

        def midpoint(a, b):
            edge = tuple(sorted((a, b)))
            if edge not in mids:
                mids[edge] = len(xy)
                xy.append(((np.array(xy[a]) + xy[b]) * .5).tolist())
                if edge in boundary:
                    boundary_vertices.add(mids[edge])
                    new_boundary.update((tuple(sorted((a, mids[edge]))), tuple(sorted((b, mids[edge])))))
            return mids[edge]

        faces = []
        for a, b, c in triangles:
            ab, bc, ca = midpoint(a, b), midpoint(b, c), midpoint(c, a)
            faces.extend(((a, ab, ca), (ab, b, bc), (ca, bc, c), (ab, bc, ca)))
        triangles, boundary = faces, new_boundary

    dt = distance_transform_edt(mask)
    pos, uv = [], []
    for i, (x, y) in enumerate(xy):
        d = dt[min(h - 1, round(y)), min(w - 1, round(x))]
        z = .001 * h / w if i in boundary_vertices else max(.001 * h / w, thickness * h / w * (d / dt.max()) ** .6)
        pos.append((x / (w - 1) - .5, (.5 - y / (h - 1)) * h / w, z))
        uv.append((x / (w - 1), 1 - y / (h - 1)))
    back = {}
    for i in range(len(xy)):
        back[i] = len(pos)
        x, y, z = pos[i]
        pos.append((x, y, -z))
        uv.append(uv[i])
    faces = []
    for a, b, c in triangles:
        pa, pb, pc = np.array(pos[a]), np.array(pos[b]), np.array(pos[c])
        if np.cross(pb - pa, pc - pa)[2] < 0:
            b, c = c, b
        faces.extend(((a, b, c), (back[a], back[c], back[b])))
        for u, v in ((a, b), (b, c), (c, a)):
            if tuple(sorted((u, v))) in boundary:
                faces.extend(((v, u, back[u]), (v, back[u], back[v])))
    edges = Counter(tuple(sorted((a, b))) for tri in faces for a, b in zip(tri, tri[1:] + tri[:1]))
    assert all(n == 2 for n in edges.values()), f'{name}: open/nonmanifold edges'
    assert np.isfinite(pos).all()
    # Bleed edge colors into RGB texture to prevent black alpha seams.
    nearest = distance_transform_edt(rgba[:, :, 3] < 100, return_distances=False, return_indices=True)
    rgb = rgba[:, :, :3][tuple(nearest)]
    Image.fromarray(rgb).save(OUT / f'{name}.webp', quality=90)

    def encode(values, dtype):
        return base64.b64encode(np.array(values, dtype=dtype).tobytes()).decode()

    i32 = len(pos) > 65535
    result = dict(p=encode(pos, '<f4'), u=encode(uv, '<f4'), i=encode(faces, '<u4' if i32 else '<u2'), i32=i32, ratio=h / w)
    print(f'{name}: {len(pos)} vertices, {len(faces)} triangles, open/nonmanifold edges=0, ratio={h/w:.4f}')
    return result


if __name__ == '__main__':
    meshes = {name: shell(name, thickness) for name, thickness in ASSETS.items()}
    (OUT / 'meshes.json').write_text(json.dumps(meshes, separators=(',', ':')), encoding='utf-8')

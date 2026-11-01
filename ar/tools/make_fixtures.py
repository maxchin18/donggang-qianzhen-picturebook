"""Deterministic 30-second YUV420 camera inputs, including a 3-second occlusion.

python ar/tools/make_fixtures.py [output-directory]
Same measured projections as the earlier independent verification, generated
from the original unedited tracking page. Does not need ffmpeg.
"""
from pathlib import Path
import sys
import json
import cv2
import numpy as np
from PIL import Image

root = Path(__file__).resolve().parents[2]
out = Path(sys.argv[1] if len(sys.argv) > 1 else root / '.ar-qa/fixtures')
out.mkdir(parents=True, exist_ok=True)
src = np.array(Image.open(root / 'assets/pages/p02.webp').convert('RGB'))
source_corners = np.float32([[0,0],[src.shape[1],0],[src.shape[1],src.shape[0]],[0,src.shape[0]]])
cases = [
    ('portrait_front', (480,640), [[105,230],[375,230],[375,410],[105,410]]),
    ('portrait_slant_mild', (480,640), [[120,240],[360,240],[375,400],[105,400]]),
    ('portrait_slant', (480,640), [[140,225],[340,225],[385,410],[95,410]]),
    ('landscape_framed', (640,480), [[170,150],[470,150],[512,330],[128,330]]),
    ('landscape', (640,480), [[110,90],[530,90],[590,410],[50,410]]),
]
meta=[]
for name, size, corners in cases:
    frame = cv2.warpPerspective(src, cv2.getPerspectiveTransform(source_corners, np.float32(corners)), size, borderValue=(77,91,103))
    Image.fromarray(frame).save(out / f'{name}.png')
    normal = cv2.cvtColor(frame, cv2.COLOR_RGB2YUV_I420).tobytes()
    blank = cv2.cvtColor(np.full_like(frame, (77,91,103)), cv2.COLOR_RGB2YUV_I420).tobytes()
    file = out / f'{name}.y4m'
    with file.open('wb') as f:
        f.write(f'YUV4MPEG2 W{size[0]} H{size[1]} F10:1 Ip A1:1 C420jpeg\n'.encode())
        for i in range(300): f.write(b'FRAME\n' + (blank if 90 <= i < 120 else normal))
    meta.append(dict(name=name, size=size, corners=corners, occlusion=[9,12], bytes=file.stat().st_size))
(out / 'manifest.json').write_text(json.dumps(meta, indent=2), encoding='utf-8')
print(f'Created and size-checked {len(meta)} fixtures in {out}')

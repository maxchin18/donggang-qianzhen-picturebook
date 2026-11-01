# 做假相機影片：把繪本頁面透視變形（像手機斜拿），輸出 Chromium 可用的 y4m
# 用法：python3 make_cam.py assets/pages/p02.webp out.y4m
import sys, cv2, numpy as np, subprocess
src, out = sys.argv[1], sys.argv[2]
W, H, FPS, SEC = 640, 480, 15, 6
page = cv2.imread(src); ph, pw = page.shape[:2]
frames = []
for i in range(FPS * SEC):
    t = i / FPS; sway = 6 * np.sin(t * 1.3)
    dst = np.float32([[110 + sway, 90], [530 + sway, 90], [600, 420], [40, 420]])  # 上窄下寬
    M = cv2.getPerspectiveTransform(np.float32([[0, 0], [pw, 0], [pw, ph], [0, ph]]), dst)
    bg = np.full((H, W, 3), (70, 90, 105), np.uint8)
    frames.append(cv2.warpPerspective(page, M, (W, H), dst=bg, borderMode=cv2.BORDER_TRANSPARENT))
p = subprocess.Popen(['ffmpeg', '-y', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                      '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
for f in frames: p.stdin.write(f.tobytes())
p.stdin.close(); p.wait()

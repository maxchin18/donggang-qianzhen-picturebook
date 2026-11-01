# AR 工作日誌與交接紀錄

給接手的 Claude、Codex 或其他 AI：這份紀錄寫的是目前做到哪裡、檔案怎麼分工、怎麼驗證、還剩什麼沒做。動工前請先讀完；做完一輪後，請在最後的「修改紀錄」加一筆。

> **2026-11-01 08:35 交接給 Codex。** 使用者用手機實測後覺得效果很不好，主要是鮪魚沒有尾鰭、船的圖片支離破碎（細節見下方「目前問題」）。Claude 已停止修改，請從「目前問題」和「接手第一步」開始。

## 接手第一步（給 Codex）

1. Repo：`https://github.com/maxchin18/donggang-qianzhen-picturebook`，分支 main。AR 程式在 `ar/`，GitHub Pages 從 main 部署。
2. 本機執行：在 repo 根目錄跑 `python -m http.server 8000`，開 `http://localhost:8000/ar/`。localhost 可以用相機，手機實測則要用 https 的上線網址。
3. 先修「目前問題」第 1、2 項。修完要逐一截圖檢查每個角色是否完整，不能只看功能流程（辨識、聲音、字幕）。
4. 用「怎麼驗證」的腳本跑一次，再請使用者用手機對著印好的第 2 頁實測。
5. 改完開 PR，合併到 main 後約 1 分鐘上線。

## 目前問題（使用者實測回饋，尚未修）

1. **鮪魚沒有尾鰭。** 已確認原因：`ar/p02/tuna_big.png`、`tuna_m.png`、`tuna_r.png` 是用 rembg 從原畫切出來的，尾鰭在原畫裡和其他東西重疊，切圖時被切掉了。三張圖最左邊都只剩一截尖尖的尾柄，`tuna_big` 的尾柄只有 81 到 122 像素高。`tuna_big.png` 的腹部兩片鰭之間還有一塊透明破洞。
   - 建議修法一（最好）：請 ChatGPT 或其他繪圖工具，照原畫風格補畫完整的鮪魚（含新月形尾鰭），輸出透明背景 PNG，再重跑 `ar/tools/genmesh.py` 產生網格。
   - 建議修法二：用程式在 PNG 左側加大畫布，畫上深藍色新月形尾鰭，並填補破洞。尾巴在 uv.x=0，會被 `wiggle()` 帶著擺動。改了 PNG 寬度後，`CHARS` 裡的 `w` 和 `x` 要跟著調整，網格也要重產。
   - 3D 漁船船舷外掛的鮪魚也用 `tuna_big`，同樣沒有尾鰭。
2. **船的圖片支離破碎。** 研判是 `ar/p02/boat2.png`（後方那艘船的去背圖）。它有很多細桅桿、繩子和燈，`genmesh.py` 用 84 格網格加上 alpha 門檻，細的部分會斷開或消失，充氣後看起來破碎。另一個可能是程式建的 3D 漁船從正上方看時，和底下原畫的漁船疊在一起，顯得雜亂。請先截圖確認是哪一個。
   - 建議：移除 `CHARS` 裡的 `boat2`，或改用程式建模（比照 `buildBoat()`）；也可以提高網格密度並對 mask 做 closing。
3. **Codex 驗證結果還沒取回。** 使用者電腦（安通Tony，Windows）上的 Codex 對上一版（commit 9ff1c68）做了獨立驗證，新版（57a1ca7）也交代要驗。結果應該在使用者電腦的 `C:\temp\AR驗證\codex` 和 `C:\temp\AR驗證\v2`，但還沒有回報給 Claude，請先讀那兩個資料夾。
4. **還沒做真手機加紙本實測**（Claude 只用 Chromium 假相機測過）。中階手機的效能也還沒驗證。

## 目標（使用者的原話）

> 在繪本製作一個 QR Code，掃描之後開始有 AR 的功能，再去掃描繪本圖片，會有立體的繪本魚、鳥、人物等主角浮動、立體跑出來，持續移動，說這頁裡面的故事。

使用者是國小學務主任（教育者），請用繁體中文溝通。使用者要求交付前**自己先驗證**，也希望有 Codex 做第二意見驗證。

## 目前狀態（2026-11-01）

- 第 2 頁 AR 已上線：https://maxchin18.github.io/donggang-qianzhen-picturebook/ar/
- 印在繪本上的 QR Code 指向 `https://maxchin18.github.io/donggang-qianzhen-picturebook/ar/?openExternalBrowser=1`。加上這個參數，是為了讓 LINE 跳到外部瀏覽器。
- 流程：掃 QR Code → 按「開始 AR」→ 允許相機 → 手機橫拿對準第 2 頁 → 約 2 秒內辨識。辨識後，鮪魚、海鷗、3D 漁船與三位漁夫會浮起並持續移動，同時播放旁白（取自繪本動畫音軌）和字幕。
- 沒有紙本的人可以用「先看預覽」看同一組角色，或在另一個螢幕顯示第 2 頁再掃描。
- GitHub Pages 從 main 部署。改動請走 PR，合併後約 1 分鐘生效。

## 檔案

| 路徑 | 用途 |
|---|---|
| `ar/index.html` | 整個 AR 程式，單一檔案，包含介面、three.js 場景、MindAR 追蹤、旁白、預覽模式 |
| `ar/p02.mind` | MindAR 辨識檔，由 p02.webp 縮成 1024x683 編譯 |
| `ar/p02/*.png` | 從原畫用 rembg 去背切出的角色：tuna_big、tuna_m、tuna_r、gull1、gull2、boat2 |
| `ar/p02/meshes.json` | 角色的「充氣」立體網格，由 `tools/genmesh.py` 產生 |
| `ar/p02/narration.m4a` | 第 2 頁旁白，取自 `assets/video/picturebook.mp4` 的 10.375 到 27.833 秒 |
| `ar/tools/` | 產生網格、做假相機、自動驗證的腳本，說明見下方 |
| `assets/pages/pXX.webp` | 繪本 16 頁原圖（1536x1024） |

## 程式架構（ar/index.html）

- 函式庫用 importmap 從 jsdelivr 載入：three 0.158.0、mind-ar 1.2.5（`mindar-image-three.prod.js`）。QR Code 產生器 qrcodejs 1.0.0 從 cdnjs 載入。
- `CHARS`：平面角色的位置、大小與游動路線。座標以頁寬為 1，原點在頁面中心。
- `artMesh()`：把 PNG 貼到 meshes.json 的立體網格上。魚身會擺動，由 `wiggle()` 用 onBeforeCompile 改頂點。
- `buildBoat()`：用 three.js 基本形狀做 3D 漁船和三位全身漁夫，還有拉魚動作、掛在船邊的鮪魚和釣線。原畫裡的漁夫被船擋住、不完整，所以改用程式建模。
- `addLights()`：環境光，加上主光、補光兩盞平行光。平行光的 target 必須和燈放在同一個 parent（anchor）底下，否則在 AR 裡光會從書頁背後打來，角色變暗、變藍。
- `updateCast()`：每一格更新角色。魚只側起約 0.45 弧度，掉頭時側起方向跟著反轉，所以從上往下看不會露出背上的接縫。
- `startAR()`：在點擊當下解鎖聲音（最多等 1.5 秒）→ 相機權限預檢 → 把 MindAR 的相機 video 設成 muted → 建角色 → 開始追蹤。遺失目標 1 秒後才暫停旁白，並在下緣顯示提示。
- 除錯用：`window.__ar`（visible、audio、started）、`window.__preview`、`window.__upd(t)`。

## 已知的坑（一定要看）

1. 全域的 `video,canvas{max-width:100%}` 會讓 MindAR 相機畫面在直式手機消失，所以 `#ar video,#ar canvas` 要設 `max-width:none`。
2. `[hidden]` 會被 `display:flex` 蓋掉，所以要加 `[hidden]{display:none!important}`。
3. MindAR 的相機 video 沒設 muted，在嚴格的自動播放政策下不會播放，頁面就永遠辨識不到。
4. 測聲音一定要用 `--autoplay-policy=user-gesture-required`。用寬鬆的旗標測，會誤以為聲音正常（以前發生過）。
5. 用 Playwright 測連點時不要連續呼叫 `p.tap()`。按鈕停用後，tap 會一直等到逾時，看起來像旁白秒播完。改用 `evaluate` 裡呼叫 `click()`。
6. Claude 雲端沙盒連不到 github.io 和 CDN，所以測試時用 npm 套件攔截 CDN 路徑，詳見 `tools/common.js`。在使用者電腦上測可以直接開上線網址。

## 怎麼驗證

準備：`npm pack three@0.158.0 mind-ar@1.2.5 qrcodejs@1.0.0`，解開放到某個資料夾 `S` 的 `pkg/three/package`、`pkg/package`、`pkg/qr/package`。再把 `tools/common.js`、`tools/test_ar.js`、`tools/test_preview.js` 也放進 `S`。

```
python3 ar/tools/make_cam.py assets/pages/p02.webp $S/cam.y4m      # 假相機（透視變形的第 2 頁）
node $S/test_ar.js $S $S/cam.y4m 390 844 v    # 直式手機
node $S/test_ar.js $S $S/cam.y4m 844 390 h    # 橫式手機
node $S/test_preview.js $S                    # 預覽模式
```

通過標準：目標在約 2 秒內找到（target found: true）、audio.currentTime 持續增加且 paused 為 false、字幕依序換成三句、截圖裡角色完整而且顏色正常。

## 驗證紀錄

- 2026-11-01：在使用者電腦（Windows）用 Playwright 對上線版（commit 9ff1c68）驗證，功能流程全部通過，找到兩個問題：俯視時鮪魚破相、AR 裡角色偏暗偏藍。本版已修好這兩個問題，並在沙盒用直式、橫式、預覽三種情況重測，全部通過。
- 同日也請使用者電腦上的 Codex（桌面版內附的命令列）獨立驗證，報告存在使用者電腦的 `C:\temp\AR驗證\`。但 Claude 沒等 Codex 的結果就上線了 #6，這是錯的；以後要等第二意見回來才上線。
- 同日 #6 上線後，使用者用手機實測：效果很不好，鮪魚沒有尾鰭，船的圖片支離破碎。Claude 的驗證只看了功能流程和整體截圖，沒有逐一檢查角色完整度，所以漏掉了。
- 還沒做：真手機加紙本實測（iOS Safari、LINE、反光、手晃），以及中階手機效能。

## 待辦與建議（依優先順序）

1. 先修「目前問題」第 1、2 項，再用真手機和印好的第 2 頁實測，特別是頁面斜看時辨識是否穩定。
2. 做一張「抹掉角色的底圖」蓋在頁面上，讓魚像真的離開紙面。這是立體感改善最大的一項。
3. 3D 船和手繪魚風格有落差，可以加船身貼圖和甲板細節；掛在船邊的魚可以放大。
4. 擴充到其他頁：剪該頁旁白 → 用 rembg 切角色 → 跑 genmesh.py → 編譯 .mind（多目標），在 `index.html` 依 targetIndex 換角色組。
5. 首次載入約 7 MB，可以把 PNG 轉成 webp，meshes.json 再壓縮。

## 修改紀錄

| 日期 | PR | 內容 |
|---|---|---|
| 2026-10-31 | #1、#2 | 第 2 頁 AR 試作（影片疊合版）、相機錯誤處理 |
| 2026-11-01 | #3 | 改成角色從紙面跳出、加旁白字幕、QR Code |
| 2026-11-01 | #4 | 角色改成充氣立體網格加燈光，相機 video 設 muted 修好聲音 |
| 2026-11-01 | #5 | 3D 漁船與三位全身漁夫，鮪魚路線避開漁船 |
| 2026-11-01 | #6 | 依使用者電腦上的驗證結果：燈光跟著書頁、魚不再直立破相、直拿提示、遺失延遲、防連點、載入失敗訊息、背景暫停、畫質上限、LINE 自動外開、工作日誌與驗證工具 |
| 2026-11-01 | #7 | 只更新工作日誌：記錄使用者實測問題（缺尾鰭、船破碎）並交接給 Codex |

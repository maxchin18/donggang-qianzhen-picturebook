# 本輪素材與提示詞

> **最新船與船員（2026-11-01）：** 船與五位船員現在直接使用 `assets/pages/p02.webp` 原圖，由 `ar/source-boat.js` 的輪廓、原座標 UV 與封閉圓弧厚度呈現；本輪沒有新增生成式人物／船舶素材，沒有重畫原圖。以下 imagegen 紀錄仍適用於既有完整鮪魚與海面清底。

2026-11-01，使用 **內建 imagegen**（未使用 API/CLI）。原畫、舊角色切圖保留；新素材存入專案，網站不依賴 Codex 生成暫存目錄。

| 新檔案 | 用途與處理 |
|---|---|
| `ar/p02/tuna_complete.png` | 補齊新月尾及魚身破洞的透明 PNG 原始輸出 |
| `ar/p02/tuna_complete.webp` | `genmesh.py` 裁邊、縮至 768px，為封閉幾何準備邊緣延色 RGB 貼圖 |
| `ar/p02/clean-page.png` | 原畫移除兩艘船、人物、大鮪魚及兩隻大海鷗的乾淨背景輸出 |
| `ar/p02/clean-page.webp` | 1536×1024、quality 87 的網站背景版本 |
| `ar/p02/gull1.webp`、`gull2.webp` | 原有 PNG 的封閉幾何 RGB 貼圖，未重畫海鷗 |

漁夫與漁船採程式 3D 幾何、Canvas 紙紋及粗糙材質，沒有生成式人臉替換。三條游魚與船邊魚使用同一完整魚形，以尺寸、路線及姿態區分。

## 鮪魚最終提示詞

參考：`ar/p02/tuna_big.png`（編輯目標）、`assets/pages/p02.webp`（原畫及風格）。透明背景：true。

> Use case: precise-object-edit. Project asset for a children's picturebook AR: create ONE complete bluefin tuna cutout on a genuinely transparent background. Image 1 is the edit target, image 2 is the original illustration and style reference. Keep the blue watercolor/cut-paper textured body, silver white belly, golden finlets, large ringed eye and open mouth closely matching image 1. Repair the large transparent hole inside the body behind the gill: it must be opaque blue silver fish skin with a complete dark pectoral fin. Extend the narrow left tail stalk into a FULL LARGE crescent tail with both long upper and lower pointed lobes like the original tuna at bottom left in image 2. Both tail lobes must be continuous with the body, substantial and clearly defined. Entire fish faces right, horizontal side view, all dorsal/pectoral/pelvic/anal fins and both tail lobes visible, no holes inside the body; only open mouth/exterior negative space transparent. Single fish only, no text, no boat, no water, no shadow. Leave transparent margin around entire animal including leftmost tail tips. Match handcrafted watercolor texture and marine navy/blue/silver/yellow palette. Wide landscape composition.

## 清底最終提示詞

參考：`assets/pages/p02.webp`（編輯目標）。透明背景：false。

> Use case: precise-object-edit. Edit this exact children's watercolor ocean picturebook spread into an AR clean background plate. Keep the exact 3:2 composition, horizon, blue sky, cream clouds, distant green mountains, foamy ocean surface, underwater blue gradients, diagonal sunlight, fishing main line across the underwater area, all hanging branch lines/hooks/bait, yellow surface buoys and small background fish schools. Remove BOTH large fishing boats entirely including masts, cabins, onboard people and equipment. Remove the large hanging tuna in the upper center. Remove the THREE large foreground tuna at bottom left, bottom middle-right, far bottom right. Remove the two large foreground seagulls at top left and upper center-right. Fill all removed boat/people/fish/bird areas seamlessly with matching watercolor sky, distant mountains or ocean/waves/underwater as appropriate, so no recognisable silhouette fragments of removed subjects remain. Preserve the small distant white birds if practical. Do NOT add any new animals, objects or text. This will overlay the original printed page as a clean plate while 3D characters float above, so keep all unaffected features in the same positions. Full landscape 1536x1024-style 3:2 image, edge to edge, no border.

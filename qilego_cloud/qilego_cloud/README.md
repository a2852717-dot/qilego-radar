# 奇樂購 AI 爆品雷達：免費雲端資料版

## 功能
- GitHub Actions 每日排程收集 Google News 公開 RSS 中涉及蝦皮、抖音、小紅書、淘寶、1688 的文章。
- GitHub Pages 免費網站介面、公開情報篩選、季節性提醒、1688 進貨試算。
- 匯入自有合法市場 CSV 與歷史預測 CSV，計算歷史命中率。

**重要：這不是蝦皮／抖音／小紅書／淘寶官方銷量 API。** 公開文章只是市場訊號，不等於商品銷售量或平台搜尋量。未連接真實交易資料前不能宣稱 80% 準確率。

## 雲端部署（免費方案，可能受額度限制）
1. 在 GitHub 建立新 repository（建議公開 repo，Pages 免費方案較容易使用）。
2. 上傳此資料夾全部檔案，包含 `.github/workflows/refresh.yml`。
3. 到 GitHub repository 的 **Settings → Actions → General**，允許 Actions 執行，並將 Workflow permissions 設為 **Read and write permissions**（若組織政策允許）。
4. 到 **Actions → 更新公開市場情報 → Run workflow**，第一次手動執行，產生 `docs/data.json`。
5. 到 **Settings → Pages → Build and deployment → Deploy from a branch**，選 `main` 和 `/docs`，儲存。
6. 等待部署後，網站通常會在 `https://你的帳號.github.io/你的repo名稱/`（實際 URL 以 Pages 顯示為準）。
7. GitHub Actions 排程設為每日 UTC 02:17（台灣時間 10:17），排程可能延遲或停用；若平台更新規則變動也可能抓不到資料。

## CSV 格式
歷史回測：`product,predicted,actual`，後兩欄 1/0。
市場觀測：`platform,product,date,views,sales,price`，例如 `蝦皮,美甲收納盒,2026-10-28,500,20,119`。這只是格式示例，不是真實數據。

## 安全與限制
- 不需要登入蝦皮、抖音、小紅書或淘寶；不會破解驗證碼或繞過平台登入。
- Google News RSS 是第三方新聞索引，不是四平台的官方公開商品 API。
- 文章量與市場熱度不能直接等同。系統目前沒有訓練過的機器學習模型；預測準確率必須用有日期的歷史資料驗證。
- 本版本的 CSV 匯入留在瀏覽器記憶體，重新整理即清空。
- 公開 repo 的 `docs/data.json` 會公開，請勿上傳私人商業數據或 API 金鑰。

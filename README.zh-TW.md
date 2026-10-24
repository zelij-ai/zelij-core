# Zelij Core

[English](README.en.md) · [简体中文](README.zh-CN.md) · **繁體中文** · [日本語](README.ja.md) · [한국어](README.ko.md) · [Türkçe](README.tr.md) · [Русский](README.ru.md) · [Tiếng Việt](README.vi.md) · [ไทย](README.th.md) · [Deutsch](README.de.md) · [Español](README.es.md) · [Français](README.md) · [Українська](README.uk.md) · [Polski](README.pl.md) · [Português (Brasil)](README.pt-BR.md) · [العربية](README.ar.md) · [فارسی](README.fa.md) · [Bahasa Indonesia](README.id.md) · [Italiano](README.it.md) · [Ελληνικά](README.el.md) · [മലയാളം](README.ml.md) · [Roman Urdu](README.ur.md) · [Română](README.ro.md)

[![ci](https://github.com/zelij-ai/zelij-core/actions/workflows/ci.yml/badge.svg)](https://github.com/zelij-ai/zelij-core/actions/workflows/ci.yml) [![version](https://img.shields.io/github/v/release/zelij-ai/zelij-core?label=version)](https://github.com/zelij-ai/zelij-core/releases) [![license](https://img.shields.io/badge/license-AGPL--3.0-1c1917)](LICENSE)

**打造一家 100% AI 原生的新創公司。** 一間辦公室，四個代理人為你工作：他們提議，你來決定。你的機器、你的 Claude 金鑰、你的資料；沒有任何東西會向外回報。

![Zelij Core 的水族箱：創辦人與四個代理人交流、提出決策並執行已核准的事項](docs/img/aquarium.gif)

*模擬一天的水族箱（此處為法語介面）。在你自己的安裝中，每一張卡片都是代理人的一次真實行動，即時呈現，並可回放最近二十四小時。金色就是你：沒有你的決定，任何具約束力的事都不會發生。人物面孔均為虛構角色。*

## 核心能做什麼

- **辦公室**：一個頁面。等待中的決策、向幕僚長提出的請求、最近的執行及其成本、日誌、代理人、已安裝的模組。
- **決策包**：目標、提案、為何是現在、選項、建議、風險、可逆性、計畫、回復、影響。不完整的決策包無法開啟。核准、拒絕，或附上一條必填的指示要求修改，該指示會轉達給代理人。
- **家規**：任何具約束力的事（金錢、公開曝光、刪除、不可逆操作）都不會在沒有決策的情況下發生；每個事實都有日期和來源，或標記為「未查證」；日誌永不刪除。
- **閘道**：創辦人的 Claude 金鑰，每次呼叫的成本依用量和附日期的公開價格計算，達到月度上限即阻擋。
- **執行器**：有界限的呼叫迴圈（每個代理人有回合預算）、節制的工具、模型的拒絕被視為一種結果。
- **模組**：擴充核心的唯一方式。穩定的介面，由發行者以 Ed25519 簽署的 `pack.json` 清單，每個檔案的雜湊都在簽章範圍內，安裝前驗證。部署目標和額外的代理人都由此進入。
- **財務**：已確認的銷售（唯讀匯入 Stripe 或附憑證的手動輸入）、每月重複的已申報支出、經量測的代理人成本、月度帳簿、給會計師的 CSV 匯出。不申報，也不開發票。
- **聯絡人**：每人一張卡片，必填的法律依據、保存期限、往來紀錄、已行使的權利；提出反對的聯絡人不再收到任何訊息，到期的聯絡人被遺忘，只保留權利日誌。
- **發布**：行銷代理人撰寫的頁面先成為草稿，再成為一項決策；核准後，以 GitHub 拉取請求或 WordPress 草稿的形式提交給網站。最後一步——合併或發布——由你完成。
- **放在口袋裡**：每項決策都會送到你的手機，透過附兩個一次性簽署連結的電子郵件，或透過有三個按鈕的 Telegram。你在捷運排隊時核准，水族箱隨即回應。與辦公桌前同一道門、同一本日誌。
- **水族箱**：看著你的代理人工作，每個泡泡都是最近 24 小時內的一次真實行動；虛線圓環是空缺的職位。一個可分享的公開頁面，附「by zelij.ai」徽章。
- **目錄**：免費版不包含的內容，如實列出；向發行者購買的模組在這裡安裝，經簽署與驗證。任何付款都不經過辦公室。
- **軟體工廠**：建造者只在一個儲存庫上讀取和提議，透過經安全閘門的拉取請求（300 行、僅文字、無密鑰、無基礎設施檔案、相依套件經 OSV 核查無已知弱點）；透過 SSH 部署到 Linux 伺服器或部署到 OVH（網域和 DNS 透過 API），原子切換、冒煙測試與回復；網域探測；辦公室每日備份。它從不合併、從不付款、從不碰觸辦公室。
- **代理人**：每個代理人一個資料夾，一個帶簡單標頭和法語指示的 `agent.md`。四個代理人：Camille Aubert（幕僚長）、Élise Tanguy（成長、行銷與產品）、Nour Bellamy（財務與客戶）、Sacha Ferrand（建造者，軟體工廠）。創辦人在辦公室裡直接對每一位說話；一個指定了代理人和任務的已核准決策包會立即執行，在計畫的範圍內。

## 一分鐘試用，不需金鑰

```bash
git clone https://github.com/zelij-ai/zelij-core.git && cd zelij-core
docker compose -f docker-compose.demo.yml up --build
```

開啟 `http://localhost:8000` 進入示範：一家虛構公司、四個模擬代理人、待核准的決策、回放他們一天的水族箱。不需金鑰、不需帳號、零成本；不會向任何模型傳送任何內容，停止後一切消失。確信之後，再進行下面的真實安裝。辦公室介面本身為法語。

## 啟動

```bash
cp .env.example .env     # Claude 金鑰、上限、SECRET_KEY、資料庫密碼
docker compose up -d --build
```

辦公室在 `http://localhost:8000` 回應。未設定 SMTP 時，登入連結會寫入容器日誌（`docker compose logs core-app`）。

完整指南（英文）：**[安裝](docs/INSTALLATION.en.md)**（從空機器到 https 辦公室、SMTP、軟體工廠、備份、疑難排解）、**[使用手冊](docs/MODE-D-EMPLOI.en.md)**（每個頁面、代理人、決策、成本）。創辦人和代理人的照片放在 [`portraits/`](portraits/README.md)（說明為法語）。

使用已發布的映像檔，不需本地建置（在 `.env` 中設定 `CORE_IMAGE_TAG=v…` 以固定版本）：

```bash
docker compose -f docker-compose.yml -f docker-compose.image.yml up -d
```

本地執行，不用 Docker：

```bash
pip install -r requirements-dev.txt
uvicorn core.bureau.app:app --reload
```

## 發行者公鑰

目錄中的模組由 zelij.ai 簽署。需設定在 `ZELIJ_CLE_PUBLIQUE` 的公鑰（`.env.example` 中已填好）：

```
8da6c92455558c15a1566b333cef22fb5fc60aad9ffbf811f372e4bb7eacc42a
```

## 安全

核心所保證並經測試的內容（`tests/test_securite.py`）：

- **模組**：模組只有經發行者簽署（Ed25519）才能安裝和執行，簽章涵蓋每個程式碼檔案的 SHA-256 雜湊：簽署後被修改、新增或移除的檔案都會讓模組失效。
- **登入**：20 分鐘有效的一次性連結，在資料庫中以雜湊儲存；對連結請求依地址、依 IP 和全域設置煞車，辦公室永遠不會淪為郵件中繼；正式環境未設定 SMTP 時，不會建立也不會記錄任何連結。
- **表單**：HMAC 工作階段 cookie，`HttpOnly`、`SameSite=Strict`，每個 POST 都做來源檢查並驗證每工作階段的反 CSRF 權杖。
- **頁面**：嚴格的內容安全政策（`default-src 'self'`，無行內指令碼，無框架）、`nosniff`、`X-Frame-Options`、`Referrer-Policy`，來源為 https 時啟用 HSTS。
- **代理人**：代理人讀到的任何內容（網頁、儲存庫檔案）都以外部內容的形式框定送達，絕不作為指令；代理人只執行其卡片上的工具，一旦讀取了私有資料，就只能呼叫公司自己的網站；它只讀取公開的 https 位址（私有位址、回送位址、鏈路本地位址和內部名稱在每一跳重新導向時都被拒絕，回應有上限）；安全閘門阻擋密鑰、基礎設施檔案、第三方指令碼、框架和網路呼叫。
- **容器**：非特權使用者、唯讀檔案系統、無能力、不可提權；SSH 伺服器的主機金鑰可以固定（`SSH_CLE_HOTE`）。
- **會計匯出**：看起來像試算表公式的儲存格會被中和。

回報弱點請寄到 `securite@zelij.ai`，修復前請勿公開。每次發布前，`pip-audit -r requirements.txt` 和 `bandit -r core scripts -ll` 必須沒有任何結果。

## 貢獻與版本

`CONTRIBUTING.md`（法語）說明一項貢獻如何進入版本，包括這條規則：貢獻一個部署目標，即可終身免費獲得對應的模組包。`SECURITY.md` 說明如何回報弱點。`CHANGELOG.md` 說明每個版本改變了什麼，以及創辦人還需要做什麼。

## 測試與發布檢查

```bash
python -m pytest -q
python scripts/controle_publication.py
```

發布檢查會拒絕金鑰、IP 位址、內部代號、個人電子郵件地址、明文密碼，以及一份私有清單（`ZELIJ_CORE_INTERDITS`）中的詞語，該清單永遠不進入儲存庫。

## 授權

GNU AGPL v3。版權所有 (C) 2026 zelij.ai。你可以使用、修改和再散布核心，前提是以同一授權發布你的修改。驅動 zelij.ai 的完整版仍屬於發行者。

by zelij.ai — https://zelij.ai/

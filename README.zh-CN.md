# Zelij Core

[English](README.en.md) · **简体中文** · [繁體中文](README.zh-TW.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Türkçe](README.tr.md) · [Русский](README.ru.md) · [Tiếng Việt](README.vi.md) · [ไทย](README.th.md) · [Deutsch](README.de.md) · [Español](README.es.md) · [Français](README.md) · [Українська](README.uk.md) · [Polski](README.pl.md) · [Português (Brasil)](README.pt-BR.md) · [العربية](README.ar.md) · [فارسی](README.fa.md) · [Bahasa Indonesia](README.id.md) · [Italiano](README.it.md) · [Ελληνικά](README.el.md) · [മലയാളം](README.ml.md) · [Roman Urdu](README.ur.md) · [Română](README.ro.md)

[![ci](https://github.com/zelij-ai/zelij-core/actions/workflows/ci.yml/badge.svg)](https://github.com/zelij-ai/zelij-core/actions/workflows/ci.yml) [![version](https://img.shields.io/github/v/release/zelij-ai/zelij-core?label=version)](https://github.com/zelij-ai/zelij-core/releases) [![license](https://img.shields.io/badge/license-AGPL--3.0-1c1917)](LICENSE)

**打造一家 100% AI 原生的初创公司。** 一个办公室，四个智能体为你工作：它们提议，你来决定。你的机器、你的 Claude 密钥、你的数据；没有任何东西会向外部回传。

![Zelij Core 的水族箱：创始人与四个智能体交流、提出决策并执行已批准的事项](docs/img/aquarium.gif)

*模拟一天的水族箱（此处为法语界面）。在你自己的安装中，每一张卡片都是智能体的一次真实行动，实时呈现，并可回放最近二十四小时。金色就是你：没有你的决定，任何有约束力的事都不会发生。人物面孔均为虚构角色。*

## 核心能做什么

- **办公室**：一个页面。等待中的决策、向幕僚长提出的请求、最近的执行及其成本、日志、智能体、已安装的模块。
- **决策包**：目标、提案、为何是现在、选项、推荐、风险、可逆性、计划、回滚、影响。不完整的决策包无法打开。批准、拒绝，或附上一条必填的指示要求修改，该指示会转达给智能体。
- **家规**：任何有约束力的事（资金、公开曝光、删除、不可逆操作）都不会在没有决策的情况下发生；每个事实都有日期和来源，或标记为「未核实」；日志永不删除。
- **网关**：创始人的 Claude 密钥，每次调用的成本按用量和带日期的公开价格计算，月度上限达到即阻止。
- **执行器**：有边界的调用循环（每个智能体有轮次预算）、节制的工具、模型的拒绝被视为一种结果。
- **模块**：扩展核心的唯一方式。稳定的接口，由发行方以 Ed25519 签名的 `pack.json` 清单，每个文件的哈希都在签名范围内，安装前校验。部署目标和额外的智能体都通过这条路进入。
- **财务**：已确认的销售（只读导入 Stripe 或附凭证的手工录入）、每月重复的已申报支出、经测量的智能体成本、月度账簿、给会计的 CSV 导出。不做申报，也不开发票。
- **联系人**：每人一张卡片，必填的法律依据、保留期限、往来记录、已行使的权利；提出反对的联系人不再收到任何信息，到期的联系人被遗忘，只保留权利日志。
- **发布**：营销智能体撰写的页面先成为草稿，再成为一项决策；批准后，作为 GitHub 拉取请求或 WordPress 草稿提交给网站。最后一步——合并或发布——由你完成。
- **装在口袋里**：每项决策都会送达你的手机，通过带两个一次性签名链接的电子邮件，或通过带三个按钮的 Telegram。你在地铁排队时批准，水族箱随即响应。与办公桌前同一道门、同一本日志。
- **水族箱**：看着你的智能体工作，每个气泡都是最近 24 小时内的一次真实行动；虚线圆环是空缺的岗位。一个可分享的公开页面，带「by zelij.ai」徽章。
- **目录**：免费版不包含的内容，如实列出；从发行方购买的模块在这里安装，经签名和校验。任何付款都不经过办公室。
- **软件工厂**：建造者只在一个仓库上读取和提议，通过经安全门的拉取请求（300 行、仅文本、无密钥、无基础设施文件、依赖项经 OSV 核查无已知漏洞）；通过 SSH 部署到 Linux 服务器或部署到 OVH（域名和 DNS 通过 API），原子切换、冒烟测试和回滚；域名探测；办公室每日备份。它从不合并、从不付款、从不触碰办公室。
- **智能体**：每个智能体一个文件夹，一个带简单头部和法语指示的 `agent.md`。四个智能体：Camille Aubert（幕僚长）、Élise Tanguy（增长、营销与产品）、Nour Bellamy（财务与客户）、Sacha Ferrand（建造者，软件工厂）。创始人在办公室里直接对每一位说话；一个指定了智能体和任务的已批准决策包会立即执行，在计划的范围内。

## 一分钟试用，无需密钥

```bash
git clone https://github.com/zelij-ai/zelij-core.git && cd zelij-core
docker compose -f docker-compose.demo.yml up --build
```

打开 `http://localhost:8000` 进入演示：一家虚构公司、四个模拟智能体、待批准的决策、回放它们一天的水族箱。无需密钥、无需账户、零成本；不会向任何模型发送任何内容，停止后一切消失。确信之后，再进行下面的真实安装。办公室界面本身为法语。

## 启动

```bash
cp .env.example .env     # Claude 密钥、上限、SECRET_KEY、数据库密码
docker compose up -d --build
```

办公室在 `http://localhost:8000` 响应。未配置 SMTP 时，登录链接会写入容器日志（`docker compose logs core-app`）。

完整指南（英文）：**[安装](docs/INSTALLATION.en.md)**（从空机器到 https 办公室、SMTP、软件工厂、备份、故障排除）、**[使用手册](docs/MODE-D-EMPLOI.en.md)**（每个页面、智能体、决策、成本）。创始人和智能体的照片放在 [`portraits/`](portraits/README.md)（说明为法语）。

使用已发布的镜像，无需本地构建（在 `.env` 中设置 `CORE_IMAGE_TAG=v…` 以固定版本）：

```bash
docker compose -f docker-compose.yml -f docker-compose.image.yml up -d
```

本地运行，不用 Docker：

```bash
pip install -r requirements-dev.txt
uvicorn core.bureau.app:app --reload
```

## 发行方公钥

目录中的模块由 zelij.ai 签名。需设置到 `ZELIJ_CLE_PUBLIQUE` 的公钥（`.env.example` 中已填好）：

```
8da6c92455558c15a1566b333cef22fb5fc60aad9ffbf811f372e4bb7eacc42a
```

## 安全

核心所保证并经测试的内容（`tests/test_securite.py`）：

- **模块**：模块只有经发行方签名（Ed25519）才能安装和运行，签名覆盖每个代码文件的 SHA-256 哈希：签名后被修改、添加或删除的文件都会让模块失效。
- **登录**：20 分钟有效的一次性链接，在数据库中以哈希存储；对链接请求按地址、按 IP 和全局设置刹车，办公室永远不会沦为邮件中继；生产环境未配置 SMTP 时，不会创建也不会记录任何链接。
- **表单**：HMAC 会话 cookie，`HttpOnly`、`SameSite=Strict`，每个 POST 都做来源检查并校验每会话的反 CSRF 令牌。
- **页面**：严格的内容安全策略（`default-src 'self'`，无内联脚本，无框架）、`nosniff`、`X-Frame-Options`、`Referrer-Policy`，源为 https 时启用 HSTS。
- **智能体**：智能体读到的任何内容（网页、仓库文件）都以外部内容的形式框定送达，绝不作为指令；智能体只运行其卡片上的工具，一旦读取了私有数据，就只能调用公司自己的网站；它只读取公开的 https 地址（私有地址、回环地址、链路本地地址和内部名称在每一跳重定向时都被拒绝，响应有上限）；安全门阻止密钥、基础设施文件、第三方脚本、框架和网络调用。
- **容器**：非特权用户、只读文件系统、无能力、不可提权；SSH 服务器的主机密钥可以固定（`SSH_CLE_HOTE`）。
- **会计导出**：看起来像电子表格公式的单元格会被中和。

报告漏洞请发送至 `securite@zelij.ai`，修复前请勿公开。每次发布前，`pip-audit -r requirements.txt` 和 `bandit -r core scripts -ll` 必须无任何结果。

## 贡献与版本

`CONTRIBUTING.md`（法语）说明一项贡献如何进入版本，包括这条规则：贡献一个部署目标，即可终身免费获得对应的模块包。`SECURITY.md` 说明如何报告漏洞。`CHANGELOG.md` 说明每个版本改变了什么，以及创始人还需要做什么。

## 测试与发布检查

```bash
python -m pytest -q
python scripts/controle_publication.py
```

发布检查会拒绝密钥、IP 地址、内部代号、个人邮箱地址、明文密码，以及一份私有清单（`ZELIJ_CORE_INTERDITS`）中的词语，该清单永远不进入仓库。

## 许可证

GNU AGPL v3。版权所有 (C) 2026 zelij.ai。你可以使用、修改和再分发核心，前提是以同一许可证发布你的修改。驱动 zelij.ai 的完整版仍归发行方所有。

by zelij.ai — https://zelij.ai/

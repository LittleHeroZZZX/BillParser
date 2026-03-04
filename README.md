<div align="center">

# BillParser

**AI 驱动的账单自动解析服务**

将支付宝、微信等截图一键结构化为账单数据，无缝对接记账 App

[![CI](https://github.com/LittleHeroZZZX/BillParser/actions/workflows/ci.yml/badge.svg)](https://github.com/LittleHeroZZZX/BillParser/actions)
[![Python](https://img.shields.io/badge/python-3.12-blue?logo=python)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-Apache%202.0-green)](LICENSE)
[![codecov](https://codecov.io/gh/LittleHeroZZZX/BillParser/branch/master/graph/badge.svg)](https://codecov.io/gh/LittleHeroZZZX/BillParser)

</div>

---

## 概览

BillParser 是一个可自托管的账单解析微服务。你只需上传一张支付截图，它就能通过 OCR + LLM 两阶段流水线自动识别：

- 交易类型（支出 / 收入 / 转账 / 信用卡还款）
- 金额、时间
- 账户（付款卡 / 收款账户）
- 个人化分类（完全由 YAML 配置驱动）

输出格式与 [钱迹 AutoTasker](https://docs.qianjiapp.com/plugin/auto_tasker.html) 接口兼容，可直接接入自动记账工作流。

---

## 核心特性

| 特性 | 说明 |
|------|------|
| **可插拔 OCR** | 内置百度千帆 OCR、PP-OCRv5，可扩展任意 OCR 后端 |
| **可插拔 LLM** | 内置 DeepSeek Chat，兼容所有 OpenAI 格式接口 |
| **流水线编排** | YAML 定义解析步骤，无需改代码即可组合 OCR + LLM |
| **个人化分类** | 账户、账单分类全部由 YAML 配置，LLM 严格按配置输出 |
| **REST API** | FastAPI 提供 `/parse_image` 接口，带 API Key 鉴权 |
| **CLI 工具** | `parse-file` 本地调试单张图片，`serve` 启动服务 |
| **容器化部署** | 提供 Dockerfile + docker-compose，一条命令上线 |

---

## 快速开始

### 方式一：Docker（推荐）

**1. 克隆并配置**

```bash
git clone https://github.com/LittleHeroZZZX/BillParser.git
cd BillParser
cp config/settings.example.yaml config/settings.yaml
cp config/parsers.example.yaml config/parsers.yaml
cp config/pipelines.example.yaml config/pipelines.yaml
cp config/assets.example.yaml config/assets.yaml
cp config/categories.example.yaml config/categories.yaml
```

**2. 填写配置**（见 [配置说明](#配置说明)）

**3. 启动**

```bash
docker compose up -d
```

服务默认监听 `http://localhost:8878`，访问 `http://localhost:8878/docs` 查看交互式 API 文档。

---

### 方式二：本地开发

> 需要 Python 3.12 和 [uv](https://docs.astral.sh/uv/)

```bash
git clone https://github.com/LittleHeroZZZX/BillParser.git
cd BillParser
uv sync
# 复制并编辑配置文件
cp config/settings.example.yaml config/settings.yaml
# ...（其余同上）

# 启动服务
uv run python -m billparser.cli serve

# 或本地解析单张图片（调试用）
uv run python -m billparser.cli parse-file tests/images/alipay/1.png
```

---

## 配置说明

所有配置均位于 `config/` 目录，Docker 部署时该目录以 volume 方式挂载，修改后无需重建镜像。

### `settings.yaml` — 服务配置

```yaml
api_keys:
  - "your_api_key_here"   # 调用 /parse_image 时需在 Header 传入 X-API-Key

server:
  host: "0.0.0.0"
  port: 8878
```

### `parsers.yaml` — 解析器凭证

```yaml
parsers:
  deepseek_chat:
    base_url: https://api.deepseek.com
    api_key: sk-xxxxxxxxxxxxxxxx

  qianfan_ocr:                  # 百度千帆 OCR
    api_key: your_api_key
    secret_key: your_secret_key

  PP_OCRv5:                     # 自托管 PP-OCRv5 服务
    url: http://your-ocr-host/predict
    token: your_token
```

### `pipelines.yaml` — 流水线编排

```yaml
pipelines:
  ocr_then_llm:
    steps:
      - "Qianfan_OCR"    # 第一步：图片 → 文字
      - "deepseek_chat"  # 第二步：文字 → 结构化账单
```

步骤名称对应 `parsers.yaml` 中的键（大小写不敏感）。可自由组合、新增流水线。

### `assets.yaml` — 账户列表

```yaml
assets:
  - account_name: "招商银行信用卡"
    description: "招商银行信用卡，尾号 1564，日常消费主力卡"
```

LLM 会根据账单内容，从该列表中匹配最合适的账户，不会凭空生成账户名。

### `categories.yaml` — 账单分类

支持两级分类结构，LLM 的输出严格限定在此列表内：

```yaml
categories:
  - transaction_type: 支出
    items:
      - l1_name: 三餐
        description: 所有与饮食相关的支出
        items:
          - l2_name: 外卖
            description: 通过外卖平台订购的餐食
          - l2_name: 食堂
            description: 公司食堂餐饮
```

---

## API 参考

### `POST /parse_image`

上传账单截图，返回结构化账单数据。

**请求**

| 参数 | 类型 | 说明 |
|------|------|------|
| `image` | `file` | 账单截图（multipart/form-data） |
| `pipeline_name` | `query` | 流水线名称，默认 `ocr_then_llm` |
| `X-API-Key` | `header` | API 鉴权密钥 |

**响应示例**

```json
{
  "transaction_type": "支出",
  "amount": 53.70,
  "time": "2025-10-26T17:27:53",
  "catename": "外卖",
  "remark": "盒马工坊双汁白切鸡 240g",
  "accountname": "招商银行信用卡",
  "accountname2": null,
  "fee": null
}
```

**curl 示例**

```bash
curl -X POST http://localhost:8878/parse_image \
  -H "X-API-Key: your_api_key_here" \
  -F "image=@/path/to/screenshot.png" \
  -F "pipeline_name=ocr_then_llm"
```

---

## 架构设计

```
RawImage
   │
   ▼
┌──────────────┐     YAML 配置驱动
│  OCR Parser  │  ◄──────────────────  parsers.yaml
│ (千帆/PP-OCR) │                       pipelines.yaml
└──────┬───────┘
       │ RawText
       ▼
┌──────────────┐     账户 & 分类注入
│  LLM Parser  │  ◄──────────────────  assets.yaml
│  (DeepSeek)  │                       categories.yaml
└──────┬───────┘
       │ Bill
       ▼
  REST Response
```

**扩展新解析器** 只需继承 `BaseParser[InputType, OutputType]`，实现 `parse()` 方法并设置 `name` 属性，即可被自动发现，在 `parsers.yaml` 中直接引用——无需修改任何注册代码。

---

## 开发

```bash
# 安装含开发依赖
uv sync --group dev

# 运行测试
uv run pytest

# 覆盖率报告
uv run pytest --cov=billparser --cov-report=html

# 代码检查 & 格式化
uv run ruff check .
uv run ruff format .
```

---

## License

[Apache 2.0](LICENSE)

# 持久化契约

所有磁盘读写都走 `scripts/store.py`（纯标准库，无依赖）。SKILL.md 不直接拼路径、不自己写 JSON——这样三个意图共享同一套 schema，不会各写各的、也不会漂。

## 为什么路径不写死

数据落点由用户在**首次使用**时用绝对路径确认，写进 config，之后所有命令从 config 读。好处：换 agent / 换机器时只要带上 config + 数据目录即可迁移，且用户始终明确知道自己的饮食数据存在哪。

- **配置文件**：`$FOOD_CALORIE_HOME/config.json`（设了环境变量时）否则 `~/.food-calorie/config.json`。环境变量让不同 agent / 环境可以各自隔离。
- **数据根 `dataRoot`**：记录在 config 里，可与配置目录不同，由用户确认。

### 首次使用流程

```bash
python <skill>/scripts/store.py propose      # 打印建议的绝对路径 proposedDataRoot
# → 把 proposedDataRoot 念给用户，确认或让其改成别的绝对路径
python <skill>/scripts/store.py init --data-root <用户确认的绝对路径> [--timezone Asia/Shanghai]
```

`propose` 若发现已初始化，会直接回 `initialized:true` + 现有 dataRoot，此时跳过 init。后续任何命令前都可先 `store.py status` 确认。

## 目录布局

```
<dataRoot>/
├── config.json                       # 实际在 $FOOD_CALORIE_HOME 或 ~/.food-calorie
├── index/
│   └── foods.json                    # 个人食物索引（跨餐一致 + 秒查），首次 init 时建为空 {}
└── days/
    └── 2026-05-30/
        ├── entries/
        │   ├── 2026-05-30T12-05-01_lunch_ab12.json
        │   └── 2026-05-30T16-40-00_snack_cd34.json
        ├── images/
        │   └── 2026-05-30T12-05-01_lunch_1.jpg   # store add 时从用户路径拷入
        ├── summary.json              # store aggregate 写：出图输入 + 证据
        └── summary.png               # generate_summary.py 写；同日重生成=覆盖
```

一餐一文件：`add` 只新增、`edit` 只动一条、`aggregate` 只读。

## entry schema

```json
{
  "schemaVersion": 1,
  "entryId": "2026-05-30T12-05-01_lunch_ab12",
  "date": "2026-05-30",
  "mealType": "lunch",
  "source": { "kind": "image", "refs": ["images/2026-05-30T12-05-01_lunch_1.jpg"] },
  "items": [
    { "name": "白米饭", "grams": 200, "kcalPer100g": 115, "kcal": 230, "confidence": "medium", "assumptions": ["按标准饭碗估算"] }
  ],
  "totalKcal": 230,
  "createdAt": "2026-05-30T12:05:01+08:00",
  "updatedAt": "2026-05-30T12:05:01+08:00",
  "revisions": []
}
```

- `mealType` ∈ `breakfast` / `lunch` / `dinner` / `snack`（出图时映射为早餐/午餐/晚餐/加餐）。
- `items[]` 由估算产出（见 `estimation.md`）。`kcal` 省略时 store 会按 `grams×kcalPer100g/100` 补算；`totalKcal` 由 store 求和，不要手填。
- `source.kind` = `image`（有图）或 `text`（纯文字描述）。
- `revisions[]` 由 `edit` 追加，每条含改动时间、note、改动前快照——保留纠正审计，同时保证纠正不会被当成新一餐重复计入。

## foods.json schema

```json
{
  "白米饭(熟)": { "kcalPer100g": 116, "typicalGrams": 200, "source": "成品估", "updatedAt": "2026-05-30" },
  "生椰拿铁(大杯)": { "kcalPerServing": 267, "typicalGrams": 480, "source": "品牌SKU", "updatedAt": "2026-05-30" }
}
```

键为食物名（含关键规格）。每100g 复用项填 `kcalPer100g`；品牌整份固定项填 `kcalPerServing`。`foods-put` 同名更新、不重复。

## store.py 子命令速查

| 命令 | 用途 | 意图 |
|---|---|---|
| `propose` | 首次取建议绝对路径 | 首次 |
| `init --data-root <abs> [--timezone <tz>]` | 写配置、建目录 | 首次 |
| `status` | 查是否已初始化 + dataRoot | 任意 |
| `today` | 按配置时区打印今天日期 | 任意 |
| `add --date <d> --meal <type> --items <items.json> [--images ...] [--note ...]` | 新建一餐，返回 entryId + 当日累计 | **log** |
| `edit --entry-id <id> [--items <items.json>] [--meal <m>] --note <note>` | 改一条、留 revision、不新建 | **edit** |
| `get --entry-id <id>` | 打印一条 | edit/排查 |
| `list --date <d>` | 列当日所有条目 | 任意 |
| `aggregate --date <d>` | 聚合写 summary.json + 打印渲染 JSON（只读不估算） | **summary** |
| `foods-get [--name <n>]` | 读个人索引 | log/edit |
| `foods-put --json <file>` | 合并写个人索引 | log/edit |

`items.json` = items 数组，例：

```json
[ { "name": "白米饭", "grams": 200, "kcalPer100g": 115, "confidence": "medium", "assumptions": ["按标准饭碗估算"] } ]
```

缺数据时 `aggregate` 会 fail-loud（退出码 4），不会凭空估算——这是「summary 不重估」的硬保证。

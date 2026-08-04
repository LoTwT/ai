# 饮食记录 JSON 规范

本规范定义 `food-calorie` 在 `summary` 模式下物化的 JSON，以及汇总脚本读取旧版或新版 JSON 时的兼容行为。每日记录在 `record`、`correct` 和 `status` 阶段只存在于当前对话状态中；不要提前创建每日 JSON 文件。

本文示例中的食物名和数值只演示字段结构，不构成热量索引或计算依据。

## 目录

- [兼容目标](#兼容目标)
- [旧版 1.0 基线](#旧版-10-基线)
- [新版 2.0 结构](#新版-20-结构)
- [字段规则](#字段规则)
- [数量与旧重量投影](#数量与旧重量投影)
- [枚举](#枚举)
- [合计规则](#合计规则)
- [输入标准化](#输入标准化)
- [校验与错误](#校验与错误)

## 兼容目标

同时满足以下要求：

1. 合并前产生的旧 JSON 无需迁移即可传给新版 `generate_summary.py`。
2. 新版默认 JSON 始终保留全部旧必需字段，可传给仓库外未升级的旧脚本副本。
3. 不删除、改名或改变旧字段类型；只通过新增字段表达新语义。
4. 旧消费者可以忽略扩展字段并继续出图。
5. `quantity` 是新版数量语义的权威来源；`weight_g` 对非固体仅为旧消费者的兼容投影。

旧脚本可能把饮品或按份计数项目的兼容投影显示成“重量”，这是兼容未升级消费者的已知限制。新版汇总不得把 g、ml、piece 和 serving 混合求和。

## 旧版 1.0 基线

缺少 `schema_version` 或显式使用字符串 `"1.0"` 的输入按 1.0 处理。只有字符串 `"2.0"` 启用新版规则；拒绝任何其他版本值。旧结构如下：

```json
{
  "date": "2026-03-15",
  "meals": [
    {
      "meal_type": "早餐",
      "items": [
        {
          "name": "示例食物",
          "weight_g": 300,
          "calories": 140
        }
      ],
      "images": ["/path/to/breakfast.jpg"]
    }
  ]
}
```

旧必需字段与类型：

| 路径 | 类型 | 约束 |
|---|---|---|
| `date` | string | `YYYY-MM-DD` |
| `meals` | array | 汇总输入至少包含一个 meal |
| `meals[].meal_type` | string | 非空 |
| `meals[].items` | array | 非空 |
| `meals[].items[].name` | string | 非空 |
| `meals[].items[].weight_g` | number | 非负；默认输出整数 |
| `meals[].items[].calories` | number | 非负 kcal；默认输出整数 |
| `meals[].images` | string array | 允许为空；旧输入缺少时可标准化为空数组 |

## 新版 2.0 结构

新版是旧结构的严格超集。物化新记录时输出 `schema_version: "2.0"`，保留 `date`、`meals`、`meal_type`、`items`、`images`、`name`、`weight_g` 和 `calories`。

```json
{
  "schema_version": "2.0",
  "date": "2026-03-15",
  "meals": [
    {
      "id": "meal-20260315-lunch",
      "meal_type": "午餐",
      "items": [
        {
          "id": "item-001",
          "name": "示例饮品（大杯）",
          "weight_g": 480,
          "calories": 270,
          "quantity": {
            "value": 480,
            "unit": "ml",
            "display": "约480ml",
            "method": "container",
            "estimated": true
          },
          "weight_g_basis": "volume_proxy",
          "calculation": {
            "method": "brand_sku",
            "energy_value": 270,
            "energy_unit": "kcal/serving",
            "source_type": "brand_official",
            "source_label": "示例品牌官方大杯 SKU"
          },
          "confidence": "high",
          "notes": []
        }
      ],
      "images": ["/path/to/lunch.jpg"],
      "totals": {
        "calories": 270
      }
    }
  ],
  "totals": {
    "calories": 270
  }
}
```

物化时从当前对话状态原样输出稳定的 `meal.id` 和 `item.id`。旧消费者会忽略它们；`correct` 模式使用它们定位条目。

同一日期和 `meal_type` 的后续记录若是既有餐次的延续，复用原 meal 与 `meal.id` 并追加 item。只有用户明确表示另一场同类餐次时才创建新的 meal 与 ID；上下文无法区分时先确认。JSON 允许同一天存在多个相同 `meal_type`，不得在物化阶段按名称强行合并。

不要输出当前没有消费者的 `timezone` 或 item 级图片索引。继续用 meal 级 `images` 表达图片归属。

## 字段规则

### 顶层

| 字段 | 新输出 | 规则 |
|---|---|---|
| `schema_version` | 必须 | 固定为字符串 `"2.0"` |
| `date` | 必须 | 目标日期，格式 `YYYY-MM-DD` |
| `meals` | 必须 | 按对话状态中的原始顺序输出 |
| `totals.calories` | 必须 | 按[合计规则](#合计规则)派生 |

### Meal

| 字段 | 新输出 | 规则 |
|---|---|---|
| `id` | 必须 | 当前对话内稳定且唯一，不因纠正内容而改变 |
| `meal_type` | 必须 | 保留用户指定或流程推断的餐次名称 |
| `items` | 必须 | 非空，保留原始顺序 |
| `images` | 必须 | 图片实际路径数组；允许为空 |
| `totals.calories` | 必须 | 该 meal 的已存储 item 热量之和 |

### Item

| 字段 | 新输出 | 规则 |
|---|---|---|
| `id` | 必须 | 当前对话内稳定且唯一；覆盖纠正时保持不变 |
| `name` | 必须 | 兼容字段，也是汇总显示名称 |
| `weight_g` | 必须 | 非负整数；按[数量与旧重量投影](#数量与旧重量投影)生成 |
| `calories` | 必须 | 唯一最终展示热量字段，保存已取整的非负整数 kcal |
| `quantity` | 必须 | 新版权威数量对象 |
| `weight_g_basis` | 必须 | 说明兼容 `weight_g` 的产生方式 |
| `calculation` | 必须 | 保存计算方法、能量依据与来源，支持复核和纠正 |
| `confidence` | 必须 | `high`、`medium` 或 `low` |
| `notes` | 必须 | 字符串数组；没有备注时输出空数组 |

`calories` 不要再复制为 `calories_kcal`。`name` 必须与最终展示名称一致。

### Quantity

`schema_version: "2.0"` 的新 item 必须同时输出以下字段：

| 字段 | 类型 | 规则 |
|---|---|---|
| `value` | number | 非负；参与热量计算的权威数量 |
| `unit` | string | `g`、`ml`、`piece` 或 `serving` |
| `display` | string | 新版汇总直接显示的数量文本 |
| `method` | string | 使用[数量方法枚举](#枚举) |
| `estimated` | boolean | 表示数量是否仍含估算误差，与 method 独立 |

用户提供“约 150g”时，`method` 可以是 `user_provided`，但 `estimated` 仍为 `true`。用户给出明确包装净含量时通常可设为 `false`。

带骨、带壳或带皮食物额外输出：

- `quantity.gross_value`：照片中观察到的总量，与 `quantity.value` 使用同一单位；
- `quantity.edible_ratio`：大于 0 且不超过 1 的可食比例；
- `quantity.value`：按 `floor(gross_value * edible_ratio + 0.5)` 半入取整得到的可食用量。

例如观察总量为 155g、可食比例为 0.7 时，`quantity.value` 必须为 109g。普通食物不要输出 `gross_value` 和 `edible_ratio`。

### Calculation

可复核的新记录使用以下字段：

| 字段 | 类型 | 规则 |
|---|---|---|
| `method` | string | 使用[计算方法枚举](#枚举) |
| `energy_value` | number | 与 `energy_unit` 对应的非负依据值 |
| `energy_unit` | string | 如 `kcal/100g`、`kcal/100ml` 或 `kcal/serving` |
| `source_type` | string | 使用[来源类型枚举](#枚举) |
| `source_label` | string | 简短、可复核的来源说明 |

若本次使用多组件计算，可在 `notes` 中简述拆分与一次性烹饪修正，但不要为同一最终热量再创建第二个兼容字段。

## 数量与旧重量投影

`quantity` 是权威数量；`weight_g` 只用于保持旧脚本可读。按下表生成：

| `quantity` 类型 | `weight_g` | `weight_g_basis` |
|---|---:|---|
| 固体 `g` | 可食用重量 | `edible_weight` |
| 饮品 `ml` | 数值上按 `1ml = 1g` 投影 | `volume_proxy` |
| `piece`，可估单个可食重量 | 数量 × 单个可食重量 | `piece_estimate` |
| `serving`，有规格重量 | 规格重量 | `serving_conversion` |
| `serving`，只有规格容量 | 数值上按 `1ml = 1g` 投影 | `volume_proxy` |
| `serving`，完全无重量或容量信息 | `0` | `unavailable` |

所有非负投影值使用 `floor(value + 0.5)` 半入取整，输出整数。带骨、带壳、带皮食物的 `weight_g` 使用可食用的 `quantity.value`，不要使用 `gross_value`。

物化记录时优先使用可确定校验的数量表示：有明确可食重量时使用 `g`，有明确饮品容量时使用 `ml`。品牌 SKU 的热量依据可以继续写为 `calculation.energy_unit: "kcal/serving"`，不要求 `quantity.unit` 同时使用 `serving`。只有权威数量本身确为个数或份数时才使用 `piece` 或 `serving`。

当前 schema 不保存单个可食重量、每份规格重量或每份规格容量等换算因子。因此，生成记录的 skill 必须按上表计算 `piece_estimate`、`serving_conversion` 及 serving 的 `volume_proxy`；汇总脚本只校验 `weight_g` 是非负整数且 unit/basis 组合合法，不独立复算这些投影。`quantity.unit` 为 `g` 或 `ml`，以及 `weight_g_basis` 为 `unavailable` 时，投影可由现有字段唯一确定，汇总脚本必须严格校验其数值。

新版汇总优先显示 `quantity.display`。没有 `quantity` 的旧 item 回退显示 `${weight_g}g`。不要汇总混合单位的数量；全天只强制汇总 kcal。

## 枚举

### `quantity.method`

```text
legacy
package
brand_spec
user_provided
count
container
anchor
history_ratio
standard_portion
```

`legacy` 只用于标准化缺少扩展字段的旧 JSON。新记录使用与实际份量推导方式相符的其他值。

### `quantity.unit`

```text
g | ml | piece | serving
```

### `confidence`

```text
high | medium | low
```

### `calculation.method`

至少支持：

```text
nutrition_label
brand_sku
finished_food_density
raw_ingredients_with_cooking_factor
soup_components
drink_components
standard_portion
```

### `calculation.source_type`

至少支持：

```text
personal_index
package_label
brand_official
food_composition_table
web
model_estimate
user_provided
```

## 合计规则

先把每个 item 的最终展示热量取整并保存到 `item.calories`，再执行求和：

```text
meal.totals.calories = sum(meal.items[*].calories)
day.totals.calories = sum(meals[*].totals.calories)
```

不要用未取整的中间值重新计算 totals，也不要相信与 item 求和不一致的输入 totals。汇总脚本以已标准化 item 的 `calories` 重新派生餐次和全天合计。

## 输入标准化

汇总脚本读取数据后先执行等价于 `normalize_record(data)` 的逻辑：

1. 缺少 `schema_version` 或值为字符串 `"1.0"` 时视为旧版 1.0；值为字符串 `"2.0"` 时执行新版规则；其他字符串、数字或类型一律作为不支持的版本报错。
2. 为旧 item 补充：
   - `quantity.value = weight_g`；
   - `quantity.unit = "g"`；
   - `quantity.display = "{weight_g}g"`；
   - `quantity.method = "legacy"`；
   - `quantity.estimated = true`；
   - `confidence = "medium"`；
   - `weight_g_basis = "legacy"`。
3. 旧 meal 缺少 `images` 时按空数组处理；新输出仍显式写出 `images`。
4. 按已存储的 item `calories` 重新派生 meal 和 day totals。
5. 保持所有 meal、item 与 images 的输入顺序。
6. 忽略渲染器不认识的扩展字段，不要因此破坏兼容输入。

标准化只帮助旧输入进入统一渲染模型，不要用它掩盖缺失旧必需字段或错误类型。

## 校验与错误

生成图片前校验完整输入。至少检查：

1. 根值是 JSON object。
2. `schema_version` 只能缺省、为字符串 `"1.0"` 或为字符串 `"2.0"`；拒绝未知版本。
3. `date` 是有效的 `YYYY-MM-DD` 字符串。
4. `meals` 是非空数组。
5. 每个 `meal_type` 是非空字符串，`items` 是非空数组，`images` 是字符串数组。
6. 每个 `name` 是非空字符串，`weight_g` 和 `calories` 是非负有限数字。
7. 所有声明为 number 或 integer 的字段都拒绝布尔值、负数、NaN、Infinity 和 -Infinity；不要因为 Python 中 `bool` 是 `int` 的子类而接受 `true` 或 `false`，也不要接受解析器可能放行的非标准非有限常量。
8. 新版 meal 必须包含非空字符串 `id` 和可派生一致的 `totals.calories`；新版 item 必须包含非空字符串 `id`、`quantity`、`weight_g_basis`、`calculation`、`confidence` 和 `notes`。
9. 新版 `quantity` 的五个基础字段同时存在且类型正确，枚举值有效；`estimated` 必须是布尔值。
10. 新版 `weight_g` 是非负整数；`quantity.unit` 为 `g` 或 `ml`，以及 `weight_g_basis` 为 `unavailable` 时，必须与可确定的投影值一致；`piece` 和 `serving` 必须使用合法的 `weight_g_basis`，其换算值由生成记录的 skill 按投影规则保证。
11. `gross_value` 与 `edible_ratio` 成对出现，且可食用量符合半入取整规则。
12. 新版 `calculation` 必须是 object，且包含有效枚举的字符串 `method`、非负有限数字 `energy_value`、非空字符串 `energy_unit`、有效枚举的字符串 `source_type` 和非空字符串 `source_label`。
13. 新版 `confidence` 必须是规定枚举之一；`notes` 必须是字符串数组，允许为空。
14. 提供的 totals 与 item 求和不一致时，以规范派生值为准，并避免显示旧的错误合计。

缺少字段、类型错误或 item 数组为空时，停止生成图片并给出包含完整字段路径的清晰错误，例如：

```text
meals[1].items[0].calories: missing required field
```

不要静默跳过坏 item 后继续生成看似完整的汇总。图片读取失败不属于 JSON 结构错误：为该图片显示占位提示，并继续处理其他有效图片。

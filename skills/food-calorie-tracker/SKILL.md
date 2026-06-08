---
name: food-calorie-tracker
description: "通过食物照片或描述记录每日饮食、估算热量、持久化保存，并生成每日饮食长图。当用户发送食物照片、说『记录饮食/这是我的早餐午餐晚餐/帮我算热量/卡路里/饮食打卡/今天吃了什么』，或纠正之前记错的食物份量（『那个不是排骨是红烧肉』『饭只有150g』），或要求『生成今日汇总/出图/汇总长图』时，都应触发本 skill。也适用于在对话中陆续发多餐照片、最后要一张当日汇总图的情况；即使用户只发一张图说『这是我午餐』也要触发。本 skill 同时负责『怎么估算』和『怎么记录/展示』，是食物热量相关的唯一入口。不要用于与饮食记录无关的图片识别、泛泛营养咨询或菜谱推荐。"
---

# 食物热量追踪

通过照片或描述记录每日饮食：识别食物 → 估算热量 → 落盘持久化 → 按日出汇总长图。这是食物热量相关的**唯一** skill，估算方法与记录展示都在这里。

## 三个意图

每次先判断用户要做哪件事，再走对应流程。区分核心是**有没有新的食物图/新的一餐**加上**动词**；歧义就用一句话反问，别猜。

| 意图 | 何时 | 做什么 | 不做 |
|---|---|---|---|
| **log** | 有新食物图，或「记录/算热量/这是我X餐」 | 估算 → `store.py add` 落一条 → 回本餐 + 当日累计 | 不出图 |
| **edit** | 指向**已记录**的某条做纠正（「那不是排骨是红烧肉」「饭只有150g」） | 重估或按新份量重算 → `store.py edit` 改那一条、留 revision | 不新建条目（避免把纠正当成新一餐重复计入）、不出图 |
| **summary** | 无新图 +「生成/汇总/出图」**或**外部定时带日期调用 | `store.py aggregate` 读当日已存条目 → `generate_summary.py` 出长图 | 不重新估算（只读已存数据） |

## 首次使用：确认数据落点

数据存哪由用户用绝对路径确认一次，写进 config，之后自动读。详见 `references/storage.md`。

```bash
python <skill>/scripts/store.py status        # 已初始化就跳过下面两步
python <skill>/scripts/store.py propose        # 打印建议的绝对路径
# → 把建议路径念给用户确认（或让其改成别的绝对路径）
python <skill>/scripts/store.py init --data-root <用户确认的绝对路径>
```

`<skill>` = 本 skill 在当前环境的安装目录，运行时定位，不要硬编码。

## log —— 记录一餐

1. **估算**：读 `references/estimation.md`，按其流程从图片/描述识别食物、估重量、算热量。先查个人索引 `store.py foods-get`；算出索引里没有的食物后用 `store.py foods-put` 追加，保证跨餐一致。
2. **判餐次**：优先用用户明说的；没说就按对话时间/上下文推断（breakfast/lunch/dinner/snack）。
3. **落盘**：把 items 写成一个临时 JSON（schema 见 `storage.md`），调：
   ```bash
   python <skill>/scripts/store.py add \
     --date $(python <skill>/scripts/store.py today) \
     --meal lunch \
     --items /tmp/items.json \
     --images /path/to/photo1.jpg
   ```
   `--images` 可省（纯文字描述）。store 会拷图、补算 totalKcal、回 entryId 和当日累计。
4. **回话**：简洁列出结果（不重复贴图），例：
   ```
   识别结果（午餐）：
   - 白米饭 约200g | 230 kcal
   - 红烧排骨 约150g | 375 kcal
   - 拿铁（大杯，全脂奶）约480ml | 220 kcal（已按较高值估算）
   合计：825 kcal ｜ 今日累计：1465 kcal
   已记录。有不准的地方告诉我，我改这条。
   ```
   首次记录时提醒一次「热量估算有 ±15-20% 误差」即可，之后别反复强调。

同一对话里用户可能分多次发不同餐——每次都 `add` 一条、报当日累计。用户没要求出图就不要自动出图，继续等。

## edit —— 纠正已记录的一条

用户纠正时**改已存条目，绝不新建**——新建会把同一餐重复计入。

1. 找到要改的 entryId（刚记的那条会在 `add` 输出里；或 `store.py list --date <d>` 查）。
2. 按 `estimation.md`：种类纠正→重查热量重算；份量纠正→每100g 热量不变、按新份量重算。
3. 写新的 items JSON，调：
   ```bash
   python <skill>/scripts/store.py edit \
     --entry-id 2026-05-30T12-05-01_lunch_ab12 \
     --items /tmp/items_fixed.json \
     --note "排骨→红烧肉，重查热量"
   ```
   store 会把改前快照存进 revisions、重算 totalKcal、回当日累计。
4. 回话确认；若变化 <5% 可直接说「热量基本不变」。

## summary —— 出当日长图

只在用户要求、或外部定时调用时做。**只读已存条目，不重新估算。**

```bash
# 1. 聚合（写 summary.json 证据 + 打印渲染 JSON）
python <skill>/scripts/store.py aggregate --date 2026-05-30 > /tmp/render.json

# 2. 出图（脚本依赖 Pillow）
python -c "import PIL" 2>/dev/null || pip install Pillow --break-system-packages 2>/dev/null || pip install Pillow
python <skill>/scripts/generate_summary.py --data /tmp/render.json \
  --output <dataRoot>/days/2026-05-30/summary.png
```

`<dataRoot>` 来自 `store.py status`。同一天多次生成 = 覆盖同名 summary.png。当日没有条目时 `aggregate` 会 fail-loud（不会凭空出图）。长图自上而下是：标题栏 → 按餐次的食物/重量/热量表（含合计）→ 原始照片分餐次排列。生成后把图交给用户。

## 定时

本 skill 不管调度。要每天自动出图，由宿主（如 Slock 每日 reminder / cron）在外部定时触发，触发消息**显式带日期**调用 summary（默认目标日 = 昨天 T-1，时区按 config）。

## 注意

- 追问只问热量影响大的（肉类品种、炒 vs 炸、饮品糖度/加料）；影响小的（蔬菜品种、咸淡）取高值不打扰。详见 `estimation.md` 追问决策矩阵。
- 用户描述可能很随意（「那个汤」「昨天那种面」），结合上下文理解；要改哪条不确定就 `list` 出来问。
- 图片模糊无法辨认时告知并请补充；能大致判断就按较高值估、标注不确定。
- 一张图可能有多种食物，全部识别。

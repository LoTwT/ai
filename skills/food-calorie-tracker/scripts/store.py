#!/usr/bin/env python3
"""
食物热量追踪 — 持久化存储 CLI（无第三方依赖，纯标准库）。

为什么要有这个脚本：log / edit / summary 三个意图都要读写同一套磁盘状态。
把「配置解析、写条目、改条目留修订、按日聚合」收敛到一个确定性的脚本里，
意图之间就不会各写各的、schema 也不会漂；同时让验收点可被机械检查：
  - log  → 必然落一个 entry 文件（add 子命令）
  - edit → 只改一条、追加一条 revision、绝不新建（edit 子命令，不碰 totalKcal 以外的历史）
  - summary → 只读已存条目做聚合，绝不重估（aggregate 子命令不调用任何估算）

存储位置不写死：首次使用时由 propose/init 让用户用「绝对路径」确认数据落点，
写进 config.json；之后所有子命令从 config 读 dataRoot。换 agent / 换机器时
只要带上 config + 数据目录即可迁移。

配置文件位置（可被环境变量覆盖，实现「按 agent/环境区分」）：
  $FOOD_CALORIE_HOME/config.json   （若设置了 FOOD_CALORIE_HOME）
  否则 ~/.food-calorie/config.json
config.json 里的 dataRoot 才是真正的数据根，可与配置目录不同，由用户确认。
"""

import argparse
import json
import os
import re
import secrets
import shutil
import sys
from datetime import datetime
from pathlib import Path

try:
    from zoneinfo import ZoneInfo
except Exception:  # pragma: no cover - 极旧 Python 兜底
    ZoneInfo = None

SCHEMA_VERSION = 1
DEFAULT_TIMEZONE = "Asia/Shanghai"
MEAL_TYPES = ["breakfast", "lunch", "dinner", "snack"]


# ── 配置定位与读写 ────────────────────────────────────────

def config_home() -> Path:
    """配置文件所在目录：优先 $FOOD_CALORIE_HOME，否则 ~/.food-calorie。"""
    env = os.environ.get("FOOD_CALORIE_HOME")
    if env:
        return Path(env).expanduser()
    return Path.home() / ".food-calorie"


def config_path() -> Path:
    return config_home() / "config.json"


def proposed_data_root() -> Path:
    """首次使用时给用户的默认数据根（绝对路径），用户可改。"""
    return config_home().resolve()


def load_config() -> dict:
    p = config_path()
    if not p.exists():
        die(
            "尚未初始化。请先用 `store.py propose` 取得建议路径，"
            "与用户确认绝对路径后用 `store.py init --data-root <abs>` 写入配置。",
            code=3,
        )
    cfg = json.loads(p.read_text(encoding="utf-8"))
    cfg.setdefault("timezone", DEFAULT_TIMEZONE)
    cfg["dataRoot"] = str(Path(cfg["dataRoot"]).expanduser())
    return cfg


def data_root() -> Path:
    return Path(load_config()["dataRoot"])


def timezone_name() -> str:
    return load_config().get("timezone", DEFAULT_TIMEZONE)


def now_local(tz_name: str) -> datetime:
    if ZoneInfo is not None:
        try:
            return datetime.now(ZoneInfo(tz_name))
        except Exception:
            pass
    return datetime.now().astimezone()


# ── 工具 ──────────────────────────────────────────────────

def die(msg: str, code: int = 1):
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(code)


def read_json_arg(path: str):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path: Path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def day_dir(root: Path, date: str) -> Path:
    return root / "days" / date


def compute_total(items) -> int:
    return int(round(sum(float(it.get("kcal", 0)) for it in items)))


def normalize_items(items):
    """补齐派生字段：未给 kcal 时由 grams×kcalPer100g/100 算；四舍五入。"""
    out = []
    for it in items:
        it = dict(it)
        if "kcal" not in it and "grams" in it and "kcalPer100g" in it:
            it["kcal"] = int(round(float(it["grams"]) * float(it["kcalPer100g"]) / 100.0))
        out.append(it)
    return out


# ── 子命令 ────────────────────────────────────────────────

def cmd_config_path(_):
    print(config_path())


def cmd_propose(_):
    p = config_path()
    if p.exists():
        cfg = load_config()
        print(json.dumps({
            "initialized": True,
            "configPath": str(p),
            "dataRoot": cfg["dataRoot"],
            "timezone": cfg.get("timezone", DEFAULT_TIMEZONE),
        }, ensure_ascii=False, indent=2))
        return
    print(json.dumps({
        "initialized": False,
        "configPath": str(p),
        "proposedDataRoot": str(proposed_data_root()),
        "defaultTimezone": DEFAULT_TIMEZONE,
        "note": "向用户展示 proposedDataRoot（绝对路径），确认或改后用 init 写入。",
    }, ensure_ascii=False, indent=2))


def cmd_status(_):
    p = config_path()
    if not p.exists():
        print(json.dumps({"initialized": False, "configPath": str(p)}, ensure_ascii=False, indent=2))
        return
    cfg = load_config()
    print(json.dumps({
        "initialized": True,
        "configPath": str(p),
        "dataRoot": cfg["dataRoot"],
        "timezone": cfg.get("timezone", DEFAULT_TIMEZONE),
    }, ensure_ascii=False, indent=2))


def cmd_init(args):
    root = Path(args.data_root).expanduser()
    if not root.is_absolute():
        die("data-root 必须是绝对路径（首次使用须与用户确认确切落点）。")
    cfg = {
        "schemaVersion": SCHEMA_VERSION,
        "dataRoot": str(root),
        "timezone": args.timezone or DEFAULT_TIMEZONE,
    }
    (root / "days").mkdir(parents=True, exist_ok=True)
    (root / "index").mkdir(parents=True, exist_ok=True)
    foods = root / "index" / "foods.json"
    if not foods.exists():
        write_json(foods, {})
    write_json(config_path(), cfg)
    print(json.dumps({"ok": True, "configPath": str(config_path()), **cfg}, ensure_ascii=False, indent=2))


def cmd_today(_):
    print(now_local(timezone_name()).strftime("%Y-%m-%d"))


def _copy_images(root: Path, date: str, entry_id: str, images):
    """把用户图片拷进当日 images/，返回相对 dataRoot 的引用列表。"""
    refs = []
    img_dir = day_dir(root, date) / "images"
    img_dir.mkdir(parents=True, exist_ok=True)
    for i, src in enumerate(images, 1):
        src_p = Path(src).expanduser()
        if not src_p.exists():
            die(f"图片不存在: {src}")
        ext = src_p.suffix.lower() or ".jpg"
        dst = img_dir / f"{entry_id}_{i}{ext}"
        shutil.copy2(src_p, dst)
        refs.append(str(dst.relative_to(root)))
    return refs


def cmd_add(args):
    if args.meal not in MEAL_TYPES:
        die(f"meal 须为 {MEAL_TYPES} 之一")
    root = data_root()
    tz = timezone_name()
    now = now_local(tz)
    # entryId 前缀用进餐日期（= 落盘目录），保证 _find_entry 快速定位；时间用当前时刻
    ts = f"{args.date}T{now.strftime('%H-%M-%S')}"
    entry_id = f"{ts}_{args.meal}_{secrets.token_hex(2)}"
    items = normalize_items(read_json_arg(args.items))
    if not items:
        die("items 不能为空")
    images = args.images or []
    refs = _copy_images(root, args.date, entry_id, images) if images else []
    entry = {
        "schemaVersion": SCHEMA_VERSION,
        "entryId": entry_id,
        "date": args.date,
        "mealType": args.meal,
        "source": {"kind": "image" if refs else "text", "refs": refs},
        "items": items,
        "totalKcal": compute_total(items),
        "createdAt": now.isoformat(),
        "updatedAt": now.isoformat(),
        "revisions": [],
    }
    if args.note:
        entry["note"] = args.note
    entry_path = day_dir(root, args.date) / "entries" / f"{entry_id}.json"
    write_json(entry_path, entry)
    print(json.dumps({
        "ok": True,
        "entryId": entry_id,
        "entryPath": str(entry_path),
        "mealKcal": entry["totalKcal"],
        "dayTotalKcal": _day_total(root, args.date),
    }, ensure_ascii=False, indent=2))


def _find_entry(root: Path, entry_id: str) -> Path:
    # entryId 内含日期前缀，直接定位当日目录
    m = re.match(r"(\d{4}-\d{2}-\d{2})T", entry_id)
    if m:
        cand = day_dir(root, m.group(1)) / "entries" / f"{entry_id}.json"
        if cand.exists():
            return cand
    # 兜底全局搜索
    for p in (root / "days").glob("*/entries/*.json"):
        if p.stem == entry_id:
            return p
    die(f"找不到条目: {entry_id}")


def cmd_edit(args):
    root = data_root()
    path = _find_entry(root, args.entry_id)
    entry = json.loads(path.read_text(encoding="utf-8"))
    # 改前快照进 revision —— edit 只改这一条、不新建，避免把纠正当成新一餐重复计入
    snapshot = {
        "at": now_local(timezone_name()).isoformat(),
        "note": args.note,
        "before": {"items": entry["items"], "totalKcal": entry["totalKcal"], "mealType": entry["mealType"]},
    }
    if args.items:
        entry["items"] = normalize_items(read_json_arg(args.items))
        entry["totalKcal"] = compute_total(entry["items"])
    if args.meal:
        if args.meal not in MEAL_TYPES:
            die(f"meal 须为 {MEAL_TYPES} 之一")
        entry["mealType"] = args.meal
    entry["updatedAt"] = snapshot["at"]
    entry.setdefault("revisions", []).append(snapshot)
    write_json(path, entry)
    print(json.dumps({
        "ok": True,
        "entryId": entry["entryId"],
        "mealKcal": entry["totalKcal"],
        "dayTotalKcal": _day_total(root, entry["date"]),
        "revisionCount": len(entry["revisions"]),
    }, ensure_ascii=False, indent=2))


def cmd_get(args):
    root = data_root()
    path = _find_entry(root, args.entry_id)
    print(path.read_text(encoding="utf-8"))


def _load_day_entries(root: Path, date: str):
    edir = day_dir(root, date) / "entries"
    if not edir.exists():
        return []
    entries = [json.loads(p.read_text(encoding="utf-8")) for p in sorted(edir.glob("*.json"))]
    return entries


def _day_total(root: Path, date: str) -> int:
    return sum(int(e.get("totalKcal", 0)) for e in _load_day_entries(root, date))


def cmd_list(args):
    root = data_root()
    entries = _load_day_entries(root, args.date)
    rows = [{
        "entryId": e["entryId"],
        "mealType": e["mealType"],
        "totalKcal": e.get("totalKcal", 0),
        "items": [it["name"] for it in e.get("items", [])],
    } for e in entries]
    print(json.dumps({
        "date": args.date,
        "entryCount": len(rows),
        "dayTotalKcal": sum(r["totalKcal"] for r in rows),
        "entries": rows,
    }, ensure_ascii=False, indent=2))


MEAL_DISPLAY = {"breakfast": "早餐", "lunch": "午餐", "dinner": "晚餐", "snack": "加餐"}
MEAL_ORDER = {m: i for i, m in enumerate(MEAL_TYPES)}


def cmd_aggregate(args):
    """按日聚合已存条目 → 写 summary.json（出图输入 + 证据），并打印渲染就绪 JSON。

    只读、不估算。缺数据时 fail-loud。
    """
    root = data_root()
    entries = _load_day_entries(root, args.date)
    if not entries:
        die(f"{args.date} 当日没有任何条目，无法聚合（summary 不会凭空估算）。", code=4)
    # 同餐次合并；entry 内多 item 展开为表格行
    by_meal = {}
    for e in entries:
        mt = e["mealType"]
        g = by_meal.setdefault(mt, {"meal_type": MEAL_DISPLAY.get(mt, mt), "items": [], "images": [], "_low": []})
        for it in e.get("items", []):
            g["items"].append({
                "name": it["name"],
                "weight_g": int(round(float(it.get("grams", 0)))),
                "calories": int(round(float(it.get("kcal", 0)))),
            })
            if it.get("confidence") == "low":
                g["_low"].append(it["name"])
        for ref in e.get("source", {}).get("refs", []):
            g["images"].append(str((root / ref).resolve()))
    meals = []
    low_conf = []
    for mt in sorted(by_meal, key=lambda m: MEAL_ORDER.get(m, 99)):
        g = by_meal[mt]
        low_conf += g.pop("_low")
        meals.append(g)
    render = {"date": args.date, "meals": meals}
    summary = {
        "schemaVersion": SCHEMA_VERSION,
        "date": args.date,
        "generatedAt": now_local(timezone_name()).isoformat(),
        "sourceEntryIds": [e["entryId"] for e in entries],
        "dayTotalKcal": _day_total(root, args.date),
        "lowConfidenceItems": low_conf,
        "render": render,
    }
    write_json(day_dir(root, args.date) / "summary.json", summary)
    print(json.dumps(render, ensure_ascii=False, indent=2))


def cmd_foods_get(args):
    root = data_root()
    foods = json.loads((root / "index" / "foods.json").read_text(encoding="utf-8"))
    if args.name:
        print(json.dumps(foods.get(args.name, {}), ensure_ascii=False, indent=2))
    else:
        print(json.dumps(foods, ensure_ascii=False, indent=2))


def cmd_foods_put(args):
    root = data_root()
    fpath = root / "index" / "foods.json"
    foods = json.loads(fpath.read_text(encoding="utf-8")) if fpath.exists() else {}
    incoming = read_json_arg(args.json)
    # 去重：同名更新、不重复追加
    foods.update(incoming)
    write_json(fpath, foods)
    print(json.dumps({"ok": True, "count": len(foods), "updated": list(incoming.keys())}, ensure_ascii=False, indent=2))


def build_parser():
    p = argparse.ArgumentParser(description="食物热量追踪 — 持久化存储 CLI")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("config-path", help="打印配置文件路径").set_defaults(func=cmd_config_path)
    sub.add_parser("propose", help="首次使用：打印建议数据根（绝对路径）供用户确认").set_defaults(func=cmd_propose)
    sub.add_parser("status", help="打印初始化状态与 dataRoot/timezone").set_defaults(func=cmd_status)

    pi = sub.add_parser("init", help="写入配置（用户确认绝对路径后）")
    pi.add_argument("--data-root", required=True)
    pi.add_argument("--timezone", default=None)
    pi.set_defaults(func=cmd_init)

    sub.add_parser("today", help="按配置时区打印今天日期").set_defaults(func=cmd_today)

    pa = sub.add_parser("add", help="log：新建一条进餐记录")
    pa.add_argument("--date", required=True)
    pa.add_argument("--meal", required=True)
    pa.add_argument("--items", required=True, help="items 数组 JSON 文件路径")
    pa.add_argument("--images", nargs="*", default=[])
    pa.add_argument("--note", default=None)
    pa.set_defaults(func=cmd_add)

    pe = sub.add_parser("edit", help="edit：改一条已存记录，留 revision，不新建")
    pe.add_argument("--entry-id", required=True)
    pe.add_argument("--items", default=None, help="新 items 数组 JSON 文件路径")
    pe.add_argument("--meal", default=None)
    pe.add_argument("--note", required=True)
    pe.set_defaults(func=cmd_edit)

    pg = sub.add_parser("get", help="打印一条记录")
    pg.add_argument("--entry-id", required=True)
    pg.set_defaults(func=cmd_get)

    pl = sub.add_parser("list", help="列出某天所有记录")
    pl.add_argument("--date", required=True)
    pl.set_defaults(func=cmd_list)

    pag = sub.add_parser("aggregate", help="summary：按日聚合 → 写 summary.json + 打印渲染 JSON（只读不估算）")
    pag.add_argument("--date", required=True)
    pag.set_defaults(func=cmd_aggregate)

    pfg = sub.add_parser("foods-get", help="读个人食物索引")
    pfg.add_argument("--name", default=None)
    pfg.set_defaults(func=cmd_foods_get)

    pfp = sub.add_parser("foods-put", help="合并写入个人食物索引（同名更新）")
    pfp.add_argument("--json", required=True)
    pfp.set_defaults(func=cmd_foods_put)

    return p


def main():
    args = build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()

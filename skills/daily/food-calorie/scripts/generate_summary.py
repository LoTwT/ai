#!/usr/bin/env python3
"""Generate a daily food-calorie summary PNG from compatible v1 or strict v2 JSON."""

from __future__ import annotations

import argparse
import copy
import json
import math
import platform
import subprocess
import sys
from datetime import datetime
from numbers import Real
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont, ImageOps
except ImportError as exc:  # pragma: no cover - exercised only without a runtime dependency
    raise SystemExit(
        "generate_summary.py 需要 Pillow 才能生成图片；"
        "请先在调用环境中安装 Pillow，本脚本不会自动安装依赖。"
    ) from exc


# Canvas
CANVAS_WIDTH = 750
PAD = 28
CONTENT_WIDTH = CANVAS_WIDTH - PAD * 2
BOTTOM_PAD = 30

# Colors
BG = "#F8F4F0"
TITLE_COLOR = "#2A2A2A"
BORDER = "#C0B8B0"
HEADER_BG = "#EDE8E3"
HEADER_TEXT = "#444444"
MEAL_TEXT = "#2A2A2A"
CELL_TEXT = "#333333"
NUM_TEXT = "#333333"
SUBTOTAL_BG = "#F3EEEA"
TOTAL_BG = "#EDE8E3"
TOTAL_TEXT = "#2A2A2A"
PHOTO_LABEL_BG = "#EDE8E3"
PHOTO_LABEL_TEXT = "#666666"
PLACEHOLDER_BG = "#F0F0F0"
PLACEHOLDER_TEXT = "#999999"

# Font sizes
FS_TITLE = 28
FS_HEADER = 18
FS_MEAL = 20
FS_CELL = 17
FS_NUM = 17
FS_SUBTOTAL = 18
FS_TOTAL_L = 22
FS_TOTAL_N = 26
FS_PHOTO = 18

# Table sizing
TITLE_TOP_PAD = 24
TITLE_TEXT_H = 36
TITLE_BOT_PAD = 20
HEADER_H = 42
BORDER_W = 1
CELL_PAD_V = 10
CELL_PAD_H = 12
LINE_SPACING = 5
ROW_MIN_H = 44
SUBTOTAL_H = 46
TOTAL_H = 56

# Columns: meal | food | quantity | calories
COL_RATIOS = (0.13, 0.50, 0.17, 0.20)

# Photos
PHOTO_SECTION_GAP = 28
PHOTO_GAP = 10
PHOTO_LABEL_H = 38
PHOTO_ERROR_H = 150

QUANTITY_UNITS = {"g", "ml", "piece", "serving"}
QUANTITY_METHODS = {
    "legacy",
    "package",
    "brand_spec",
    "user_provided",
    "count",
    "container",
    "anchor",
    "history_ratio",
    "standard_portion",
}
CONFIDENCE_LEVELS = {"high", "medium", "low"}
WEIGHT_BASES = {
    "legacy",
    "edible_weight",
    "volume_proxy",
    "piece_estimate",
    "serving_conversion",
    "unavailable",
}
CALCULATION_METHODS = {
    "nutrition_label",
    "brand_sku",
    "finished_food_density",
    "raw_ingredients_with_cooking_factor",
    "soup_components",
    "drink_components",
    "standard_portion",
}
SOURCE_TYPES = {
    "personal_index",
    "package_label",
    "brand_official",
    "food_composition_table",
    "web",
    "model_estimate",
    "user_provided",
}


class RecordValidationError(ValueError):
    """Raised when an input field does not satisfy the record schema."""


def _validation_error(path, message):
    raise RecordValidationError(f"{path}: {message}")


def _required(mapping, key, path):
    if key not in mapping:
        _validation_error(f"{path}.{key}" if path else key, "缺少必需字段")
    return mapping[key]


def _require_mapping(value, path):
    if not isinstance(value, dict):
        _validation_error(path, "必须是对象")
    return value


def _require_nonempty_string(value, path):
    if not isinstance(value, str) or not value.strip():
        _validation_error(path, "必须是非空字符串")
    return value


def _require_number(value, path, *, integer=False, minimum=0):
    if isinstance(value, bool) or not isinstance(value, Real):
        _validation_error(path, "必须是数字")
    if isinstance(value, int):
        numeric_value = value
    else:
        try:
            numeric_value = float(value)
        except (OverflowError, ValueError):
            _validation_error(path, "数值超出支持范围")
        if not math.isfinite(numeric_value):
            _validation_error(path, "必须是有限数字")
    if value < minimum:
        _validation_error(path, f"必须大于或等于 {minimum}")
    if integer and not (
        isinstance(value, int) or numeric_value.is_integer()
    ):
        _validation_error(path, "必须是整数")
    return value


def _format_number(value):
    if isinstance(value, int) and not isinstance(value, bool):
        return str(value)
    if isinstance(value, Real) and not isinstance(value, bool):
        if float(value).is_integer():
            return str(int(value))
        return format(float(value), ".12g")
    return str(value)


def _round_half_up_nonnegative(value, path):
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    try:
        numeric_value = float(value)
        if not math.isfinite(numeric_value):
            raise ValueError
        return math.floor(numeric_value + 0.5)
    except (OverflowError, ValueError):
        _validation_error(path, "数值超出支持范围")


def _paths_refer_to_same_file(first_path, second_path):
    first = Path(first_path)
    second = Path(second_path)
    try:
        return first.resolve() == second.resolve()
    except (OSError, RuntimeError):
        return first.absolute() == second.absolute()


def _validate_optional_enum(mapping, key, allowed, path):
    if key not in mapping:
        return
    value = mapping[key]
    field_path = f"{path}.{key}"
    if not isinstance(value, str) or value not in allowed:
        _validation_error(field_path, f"必须是以下值之一：{', '.join(sorted(allowed))}")


def _require_enum(mapping, key, allowed, path):
    value = _require_nonempty_string(
        _required(mapping, key, path), f"{path}.{key}"
    )
    if value not in allowed:
        _validation_error(
            f"{path}.{key}", f"必须是以下值之一：{', '.join(sorted(allowed))}"
        )
    return value


def _validate_optional_id(mapping, path):
    if "id" in mapping:
        _require_nonempty_string(mapping["id"], f"{path}.id")


def _normalize_legacy_item(item):
    weight = item["weight_g"]
    item["quantity"] = {
        "value": weight,
        "unit": "g",
        "display": f"{_format_number(weight)}g",
        "method": "legacy",
        "estimated": True,
    }
    item["confidence"] = "medium"
    item["weight_g_basis"] = "legacy"


def _validate_v2_quantity(item, path):
    quantity_path = f"{path}.quantity"
    quantity = _require_mapping(_required(item, "quantity", path), quantity_path)
    value = _require_number(
        _required(quantity, "value", quantity_path), f"{quantity_path}.value"
    )
    unit = _require_nonempty_string(
        _required(quantity, "unit", quantity_path), f"{quantity_path}.unit"
    )
    if unit not in QUANTITY_UNITS:
        _validation_error(
            f"{quantity_path}.unit",
            f"必须是以下值之一：{', '.join(sorted(QUANTITY_UNITS))}",
        )
    _require_nonempty_string(
        _required(quantity, "display", quantity_path), f"{quantity_path}.display"
    )
    method = _require_nonempty_string(
        _required(quantity, "method", quantity_path), f"{quantity_path}.method"
    )
    if method not in QUANTITY_METHODS or method == "legacy":
        _validation_error(
            f"{quantity_path}.method",
            "2.0 记录必须使用非 legacy 的合法数量推导方法",
        )
    estimated = _required(quantity, "estimated", quantity_path)
    if not isinstance(estimated, bool):
        _validation_error(f"{quantity_path}.estimated", "必须是布尔值")

    has_gross = "gross_value" in quantity
    has_ratio = "edible_ratio" in quantity
    if has_gross != has_ratio:
        missing = "edible_ratio" if has_gross else "gross_value"
        _validation_error(f"{quantity_path}.{missing}", "带骨/壳/皮数量必须成对提供")
    if has_gross:
        gross = _require_number(quantity["gross_value"], f"{quantity_path}.gross_value")
        ratio = _require_number(
            quantity["edible_ratio"], f"{quantity_path}.edible_ratio", minimum=0
        )
        if ratio <= 0 or ratio > 1:
            _validation_error(f"{quantity_path}.edible_ratio", "必须在 (0, 1] 范围内")
        try:
            edible_value = gross * ratio
        except OverflowError:
            _validation_error(f"{quantity_path}.value", "数值超出支持范围")
        expected_edible = _round_half_up_nonnegative(
            edible_value, f"{quantity_path}.value"
        )
        if value != expected_edible:
            _validation_error(
                f"{quantity_path}.value",
                f"必须等于 floor(gross_value * edible_ratio + 0.5)，即 {expected_edible}",
            )

    weight = item["weight_g"]
    basis = _require_nonempty_string(
        _required(item, "weight_g_basis", path), f"{path}.weight_g_basis"
    )
    if basis not in WEIGHT_BASES or basis == "legacy":
        _validation_error(
            f"{path}.weight_g_basis",
            f"2.0 记录必须使用非 legacy 的合法值：{', '.join(sorted(WEIGHT_BASES - {'legacy'}))}",
        )

    projected = _round_half_up_nonnegative(value, f"{quantity_path}.value")
    if unit == "g":
        if basis != "edible_weight":
            _validation_error(f"{path}.weight_g_basis", "g 数量必须使用 edible_weight")
        if weight != projected:
            _validation_error(f"{path}.weight_g", f"必须等于可食用量的整数投影 {projected}")
    elif unit == "ml":
        if basis != "volume_proxy":
            _validation_error(f"{path}.weight_g_basis", "ml 数量必须使用 volume_proxy")
        if weight != projected:
            _validation_error(f"{path}.weight_g", f"必须等于容量的整数投影 {projected}")
    elif unit == "piece" and basis != "piece_estimate":
        _validation_error(f"{path}.weight_g_basis", "piece 数量必须使用 piece_estimate")
    elif unit == "serving" and basis not in {
        "serving_conversion",
        "volume_proxy",
        "unavailable",
    }:
        _validation_error(
            f"{path}.weight_g_basis",
            "serving 数量必须使用 serving_conversion、volume_proxy 或 unavailable",
        )
    if basis == "unavailable" and weight != 0:
        _validation_error(f"{path}.weight_g", "weight_g_basis 为 unavailable 时必须是 0")


def _validate_v2_calculation(item, path):
    calculation_path = f"{path}.calculation"
    calculation = _require_mapping(
        _required(item, "calculation", path), calculation_path
    )
    _require_enum(calculation, "method", CALCULATION_METHODS, calculation_path)
    _require_number(
        _required(calculation, "energy_value", calculation_path),
        f"{calculation_path}.energy_value",
    )
    _require_nonempty_string(
        _required(calculation, "energy_unit", calculation_path),
        f"{calculation_path}.energy_unit",
    )
    _require_enum(calculation, "source_type", SOURCE_TYPES, calculation_path)
    _require_nonempty_string(
        _required(calculation, "source_label", calculation_path),
        f"{calculation_path}.source_label",
    )


def _validate_notes(item, path, *, required):
    notes_path = f"{path}.notes"
    if required:
        notes = _required(item, "notes", path)
    elif "notes" in item:
        notes = item["notes"]
    else:
        return
    if not isinstance(notes, list):
        _validation_error(notes_path, "必须是数组")
    for index, note in enumerate(notes):
        if not isinstance(note, str):
            _validation_error(f"{notes_path}[{index}]", "必须是字符串")


def _normalize_item(raw_item, path, schema_version):
    item = _require_mapping(raw_item, path)
    if schema_version == "2.0":
        _require_nonempty_string(_required(item, "id", path), f"{path}.id")
    else:
        _validate_optional_id(item, path)
    _require_nonempty_string(_required(item, "name", path), f"{path}.name")
    weight = _require_number(
        _required(item, "weight_g", path),
        f"{path}.weight_g",
        integer=schema_version == "2.0",
    )
    calories = _require_number(
        _required(item, "calories", path),
        f"{path}.calories",
        integer=schema_version == "2.0",
    )

    if schema_version == "1.0":
        _normalize_legacy_item(item)
    else:
        item["weight_g"] = int(weight)
        item["calories"] = int(calories)
        _validate_v2_quantity(item, path)
        _require_enum(item, "confidence", CONFIDENCE_LEVELS, path)
        _validate_notes(item, path, required=True)
        _validate_v2_calculation(item, path)

    if schema_version == "1.0":
        _validate_notes(item, path, required=False)
        if "calculation" in item:
            calculation_path = f"{path}.calculation"
            calculation = _require_mapping(item["calculation"], calculation_path)
            _validate_optional_enum(
                calculation, "method", CALCULATION_METHODS, calculation_path
            )
            _validate_optional_enum(
                calculation, "source_type", SOURCE_TYPES, calculation_path
            )
    return item


def normalize_record(data):
    """Validate and return a deep-copied, renderer-ready record.

    Missing ``schema_version`` is treated as legacy schema 1.0. Totals are always
    derived from stored item ``calories`` values, never trusted from input.
    """

    record = copy.deepcopy(_require_mapping(data, "$"))
    schema_version = record.get("schema_version", "1.0")
    if not isinstance(schema_version, str):
        _validation_error("schema_version", "必须是字符串")
    if schema_version not in {"1.0", "2.0"}:
        _validation_error("schema_version", "仅支持 1.0 或 2.0")
    record["schema_version"] = schema_version

    date_value = _require_nonempty_string(_required(record, "date", ""), "date")
    try:
        parsed_date = datetime.strptime(date_value, "%Y-%m-%d")
    except ValueError:
        _validation_error("date", "必须使用有效的 YYYY-MM-DD 日期")
    if parsed_date.strftime("%Y-%m-%d") != date_value:
        _validation_error("date", "必须使用有效的 YYYY-MM-DD 日期")

    meals = _required(record, "meals", "")
    if not isinstance(meals, list):
        _validation_error("meals", "必须是数组")
    if not meals:
        _validation_error("meals", "至少需要一个餐次")

    normalized_meals = []
    day_calories = 0
    meal_ids = set()
    item_ids = set()
    for meal_index, raw_meal in enumerate(meals):
        meal_path = f"meals[{meal_index}]"
        meal = _require_mapping(raw_meal, meal_path)
        if schema_version == "2.0":
            meal_id = _require_nonempty_string(
                _required(meal, "id", meal_path), f"{meal_path}.id"
            )
            if meal_id in meal_ids:
                _validation_error(f"{meal_path}.id", f"重复的 meal ID：{meal_id}")
            meal_ids.add(meal_id)
        else:
            _validate_optional_id(meal, meal_path)
        _require_nonempty_string(
            _required(meal, "meal_type", meal_path), f"{meal_path}.meal_type"
        )

        items = _required(meal, "items", meal_path)
        if not isinstance(items, list):
            _validation_error(f"{meal_path}.items", "必须是数组")
        if not items:
            _validation_error(f"{meal_path}.items", "至少需要一个食物条目")
        normalized_items = []
        for item_index, item in enumerate(items):
            item_path = f"{meal_path}.items[{item_index}]"
            normalized_item = _normalize_item(item, item_path, schema_version)
            if schema_version == "2.0":
                item_id = normalized_item["id"]
                if item_id in item_ids:
                    _validation_error(item_path + ".id", f"重复的 item ID：{item_id}")
                item_ids.add(item_id)
            normalized_items.append(normalized_item)
        meal["items"] = normalized_items

        images = (
            _required(meal, "images", meal_path)
            if schema_version == "2.0"
            else meal.get("images", [])
        )
        if not isinstance(images, list):
            _validation_error(f"{meal_path}.images", "必须是字符串路径数组")
        for image_index, image_path in enumerate(images):
            if not isinstance(image_path, str) or not image_path:
                _validation_error(
                    f"{meal_path}.images[{image_index}]", "必须是非空字符串路径"
                )
        meal["images"] = images

        if schema_version == "2.0":
            totals_path = f"{meal_path}.totals"
            totals = _require_mapping(
                _required(meal, "totals", meal_path), totals_path
            )
            _require_number(
                _required(totals, "calories", totals_path),
                f"{totals_path}.calories",
                integer=True,
            )
        elif "totals" in meal:
            totals_path = f"{meal_path}.totals"
            totals = _require_mapping(meal["totals"], totals_path)
            if "calories" in totals:
                _require_number(totals["calories"], f"{totals_path}.calories")
        meal_calories = sum(item["calories"] for item in meal["items"])
        _require_number(
            meal_calories,
            f"{meal_path}.totals.calories",
            integer=schema_version == "2.0",
        )
        meal["totals"] = {"calories": meal_calories}
        day_calories += meal_calories
        normalized_meals.append(meal)

    if schema_version == "2.0":
        totals = _require_mapping(_required(record, "totals", ""), "totals")
        _require_number(
            _required(totals, "calories", "totals"),
            "totals.calories",
            integer=True,
        )
    elif "totals" in record:
        totals = _require_mapping(record["totals"], "totals")
        if "calories" in totals:
            _require_number(totals["calories"], "totals.calories")
    _require_number(
        day_calories,
        "totals.calories",
        integer=schema_version == "2.0",
    )
    record["meals"] = normalized_meals
    record["totals"] = {"calories": day_calories}
    return record


def _discover_fonts():
    """Return platform-appropriate Chinese-capable bold and regular font paths."""

    bold = []
    regular = []
    system = platform.system()

    if system == "Darwin":
        bold.extend(
            [
                "/System/Library/Fonts/PingFang.ttc",
                "/System/Library/Fonts/STHeiti Medium.ttc",
                "/Library/Fonts/Arial Unicode.ttf",
            ]
        )
        regular.extend(
            [
                "/System/Library/Fonts/PingFang.ttc",
                "/System/Library/Fonts/STHeiti Light.ttc",
                "/Library/Fonts/Arial Unicode.ttf",
            ]
        )
    elif system == "Windows":
        windows_fonts = Path("C:/Windows/Fonts")
        bold.extend([str(windows_fonts / "msyhbd.ttc"), str(windows_fonts / "simhei.ttf")])
        regular.extend(
            [
                str(windows_fonts / "msyh.ttc"),
                str(windows_fonts / "simsun.ttc"),
                str(windows_fonts / "simhei.ttf"),
            ]
        )

    bold.extend(
        [
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
            "/usr/share/fonts/noto-cjk/NotoSansCJK-Bold.ttc",
        ]
    )
    regular.extend(
        [
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
            "/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc",
            "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
        ]
    )

    try:
        output = subprocess.check_output(
            ["fc-list", ":lang=zh", "file"],
            text=True,
            timeout=5,
            stderr=subprocess.DEVNULL,
        )
        for line in output.strip().splitlines():
            font_path = line.split(":")[0].strip()
            (bold if "Bold" in font_path else regular).append(font_path)
    except Exception:
        pass
    return bold, regular


FONT_BOLD_CANDIDATES, FONT_REGULAR_CANDIDATES = _discover_fonts()


def _load_font(candidates, size):
    for font_path in candidates:
        try:
            return ImageFont.truetype(font_path, size)
        except (OSError, IOError):
            continue
    try:
        return ImageFont.truetype("DejaVuSans.ttf", size)
    except (OSError, IOError):
        return ImageFont.load_default()


def load_fonts():
    return {
        "title": _load_font(FONT_BOLD_CANDIDATES, FS_TITLE),
        "header": _load_font(FONT_BOLD_CANDIDATES, FS_HEADER),
        "meal": _load_font(FONT_BOLD_CANDIDATES, FS_MEAL),
        "cell": _load_font(FONT_REGULAR_CANDIDATES, FS_CELL),
        "num": _load_font(FONT_REGULAR_CANDIDATES, FS_NUM),
        "subtotal": _load_font(FONT_BOLD_CANDIDATES, FS_SUBTOTAL),
        "total_l": _load_font(FONT_BOLD_CANDIDATES, FS_TOTAL_L),
        "total_n": _load_font(FONT_BOLD_CANDIDATES, FS_TOTAL_N),
        "photo": _load_font(FONT_BOLD_CANDIDATES, FS_PHOTO),
    }


def text_size(draw, text, font):
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def column_positions():
    widths = []
    remaining = CONTENT_WIDTH
    for ratio in COL_RATIOS[:-1]:
        width = int(round(CONTENT_WIDTH * ratio))
        widths.append(width)
        remaining -= width
    widths.append(remaining)

    positions = []
    x = PAD
    for width in widths:
        positions.append((x, width))
        x += width
    return positions


def wrap_text(draw, text, font, max_width):
    """Wrap text by rendered pixel width, preserving explicit line breaks."""

    lines = []
    for paragraph in str(text).split("\n"):
        if paragraph == "":
            lines.append("")
            continue
        current = ""
        for character in paragraph:
            candidate = current + character
            if current and text_size(draw, candidate, font)[0] > max_width:
                lines.append(current)
                current = character
            else:
                current = candidate
        lines.append(current)
    return lines or [""]


def _line_height(draw, font):
    return max(1, text_size(draw, "国Ag", font)[1])


def _block_height(draw, lines, font):
    return len(lines) * _line_height(draw, font) + max(0, len(lines) - 1) * LINE_SPACING


def _draw_lines(draw, lines, font, fill, box, *, align="left"):
    x, y, width, height = box
    line_height = _line_height(draw, font)
    block_height = _block_height(draw, lines, font)
    line_y = y + (height - block_height) / 2
    for line in lines:
        line_width, _ = text_size(draw, line, font)
        if align == "center":
            line_x = x + (width - line_width) / 2
        else:
            line_x = x
        draw.text((line_x, line_y), line, fill=fill, font=font, anchor="lt")
        line_y += line_height + LINE_SPACING


def build_meal_data(meals):
    """Build rendering rows while deriving all totals from stored item calories."""

    groups = []
    for meal in meals:
        items = []
        for item in meal["items"]:
            quantity = item.get("quantity")
            quantity_display = (
                quantity["display"]
                if isinstance(quantity, dict) and "display" in quantity
                else f"{_format_number(item['weight_g'])}g"
            )
            items.append(
                {
                    "name": item["name"],
                    "quantity_display": quantity_display,
                    "calories": item["calories"],
                }
            )
        groups.append(
            {
                "meal_type": meal["meal_type"],
                "items": items,
                "meal_calories": sum(item["calories"] for item in meal["items"]),
            }
        )
    return groups


def build_table_layout(meal_groups, draw, fonts):
    """Calculate wrapped lines and row heights before allocating the canvas."""

    columns = column_positions()
    food_width = columns[1][1] - CELL_PAD_H * 2
    quantity_width = columns[2][1] - CELL_PAD_H * 2
    meal_width = columns[0][1] - CELL_PAD_H * 2
    groups = []

    for group in meal_groups:
        rows = []
        for item in group["items"]:
            name_lines = wrap_text(draw, item["name"], fonts["cell"], food_width)
            quantity_lines = wrap_text(
                draw, item["quantity_display"], fonts["num"], quantity_width
            )
            content_height = max(
                _block_height(draw, name_lines, fonts["cell"]),
                _block_height(draw, quantity_lines, fonts["num"]),
                _line_height(draw, fonts["num"]),
            )
            rows.append(
                {
                    **item,
                    "name_lines": name_lines,
                    "quantity_lines": quantity_lines,
                    "height": max(ROW_MIN_H, content_height + CELL_PAD_V * 2),
                }
            )

        meal_lines = wrap_text(draw, group["meal_type"], fonts["meal"], meal_width)
        group_height = sum(row["height"] for row in rows)
        needed_meal_height = _block_height(draw, meal_lines, fonts["meal"]) + CELL_PAD_V * 2
        if needed_meal_height > group_height:
            rows[-1]["height"] += needed_meal_height - group_height
            group_height = needed_meal_height

        groups.append(
            {
                **group,
                "rows": rows,
                "meal_lines": meal_lines,
                "height": group_height,
            }
        )

    table_height = HEADER_H + sum(group["height"] + SUBTOTAL_H for group in groups) + TOTAL_H
    return groups, table_height


def collect_images(meals):
    result = []
    for meal in meals:
        for image_path in meal.get("images", []):
            result.append((meal["meal_type"], image_path))
    return result


def _scaled_photo_height(width, height):
    return max(1, int(round(height * (CONTENT_WIDTH / width))))


def _oriented_photo_size(image_path):
    with Image.open(image_path) as source:
        oriented = ImageOps.exif_transpose(source)
        return oriented.size


def _open_oriented_rgb(image_path):
    with Image.open(image_path) as source:
        oriented = ImageOps.exif_transpose(source)
        return oriented.convert("RGB")


def calc_photo_height(photo_list):
    if not photo_list:
        return 0
    height = PHOTO_SECTION_GAP
    for index, (_, image_path) in enumerate(photo_list):
        height += PHOTO_LABEL_H
        try:
            width, source_height = _oriented_photo_size(image_path)
            if width <= 0 or source_height <= 0:
                raise ValueError("invalid image dimensions")
            height += _scaled_photo_height(width, source_height)
        except Exception:
            height += PHOTO_ERROR_H
        if index < len(photo_list) - 1:
            height += PHOTO_GAP
    return height


def _draw_table(draw, y, table_groups, total_calories, fonts):
    columns = column_positions()

    draw.rectangle(
        (PAD, y, PAD + CONTENT_WIDTH, y + HEADER_H),
        fill=HEADER_BG,
        outline=BORDER,
        width=BORDER_W,
    )
    headers = ["餐次", "食物", "数量", "热量(千卡)"]
    for index, header in enumerate(headers):
        column_x, column_width = columns[index]
        draw.text(
            (column_x + column_width / 2, y + HEADER_H / 2),
            header,
            fill=HEADER_TEXT,
            font=fonts["header"],
            anchor="mm",
        )
    for index in range(1, 4):
        line_x = columns[index][0]
        draw.line((line_x, y, line_x, y + HEADER_H), fill=BORDER, width=BORDER_W)
    y += HEADER_H

    for group in table_groups:
        group_y = y
        for row in group["rows"]:
            row_height = row["height"]
            draw.rectangle(
                (columns[1][0], y, PAD + CONTENT_WIDTH, y + row_height),
                fill=BG,
                outline=BORDER,
                width=BORDER_W,
            )
            for column_index in range(2, 4):
                line_x = columns[column_index][0]
                draw.line((line_x, y, line_x, y + row_height), fill=BORDER, width=BORDER_W)

            _draw_lines(
                draw,
                row["name_lines"],
                fonts["cell"],
                CELL_TEXT,
                (
                    columns[1][0] + CELL_PAD_H,
                    y,
                    columns[1][1] - CELL_PAD_H * 2,
                    row_height,
                ),
            )
            _draw_lines(
                draw,
                row["quantity_lines"],
                fonts["num"],
                NUM_TEXT,
                (
                    columns[2][0] + CELL_PAD_H,
                    y,
                    columns[2][1] - CELL_PAD_H * 2,
                    row_height,
                ),
                align="center",
            )
            draw.text(
                (columns[3][0] + columns[3][1] / 2, y + row_height / 2),
                _format_number(row["calories"]),
                fill=NUM_TEXT,
                font=fonts["num"],
                anchor="mm",
            )
            y += row_height

        draw.rectangle(
            (PAD, group_y, columns[1][0], group_y + group["height"]),
            fill=BG,
            outline=BORDER,
            width=BORDER_W,
        )
        _draw_lines(
            draw,
            group["meal_lines"],
            fonts["meal"],
            MEAL_TEXT,
            (
                columns[0][0] + CELL_PAD_H,
                group_y,
                columns[0][1] - CELL_PAD_H * 2,
                group["height"],
            ),
            align="center",
        )

        draw.rectangle(
            (PAD, y, PAD + CONTENT_WIDTH, y + SUBTOTAL_H),
            fill=SUBTOTAL_BG,
            outline=BORDER,
            width=BORDER_W,
        )
        for line_x in (columns[2][0], columns[3][0]):
            draw.line((line_x, y, line_x, y + SUBTOTAL_H), fill=BORDER, width=BORDER_W)
        subtotal_mid_y = y + SUBTOTAL_H / 2
        first_two_width = columns[0][1] + columns[1][1]
        draw.text(
            (PAD + first_two_width / 2, subtotal_mid_y),
            f"{group['meal_type']}小计",
            fill=TOTAL_TEXT,
            font=fonts["subtotal"],
            anchor="mm",
        )
        draw.text(
            (columns[2][0] + columns[2][1] / 2, subtotal_mid_y),
            "—",
            fill=TOTAL_TEXT,
            font=fonts["subtotal"],
            anchor="mm",
        )
        draw.text(
            (columns[3][0] + columns[3][1] / 2, subtotal_mid_y),
            _format_number(group["meal_calories"]),
            fill=TOTAL_TEXT,
            font=fonts["subtotal"],
            anchor="mm",
        )
        y += SUBTOTAL_H

    draw.rectangle(
        (PAD, y, PAD + CONTENT_WIDTH, y + TOTAL_H),
        fill=TOTAL_BG,
        outline=BORDER,
        width=BORDER_W,
    )
    draw.line((columns[3][0], y, columns[3][0], y + TOTAL_H), fill=BORDER, width=BORDER_W)
    total_mid_y = y + TOTAL_H / 2
    first_three_width = columns[0][1] + columns[1][1] + columns[2][1]
    draw.text(
        (PAD + first_three_width / 2, total_mid_y),
        "全天合计",
        fill=TOTAL_TEXT,
        font=fonts["total_l"],
        anchor="mm",
    )
    draw.text(
        (columns[3][0] + columns[3][1] / 2, total_mid_y),
        _format_number(total_calories),
        fill=TOTAL_TEXT,
        font=fonts["total_n"],
        anchor="mm",
    )
    return y + TOTAL_H


def _draw_photos(canvas, draw, y, photo_list, fonts):
    if not photo_list:
        return y
    y += PHOTO_SECTION_GAP
    resampling = getattr(Image, "Resampling", Image).LANCZOS

    for index, (meal_type, image_path) in enumerate(photo_list):
        draw.rounded_rectangle(
            (PAD, y, PAD + CONTENT_WIDTH, y + PHOTO_LABEL_H),
            radius=4,
            fill=PHOTO_LABEL_BG,
        )
        draw.text(
            (PAD + 10, y + PHOTO_LABEL_H / 2),
            f"[ {meal_type} ]",
            fill=PHOTO_LABEL_TEXT,
            font=fonts["photo"],
            anchor="lm",
        )
        y += PHOTO_LABEL_H

        try:
            with _open_oriented_rgb(image_path) as photo:
                if photo.width <= 0 or photo.height <= 0:
                    raise ValueError("invalid image dimensions")
                new_height = _scaled_photo_height(photo.width, photo.height)
                with photo.resize((CONTENT_WIDTH, new_height), resampling) as resized:
                    canvas.paste(resized, (PAD, y))
                y += new_height
        except Exception:
            draw.rectangle(
                (PAD, y, PAD + CONTENT_WIDTH, y + PHOTO_ERROR_H), fill=PLACEHOLDER_BG
            )
            draw.text(
                (PAD + 10, y + PHOTO_ERROR_H / 2),
                "图片加载失败",
                fill=PLACEHOLDER_TEXT,
                font=fonts["cell"],
                anchor="lm",
            )
            y += PHOTO_ERROR_H

        if index < len(photo_list) - 1:
            y += PHOTO_GAP
    return y


def generate_summary(data, output_path):
    """Normalize ``data`` and render it to ``output_path`` as PNG."""

    record = normalize_record(data)
    output = Path(output_path)
    for meal_index, meal in enumerate(record["meals"]):
        for image_index, image_path in enumerate(meal["images"]):
            if _paths_refer_to_same_file(image_path, output):
                _validation_error(
                    f"meals[{meal_index}].images[{image_index}]",
                    "图片路径不能与输出路径相同",
                )
    meals = record["meals"]
    photo_list = collect_images(meals)
    fonts = load_fonts()

    measurement_canvas = Image.new("RGB", (CANVAS_WIDTH, 1), BG)
    measurement_draw = ImageDraw.Draw(measurement_canvas)
    meal_groups = build_meal_data(meals)
    table_groups, table_height = build_table_layout(meal_groups, measurement_draw, fonts)
    measurement_canvas.close()

    title_height = TITLE_TOP_PAD + TITLE_TEXT_H + TITLE_BOT_PAD
    photo_height = calc_photo_height(photo_list)
    canvas_height = title_height + table_height + photo_height + BOTTOM_PAD
    canvas = Image.new("RGB", (CANVAS_WIDTH, canvas_height), BG)
    draw = ImageDraw.Draw(canvas)

    title = f"{record['date']} 饮食摄入明细"
    title_width, _ = text_size(draw, title, fonts["title"])
    draw.text(
        ((CANVAS_WIDTH - title_width) / 2, TITLE_TOP_PAD),
        title,
        fill=TITLE_COLOR,
        font=fonts["title"],
        anchor="lt",
    )

    y = title_height
    y = _draw_table(draw, y, table_groups, record["totals"]["calories"], fonts)
    y = _draw_photos(canvas, draw, y, photo_list, fonts)

    if y + BOTTOM_PAD != canvas.height:
        canvas = canvas.crop((0, 0, CANVAS_WIDTH, y + BOTTOM_PAD))
    output.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output, "PNG")
    canvas.close()
    print(f"汇总长图已保存: {output}")
    return output


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", required=True, help="输入 JSON 路径")
    parser.add_argument("--output", required=True, help="输出 PNG 路径")
    args = parser.parse_args(argv)

    if _paths_refer_to_same_file(args.data, args.output):
        print("输入 JSON 路径不能与输出 PNG 路径相同", file=sys.stderr)
        return 2

    try:
        with open(args.data, "r", encoding="utf-8") as file:
            data = json.load(file)
    except json.JSONDecodeError as exc:
        print(
            f"输入 JSON 解析失败: {args.data}:{exc.lineno}:{exc.colno}: {exc.msg}",
            file=sys.stderr,
        )
        return 2
    except OSError as exc:
        print(f"无法读取输入 JSON {args.data}: {exc}", file=sys.stderr)
        return 2

    try:
        generate_summary(data, args.output)
    except RecordValidationError as exc:
        print(f"输入数据错误: {exc}", file=sys.stderr)
        return 2
    except OSError as exc:
        print(f"无法生成输出图片 {args.output}: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

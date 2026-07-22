#!/usr/bin/env python3
"""
食物热量追踪 - 每日汇总长图生成器 v4

参考样式：
- 标题：一句话描述（如"2026年03月15日饮食摄入明细"）
- 表格：餐次/加餐 | 食物（带规格） | 重量(g) | 热量(千卡)
  每个餐次的食物用顿号拼接为一个单元格，餐次名称垂直居中
- 合计行在底部
- 照片：保持原比例，等宽缩放，从上到下排列
"""

import argparse
import json
import platform
import subprocess
import sys
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


# ── 画布 ──────────────────────────────────────────────────

CANVAS_WIDTH = 750
PAD = 28  # 水平内边距
CW = CANVAS_WIDTH - PAD * 2  # 内容宽度

# ── 颜色 ──────────────────────────────────────────────────

BG              = "#F8F4F0"
TITLE_COLOR     = "#2A2A2A"
BORDER          = "#C0B8B0"
HEADER_BG       = "#EDE8E3"
HEADER_TEXT      = "#444444"
MEAL_TEXT        = "#2A2A2A"
CELL_TEXT        = "#333333"
NUM_TEXT         = "#333333"
TOTAL_BG        = "#EDE8E3"
TOTAL_TEXT       = "#2A2A2A"
PHOTO_LABEL_BG  = "#EDE8E3"
PHOTO_LABEL_TEXT = "#666666"

# ── 字体大小 ──────────────────────────────────────────────

FS_TITLE   = 28
FS_HEADER  = 18
FS_MEAL    = 22
FS_CELL    = 17
FS_NUM     = 17
FS_TOTAL_L = 22
FS_TOTAL_N = 26
FS_PHOTO   = 18

# ── 表格尺寸 ──────────────────────────────────────────────

TITLE_TOP_PAD   = 24
TITLE_BOT_PAD   = 20
HEADER_H        = 42
BORDER_W        = 1
CELL_PAD_V      = 14     # 单元格上下内边距
CELL_PAD_H      = 12     # 单元格左右内边距
TOTAL_H         = 56
TEXT_WRAP_WIDTH  = 18     # 食物描述列的中文字符折行宽度

# 列宽比例：餐次 | 食物 | 重量 | 热量
COL_RATIOS = [0.13, 0.50, 0.17, 0.20]

# ── 照片 ──────────────────────────────────────────────────

PHOTO_SECTION_GAP = 28
PHOTO_GAP = 10
PHOTO_LABEL_H = 38


# ── 字体发现 ──────────────────────────────────────────────

def _discover():
    """
    跨平台字体发现，统一优先级：
    1. 苹方 PingFang SC (macOS)
    2. 微软雅黑 Microsoft YaHei (Windows)
    3. Noto Sans CJK SC (Linux/通用)
    4. 文泉驿正黑 (Linux 回退)
    """
    bold, regular = [], []
    s = platform.system()

    # macOS — 苹方优先
    if s == "Darwin":
        bold += [
            "/System/Library/Fonts/PingFang.ttc",
            "/System/Library/Fonts/STHeiti Medium.ttc",
            "/Library/Fonts/Arial Unicode.ttf",
        ]
        regular += [
            "/System/Library/Fonts/PingFang.ttc",
            "/System/Library/Fonts/STHeiti Light.ttc",
            "/Library/Fonts/Arial Unicode.ttf",
        ]

    # Windows — 微软雅黑优先
    elif s == "Windows":
        wf = Path("C:/Windows/Fonts")
        bold += [
            str(wf / "msyhbd.ttc"),    # 微软雅黑 Bold
            str(wf / "simhei.ttf"),     # 黑体
        ]
        regular += [
            str(wf / "msyh.ttc"),       # 微软雅黑
            str(wf / "simsun.ttc"),      # 宋体
            str(wf / "simhei.ttf"),
        ]

    # Linux — Noto Sans CJK 优先，文泉驿回退
    if s == "Linux" or True:  # 所有平台都追加 Noto 作为兜底
        bold += [
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
            "/usr/share/fonts/noto-cjk/NotoSansCJK-Bold.ttc",
        ]
        regular += [
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
            "/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc",
            "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
        ]
        # fc-list 动态补充
        try:
            out = subprocess.check_output(["fc-list", ":lang=zh", "file"], text=True, timeout=5)
            for ln in out.strip().splitlines():
                p = ln.split(":")[0].strip()
                (bold if "Bold" in p else regular).append(p)
        except Exception:
            pass

    return bold, regular

FB, FR = _discover()


def lfont(cands, size):
    for p in cands:
        try:
            return ImageFont.truetype(p, size)
        except (OSError, IOError):
            continue
    return ImageFont.load_default()


def tsz(draw, text, font):
    bb = draw.textbbox((0, 0), text, font=font)
    return bb[2] - bb[0], bb[3] - bb[1]


# ── 列位置 ────────────────────────────────────────────────

def cols():
    positions = []
    x = PAD
    for r in COL_RATIOS:
        w = int(CW * r)
        positions.append((x, w))
        x += w
    return positions


# ── 食物描述折行 ──────────────────────────────────────────

ROW_H = 36  # 每种食物的固定行高


def build_meal_data(meals):
    """
    构建扁平化的行数据。每种食物一行。
    返回 meal_groups: [{meal_type, items: [{name, weight_g, calories}], meal_cal}]
    """
    groups = []
    for m in meals:
        meal_cal = sum(it["calories"] for it in m["items"])
        groups.append({
            "meal_type": m["meal_type"],
            "items": m["items"],
            "meal_cal": meal_cal,
        })
    return groups


# ── 照片收集 ──────────────────────────────────────────────

def collect_images(meals):
    result = []
    for m in meals:
        for p in m.get("images", []):
            result.append((m["meal_type"], p))
    return result


def calc_photo_height(photo_list):
    if not photo_list:
        return 0
    h = PHOTO_SECTION_GAP
    for i, (_, path) in enumerate(photo_list):
        h += PHOTO_LABEL_H
        try:
            with Image.open(path) as img:
                w, ht = img.width, img.height
                # 竖拍旋转后宽高互换
                if ht > w:
                    w, ht = ht, w
                ratio = CW / w
                h += int(ht * ratio)
        except Exception:
            h += 150
        if i < len(photo_list) - 1:
            h += PHOTO_GAP
    return h


# ── 主绘制 ────────────────────────────────────────────────

def generate_summary(data, output_path):
    meals = data["meals"]
    date_str = data.get("date", "未知日期")
    photo_list = collect_images(meals)
    total_cal = sum(sum(it["calories"] for it in m["items"]) for m in meals)
    total_weight = sum(sum(it["weight_g"] for it in m["items"]) for m in meals)

    fonts = {
        "title":   lfont(FB, FS_TITLE),
        "header":  lfont(FB, FS_HEADER),
        "meal":    lfont(FB, FS_MEAL),
        "cell":    lfont(FR, FS_CELL),
        "num":     lfont(FR, FS_NUM),
        "total_l": lfont(FB, FS_TOTAL_L),
        "total_n": lfont(FB, FS_TOTAL_N),
        "photo":   lfont(FB, FS_PHOTO),
    }

    c = cols()
    meal_groups = build_meal_data(meals)

    # 总高度
    title_h = TITLE_TOP_PAD + 36 + TITLE_BOT_PAD
    total_rows = sum(len(g["items"]) for g in meal_groups)
    table_h = HEADER_H + total_rows * ROW_H + TOTAL_H
    photo_h = calc_photo_height(photo_list)
    canvas_h = title_h + table_h + photo_h + 40

    img = Image.new("RGB", (CANVAS_WIDTH, canvas_h), BG)
    draw = ImageDraw.Draw(img)

    y = TITLE_TOP_PAD

    # ── 标题 ──
    title = f"{date_str} 饮食摄入明细"
    tw, _ = tsz(draw, title, fonts["title"])
    draw.text(((CANVAS_WIDTH - tw) // 2, y), title,
              fill=TITLE_COLOR, font=fonts["title"])
    y += 36 + TITLE_BOT_PAD

    # ── 表头 ──
    draw.rectangle((PAD, y, PAD + CW, y + HEADER_H), fill=HEADER_BG, outline=BORDER, width=BORDER_W)
    headers = ["餐次", "食物", "重量(g)", "热量(千卡)"]
    header_mid_y = y + HEADER_H // 2
    for i, h in enumerate(headers):
        cx, cw = c[i]
        draw.text((cx + cw // 2, header_mid_y), h,
                  fill=HEADER_TEXT, font=fonts["header"], anchor="mm")
    for i in range(1, 4):
        lx = c[i][0]
        draw.line((lx, y, lx, y + HEADER_H), fill=BORDER, width=BORDER_W)
    y += HEADER_H

    # ── 数据行（每种食物独立一行，餐次名垂直合并居中） ──
    for group in meal_groups:
        items = group["items"]
        n = len(items)
        group_h = n * ROW_H
        group_y = y

        for idx, item in enumerate(items):
            row_y = y + idx * ROW_H
            row_mid_y = row_y + ROW_H // 2

            # 食物+重量+热量 三列的独立单元格
            draw.rectangle(
                (c[1][0], row_y, PAD + CW, row_y + ROW_H),
                fill=BG, outline=BORDER, width=BORDER_W
            )
            for ci in range(2, 4):
                lx = c[ci][0]
                draw.line((lx, row_y, lx, row_y + ROW_H), fill=BORDER, width=BORDER_W)

            # 食物名称（左对齐，垂直居中）
            draw.text((c[1][0] + CELL_PAD_H, row_mid_y),
                      item["name"], fill=CELL_TEXT, font=fonts["cell"], anchor="lm")

            # 重量（水平+垂直居中）
            draw.text((c[2][0] + c[2][1] // 2, row_mid_y),
                      str(item["weight_g"]), fill=NUM_TEXT, font=fonts["num"], anchor="mm")

            # 热量（水平+垂直居中）
            draw.text((c[3][0] + c[3][1] // 2, row_mid_y),
                      str(item["calories"]), fill=NUM_TEXT, font=fonts["num"], anchor="mm")

        # 餐次列：合并单元格
        draw.rectangle(
            (PAD, group_y, c[1][0], group_y + group_h),
            fill=BG, outline=BORDER, width=BORDER_W
        )
        draw.text((c[0][0] + c[0][1] // 2, group_y + group_h // 2),
                  group["meal_type"], fill=MEAL_TEXT, font=fonts["meal"], anchor="mm")

        y += group_h

    # ── 合计行 ──
    draw.rectangle((PAD, y, PAD + CW, y + TOTAL_H), fill=TOTAL_BG, outline=BORDER, width=BORDER_W)
    for i in range(1, 4):
        lx = c[i][0]
        draw.line((lx, y, lx, y + TOTAL_H), fill=BORDER, width=BORDER_W)
    total_mid_y = y + TOTAL_H // 2

    draw.text((c[0][0] + c[0][1] // 2, total_mid_y),
              "合计", fill=TOTAL_TEXT, font=fonts["total_l"], anchor="mm")
    draw.text((c[1][0] + c[1][1] // 2, total_mid_y),
              "—", fill=TOTAL_TEXT, font=fonts["total_l"], anchor="mm")
    draw.text((c[2][0] + c[2][1] // 2, total_mid_y),
              str(total_weight), fill=TOTAL_TEXT, font=fonts["total_n"], anchor="mm")
    draw.text((c[3][0] + c[3][1] // 2, total_mid_y),
              str(total_cal), fill=TOTAL_TEXT, font=fonts["total_n"], anchor="mm")

    y += TOTAL_H

    # ── 照片区域 ──
    if photo_list:
        y += PHOTO_SECTION_GAP
        for i, (meal_type, img_path) in enumerate(photo_list):
            # 餐次标签
            draw.rounded_rectangle(
                (PAD, y, PAD + CW, y + PHOTO_LABEL_H),
                radius=4, fill=PHOTO_LABEL_BG
            )
            draw.text((PAD + 10, y + PHOTO_LABEL_H // 2),
                      f"[ {meal_type} ]", fill=PHOTO_LABEL_TEXT,
                      font=fonts["photo"], anchor="lm")
            y += PHOTO_LABEL_H

            # 照片（竖拍旋转横放，横拍保持原样，等宽缩放）
            try:
                with Image.open(img_path) as photo:
                    photo = photo.convert("RGB")
                    # 竖拍照片（高 > 宽）顺时针旋转90度横放
                    if photo.height > photo.width:
                        photo = photo.rotate(-90, expand=True)
                    ratio = CW / photo.width
                    new_w = CW
                    new_h = int(photo.height * ratio)
                    resized = photo.resize((new_w, new_h), Image.LANCZOS)
                    img.paste(resized, (PAD, y))
                    y += new_h
            except Exception:
                draw.rectangle((PAD, y, PAD + CW, y + 150), fill="#F0F0F0")
                draw.text((PAD + 10, y + 65), "图片加载失败", fill="#999", font=fonts["cell"])
                y += 150

            if i < len(photo_list) - 1:
                y += PHOTO_GAP

    # 裁掉多余空白
    img = img.crop((0, 0, CANVAS_WIDTH, y + 30))

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(str(out), "PNG", quality=95)
    print(f"汇总长图已保存: {out}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    with open(args.data, "r", encoding="utf-8") as f:
        generate_summary(json.load(f), args.output)


if __name__ == "__main__":
    main()

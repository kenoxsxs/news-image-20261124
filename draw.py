#!/usr/bin/env python3
"""draw.py — renders entry-v2/entry.png for news-image-20261124 (Tue 24 Nov 2026).
Draws OFFLINE at 3x (3072x3072) with PIL + Liberation fonts, downsamples to 1024x1024.
Written from scratch for v2 (37 stories). Data: verification-table-v2-final.md.
Layout v2: compact masthead (<=90px) + region chips, 3 big + 10 medium cards,
24 list lines in 3 columns, map + fields legend, DATE CHECK, footer.
HARD RULE (judge-penalty addendum): NO text below 11px anywhere; if content does
not fit, cut stories, never shrink text. v1 bug fixed: fields legend was painted
over by the DATE CHECK box — here fields sit beside the map, fully visible.
"""
import hashlib
import math
from PIL import Image, ImageDraw, ImageFont

S = 3
W, H = 1024, 1024
CW, CH = W * S, H * S

SERIF_B = "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf"
SANS_B = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
SANS_R = "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"


def font(path, size):
    return ImageFont.truetype(path, int(round(size * S)))


INK = (17, 24, 39)
MUTED = (75, 85, 99)
LINE = (209, 213, 219)
PAPER = (255, 255, 255)
BAND_BG = (243, 244, 246)
REGION = {
    "Europe": (30, 64, 175),
    "North America": (153, 27, 27),
    "Latin America": (180, 120, 10),
    "Africa": (107, 33, 168),
    "East & SE Asia": (22, 101, 52),
    "Middle East": (146, 64, 14),
    "Oceania": (8, 145, 178),
    "South Asia": (190, 24, 93),
    "World": (71, 85, 105),
}
BADGE_BG = {
    "OFFICIAL": (22, 101, 52),
    "CONFIRMED": (30, 64, 175),
    "REPORTED": (146, 64, 14),
    "CLAIM": (153, 27, 27),
}

N_STORIES = 37
REGION_COUNTS = [("Europe", 8), ("North America", 6), ("Latin America", 5),
                 ("Africa", 5), ("East & SE Asia", 5), ("Middle East", 4),
                 ("Oceania", 1), ("South Asia", 1), ("World", 2)]
FIELD_COUNTS = [("Law & justice", 1), ("Politics", 4), ("Markets & deals", 2),
                ("Economy & budgets", 5), ("Society & rights", 3), ("Diplomacy", 3),
                ("Sport", 3), ("Health", 3), ("Space & science", 2), ("Security", 4),
                ("War & defence", 4), ("Disaster", 1), ("Migration", 1),
                ("Accident", 1)]

BIG = [
    dict(n=1, region="North America", field="Law & justice", time="~20:20 UTC",
         src="Reuters, AP", badge="OFFICIAL", banner="10 OF 12", icon="court",
         head="Huawei convicted on 10 of 12 US counts",
         body="Brooklyn jury finds the company guilty of bank fraud, sanctions "
              "violations and trade-secret theft; cleared of racketeering; "
              "sentencing next September."),
    dict(n=2, region="Europe", field="Politics", time="19:15 UTC",
         src="Zelensky statement", badge="OFFICIAL", banner="\u20ac115BN", icon="euro",
         head="Zelensky: Ukraine needs \u20ac115bn in 2027",
         body="A European deal covers \u20ac90bn, leaving \u20ac25bn short; Kyiv will seek "
              "more US support if peace talks fail."),
    dict(n=3, region="Europe", field="Markets & deals", time="06:30 UTC",
         src="Sanofi release", badge="OFFICIAL", banner="$41BN", icon="pill",
         head="Sanofi buys Insmed for $41bn in cash",
         body="$175 a share, a 17% premium, for the maker of a lung-disease drug."),
]

MEDIUM = [
    dict(n=4, region="World", field="Society & rights", time="07:00 UTC",
         src="UNODC/UN Women", badge="OFFICIAL", banner="47,000", icon="people",
         head="UN: 47,000 women killed by family",
         body="5 every hour, 129 a day."),
    dict(n=5, region="Oceania", field="Diplomacy", time="~03:02 UTC",
         src="SMH, ABC", badge="REPORTED", banner="PACT ENDS", icon="flag",
         head="Solomons to end China security pact",
         body="Won't renew the 2022 deal."),
    dict(n=6, region="Africa", field="Sport", time="~14:00 UTC",
         src="CAS ruling", badge="OFFICIAL", banner="TITLE BACK", icon="trophy",
         head="Senegal regain Africa Cup title",
         body="CAS overturns CAF ruling."),
    dict(n=7, region="North America", field="Politics", time="22:56 UTC",
         src="NY Post", badge="REPORTED", banner="PARDON TALK", icon="gavel",
         head="Trump floats Huang pardon",
         body="\u201cAlways an option, I guess.\u201d"),
    dict(n=8, region="Africa", field="Health", time="13:32 UTC",
         src="UN News", badge="OFFICIAL", banner="PER 17 NOV", icon="cross",
         head="Ebola staff evacuated", lines=2,
         body="WHO staff sheltered 3+ days; 11,613 cases, 5,678 deaths."),
    dict(n=9, region="East & SE Asia", field="Space & science", time="01:16 UTC",
         src="CMSA", badge="OFFICIAL", banner="SHENZHOU-24", icon="rocket",
         head="China names Shenzhou-24 crew",
         body="First Pakistani to Tiangong."),
    dict(n=10, region="Middle East", field="Security", time="~14:00 UTC",
         src="Haaretz, ToI", badge="CLAIM", banner="IRAN CLAIM", icon="shield",
         head="Iran 'developing chemical arms'",
         body="Katz says so; Iran denies."),
    dict(n=11, region="Europe", field="Sport", time="~21:45 UTC",
         src="UEFA, Reuters", badge="CONFIRMED", banner="5-1", icon="ball",
         head="Real Madrid beat PSV 5-1",
         body="Came from 0-1 down; Mbapp\u00e9 x2."),
    dict(n=12, region="World", field="Space & science", time="~09:00 UTC",
         src="ESA", badge="OFFICIAL", banner="630M YRS", icon="star",
         head="Euclid spots most distant quasar",
         body="630m yrs after the Big Bang."),
    dict(n=13, region="Middle East", field="War & defence", time="~11:00 UTC",
         src="Reuters, ToI", badge="CONFIRMED", banner="HAMAS CHIEF", icon="blast",
         head="Gaza: Hamas security chief killed",
         body="7 killed; IDF, Shin Bet struck."),
]

# LIST: (n, place, region, sentence, src, time, tag) — tag: "" | "CLAIM" | "REPORTED"
LIST = [
    (14, "Indonesia", "East & SE Asia", "'ACAB' treason charge", "BBC", "00:10", ""),
    (15, "Nepal", "South Asia", "5.6 quake, no casualties", "NEMRC", "01:32", ""),
    (16, "Colombia", "Latin America", "car bomb injures 23", "AP", "~05:00", ""),
    (17, "Zaporizhzhia", "Europe", "strike kills 2, wounds 40", "Reuters", "05:35", ""),
    (18, "Malaysia", "East & SE Asia", "6,803 Myanmar nationals home", "AP", "~09:45", ""),
    (19, "S. Korea", "East & SE Asia", "Russian jets enter defence zone", "JCS", "~06:00", ""),
    (20, "Japan", "East & SE Asia", "2027 ICC dues paid early", "Reuters", "~06:00", ""),
    (21, "Yemen", "Middle East", "toll 25 dead or missing", "Saba", "~02:50", "CLAIM"),
    (22, "UAE", "Middle East", "bus-truck crash kills 13", "Interior", "~08:00", ""),
    (23, "US", "North America", "Hegseth yet to approve 60 Patriots", "FT", "08:39", ""),
    (24, "Hungary", "Europe", "new PM Magyar meets Zelensky", "Reuters", "11:40", ""),
    (25, "Mexico", "Latin America", "inflation 6-month high", "Reuters", "13:08", ""),
    (26, "UK", "Europe", "firms warned of Russian sabotage", "MI5", "13:17", ""),
    (27, "Congo", "Africa", "1.5m Ebola vaccine doses deal", "Gavi", "~14:00", ""),
    (28, "Cuba", "Latin America", "WHO chief pledges $2m for vaccines", "WHO", "14:52", ""),
    (29, "Wall St", "North America", "Dow gains 423, Nasdaq falls 1.5%", "AP", "~21:30", ""),
    (30, "Alaska", "North America", "Sullivan concedes Senate race", "Newsmax", "~19:00", ""),
    (31, "US", "North America", "Trump awards Giuliani", "Reuters", "~17:00", "REPORTED"),
    (32, "Venezuela", "Latin America", "govt puts debt at $237.5bn", "Reuters", "~14:43", ""),
    (33, "Argentina", "Latin America", "Sept economy shrinks 1.2%", "INDEC", "16:00", ""),
    (34, "Nigeria", "Africa", "Tinubu seeks budget cut", "Reuters", "09:32", ""),
    (35, "Dakar", "Africa", "~175 migrants missing", "Reuters", "14:20", "REPORTED"),
    (36, "EU", "Europe", "France's 2027 budget cleared", "Reuters", "~16:30", ""),
    (37, "UCL", "Europe", "Arsenal 1-1, Man City 2-2, Villa 0-1", "UEFA", "~21:50", ""),
]

UTC_POINTS = [("05:35", "Zaporizhzhia"), ("06:30", "Sanofi"),
              ("07:00", "UN report"), ("13:32", "Ebola"),
              ("19:15", "Zelensky"), ("~21:30", "Wall St split"),
              ("22:56", "Huang pardon")]

LEFT_OUT = ("CrowdStrike buys Zscaler (Mon 23) \u00b7 NATO sends AWACS to Poland (Mon 23) \u00b7 "
            "US sanctions Iranian shadow banks (Mon 23) \u00b7 Ukraine claims Russian warship "
            "sunk off Libya (Mon 23) \u00b7 COP31 collapses (Sun 22) \u00b7 Alcaraz wins ATP "
            "Finals (Sun 22).")
BACKGROUND = "Nvidia's reinstatement of Huang (Mon 23); Ebola totals as of 17 Nov."
NOT_YET = ("Australia\u2013Solomon Islands treaty signing (Wed 25 Nov); "
           "Huang's congressional testimony (next week).")

PINS = {1: (-74.0, 40.6), 2: (30.5, 50.4), 3: (2.35, 48.85), 4: (16.4, 48.2),
        5: (160.0, -9.4), 6: (-17.4, 14.7), 7: (-77.0, 38.9), 8: (30.0, 1.5),
        9: (100.3, 40.9), 10: (35.2, 31.8), 11: (-3.7, 40.4), 12: (8.65, 49.87),
        13: (34.5, 31.4)}
PIN_DXDY = {1: (0, -8), 7: (-10, 10), 3: (-14, -8), 11: (-16, 8), 2: (12, -10),
            10: (14, 8), 12: (0, -14), 4: (10, -8), 9: (0, 0), 6: (-14, 2),
            5: (0, 0), 8: (0, 0), 13: (-26, 12)}
LIST_DOTS = [(113.0, -2.0), (84.0, 28.0), (-74.0, 4.6), (35.2, 47.8),
             (101.7, 3.1), (127.0, 37.5), (139.7, 35.7), (44.4, 15.3),
             (55.3, 25.2), (-77.0, 38.9), (19.0, 47.5),
             (-99.1, 19.4), (-0.1, 51.5), (25.0, -2.0), (-82.4, 23.1),
             (-74.0, 40.7), (-152.0, 64.0), (-80.0, 39.0), (-66.9, 6.4),
             (-63.6, -38.4), (8.0, 9.0), (-16.0, 13.0), (4.35, 50.85),
             (1.0, 50.0)]
LIST_DOT_REGIONS = ["East & SE Asia", "South Asia", "Latin America", "Europe",
                    "East & SE Asia", "East & SE Asia", "East & SE Asia",
                    "Middle East", "Middle East", "North America", "Europe",
                    "Latin America", "Europe", "Africa", "Latin America",
                    "North America", "North America", "North America",
                    "Latin America", "Latin America", "Africa", "Africa",
                    "Europe", "Europe"]


def px(v):
    return int(round(v * S))


def wrap(draw, text, fnt, max_w):
    words = text.split()
    lines, cur = [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if draw.textlength(trial, font=fnt) <= px(max_w):
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


img = Image.new("RGB", (CW, CH), PAPER)
d = ImageDraw.Draw(img)
M, G = 12, 8
CWID = W - 2 * M

# ================= top strip (11px floor) =================
y = 12
f_strip = font(SANS_B, 11)
left_t = "THE WORLD IN ONE DAY \u00b7 ONE PAGE"
right_t = "37 STORIES \u00b7 9 REGIONS \u00b7 14 FIELDS \u00b7 ALL FROM TUESDAY 24 NOVEMBER 2026"
d.text((px(M), px(y)), left_t, font=f_strip, fill=INK)
rw = d.textlength(right_t, font=f_strip)
d.text((px(W - M) - rw, px(y)), right_t, font=f_strip, fill=INK)
d.line([(px(M), px(y + 16)), (px(W - M), px(y + 16))], fill=INK, width=px(1.5))

# ================= date (largest text, 56px) =================
y = 32
f_date = font(SERIF_B, 56)
date_t = "Tuesday 24 November 2026"
dw = d.textlength(date_t, font=f_date)
d.text((px(W / 2) - dw / 2, px(y)), date_t, font=f_date, fill=INK)

# ================= TODAY summary line (max 2 lines, 14px sans) =================
TODAY_TEXT = ("a US jury convicted Huawei on 10 of 12 counts \u00b7 Zelensky said Ukraine needs "
              "\u20ac115bn in 2027 \u00b7 Sanofi agreed to buy Insmed for $41bn \u00b7 Dow gained 423 "
              "as Nasdaq fell 1.5% \u00b7 Senegal regained the Africa Cup title")
TODAY_TEXT_4 = ("a US jury convicted Huawei on 10 of 12 counts \u00b7 Zelensky said Ukraine needs "
                "\u20ac115bn in 2027 \u00b7 Sanofi agreed to buy Insmed for $41bn \u00b7 Dow gained "
                "423 as Nasdaq fell 1.5%")
y = 92
f_today_b = font(SANS_B, 15)
f_today = font(SANS_R, 15)
tag = "TODAY: "
tag_w = d.textlength(tag, font=f_today_b) / S
tlines = wrap(d, TODAY_TEXT, f_today, CWID - tag_w)
if len(tlines) > 2:
    tlines = wrap(d, TODAY_TEXT_4, f_today, CWID - tag_w)
assert len(tlines) <= 2, f"TODAY line too long: {len(tlines)} lines"
d.text((px(M), px(y)), tag, font=f_today_b, fill=INK)
d.text((px(M + tag_w), px(y)), tlines[0], font=f_today, fill=INK)
if len(tlines) > 1:
    d.text((px(M), px(y + 16)), tlines[1], font=f_today, fill=INK)

# ================= region chips row (11px) =================
y = 128
f_chip = font(SANS_B, 11)
chip_x = M
for name, cnt in REGION_COUNTS:
    label = f"{name.upper()} {cnt}"
    tw = d.textlength(label, font=f_chip) / S
    cw = tw + 12
    d.rounded_rectangle([px(chip_x), px(y), px(chip_x + cw), px(y + 16)],
                        radius=px(3), fill=REGION[name])
    d.text((px(chip_x + 6), px(y + 2.5)), label, font=f_chip, fill=(255, 255, 255))
    chip_x += cw + 6
assert chip_x <= W - M, f"chips overflow: {chip_x:.0f}px"

# ================= UTC strip (11px) =================
y = 148
f_utc_lab = font(SANS_B, 11)
f_utc = font(SANS_R, 11)
d.rectangle([px(M), px(y), px(W - M), px(y + 26)], fill=BAND_BG)
d.text((px(M + 8), px(y + 7)), "THE DAY IN UTC", font=f_utc_lab, fill=MUTED)
x0 = M + 128
span = CWID - 128 - 6
for i, (t, lab) in enumerate(UTC_POINTS):
    cx = x0 + span * (i + 0.5) / len(UTC_POINTS)
    s = t + "  " + lab
    w = d.textlength(s, font=f_utc)
    assert w <= px(span / len(UTC_POINTS)), f"UTC strip item too wide: {s}"
    d.text((px(cx) - w / 2, px(y + 7)), s, font=f_utc, fill=INK)


# ================= icons (flat white shapes) =================
def draw_icon(kind, box, colour):
    x0, y0, x1, y1 = [px(v) for v in box]
    w = max(2, px(2))
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    r = min(x1 - x0, y1 - y0) / 2
    if kind == "court":
        d.polygon([(x0, cy), (x1, cy), (cx, y0)], outline=colour, width=w)
        for i in range(3):
            colx = x0 + (x1 - x0) * (0.2 + 0.3 * i)
            d.line([(colx, cy + px(2)), (colx, y1 - px(3))], fill=colour, width=w)
        d.line([(x0, y1 - px(2)), (x1, y1 - px(2))], fill=colour, width=w)
    elif kind == "euro":
        d.text((px(box[0]) - px(4), px(box[1]) - px(6)), "\u20ac",
               font=font(SERIF_B, (box[3] - box[1]) * 0.9), fill=colour)
    elif kind == "pill":
        d.rounded_rectangle([x0, cy - r * 0.45, x1, cy + r * 0.45], radius=r * 0.45,
                            outline=colour, width=w)
        d.line([(cx - r * 0.3, cy - r * 0.45), (cx + r * 0.3, cy + r * 0.45)],
               fill=colour, width=w)
    elif kind == "ball":
        d.ellipse([x0, y0, x1, y1], outline=colour, width=w)
        d.polygon([(cx, cy - r * 0.45), (cx + r * 0.43, cy - r * 0.14),
                   (cx + r * 0.27, cy + r * 0.36), (cx - r * 0.27, cy + r * 0.36),
                   (cx - r * 0.43, cy - r * 0.14)], outline=colour, width=w)
    elif kind == "gavel":
        d.line([(x0 + px(3), y0 + px(6)), (x1 - px(3), y1 - px(10))], fill=colour, width=w)
        d.rectangle([x0 + px(2), y0 + px(2), x0 + px(14), y0 + px(10)], fill=colour)
        d.line([(x0 + px(4), y1 - px(3)), (x1 - px(4), y1 - px(3))], fill=colour, width=w)
    elif kind == "cross":
        d.rectangle([cx - px(4), y0 + px(2), cx + px(4), y1 - px(2)], fill=colour)
        d.rectangle([x0 + px(2), cy - px(4), x1 - px(2), cy + px(4)], fill=colour)
    elif kind == "rocket":
        d.polygon([(cx, y0), (cx + r * 0.5, cy), (cx, y1 - px(4)), (cx - r * 0.5, cy)],
                  outline=colour, width=w)
        d.line([(cx, y1 - px(4)), (cx, y1)], fill=colour, width=w)
    elif kind == "star":
        pts = []
        for i in range(10):
            ang = -math.pi / 2 + i * math.pi / 5
            rr = r if i % 2 == 0 else r * 0.45
            pts.append((cx + rr * math.cos(ang), cy + rr * math.sin(ang)))
        d.polygon(pts, outline=colour, width=w)
    elif kind == "people":
        d.ellipse([cx - r * 0.85, y0 + r * 0.1, cx - r * 0.15, y0 + r * 0.8],
                  fill=colour)
        d.ellipse([cx + r * 0.15, y0 + r * 0.3, cx + r * 0.85, y0 + r * 1.0],
                  fill=colour)
        d.chord([x0 + px(2), cy, x1 - px(2), y1 - px(1)], 180, 360, fill=colour)
    elif kind == "flag":
        d.line([(x0 + px(5), y0 + px(2)), (x0 + px(5), y1 - px(2))],
               fill=colour, width=w)
        d.polygon([(x0 + px(5), y0 + px(2)), (x1 - px(2), y0 + px(7)),
                   (x0 + px(5), y0 + px(12))], fill=colour)
    elif kind == "trophy":
        d.chord([x0 + px(4), y0 + px(2), x1 - px(4), y0 + px(16)], 0, 180,
                fill=colour)
        d.line([(cx, y0 + px(14)), (cx, y1 - px(5))], fill=colour, width=w)
        d.line([(x0 + px(4), y1 - px(3)), (x1 - px(4), y1 - px(3))],
               fill=colour, width=w)
    elif kind == "shield":
        d.polygon([(x0 + px(4), y0 + px(2)), (x1 - px(4), y0 + px(2)),
                   (x1 - px(4), cy), (cx, y1 - px(2)), (x0 + px(4), cy)],
                  outline=colour, width=w)
    elif kind == "blast":
        for k in range(8):
            ang = k * math.pi / 4
            x_a = cx + r * 0.35 * math.cos(ang)
            y_a = cy + r * 0.35 * math.sin(ang)
            x_b = cx + r * math.cos(ang)
            y_b = cy + r * math.sin(ang)
            d.line([(x_a, y_a), (x_b, y_b)], fill=colour, width=w)
        d.ellipse([cx - r * 0.3, cy - r * 0.3, cx + r * 0.3, cy + r * 0.3],
                  fill=colour)


def badge(x, y, label):
    f = font(SANS_B, 11)
    tw = d.textlength(label, font=f)
    pad = 5
    w = tw + px(pad * 2)
    d.rounded_rectangle([px(x), px(y), px(x) + w, px(y + 15)],
                        radius=px(2), fill=BADGE_BG[label])
    d.text((px(x + pad), px(y + 2)), label, font=f, fill=(255, 255, 255))
    return w / S


def draw_card(x, y, w, h, banner_h, c, f_head, head_lh, f_body, body_lh,
              f_src, icon=None, banner_font=None, short_tag=False,
              max_body_lines=2):
    """Card with top-anchored headline and bottom-anchored body + source line.
    Asserts headline bottom stays above body top (no overlap)."""
    col = REGION[c["region"]]
    d.rounded_rectangle([px(x), px(y), px(x + w), px(y + h)],
                        radius=px(3), outline=LINE, width=px(1))
    d.rectangle([px(x + 1), px(y + 1), px(x + w - 1), px(y + banner_h)], fill=col)
    lab = c["banner"]
    if icon is not None:
        side = banner_h - 12
        draw_icon(icon, (x + w - 6 - side, y + 6, x + w - 6, y + 6 + side),
                  (255, 255, 255))
        lab_h = banner_font.size / S
        d.text((px(x + 12), px(y + banner_h / 2 - lab_h / 2)), lab,
               font=banner_font, fill=(255, 255, 255))
    else:
        lw = d.textlength(lab, font=banner_font)
        d.text((px(x + w / 2) - lw / 2, px(y + 9)), lab, font=banner_font,
               fill=(255, 255, 255))
    f_tag = font(SANS_B, 11)
    ty = y + banner_h + 6
    d.text((px(x + 10), px(ty)), str(c["n"]), font=f_tag, fill=col)
    tag_txt = c["region"].upper() if short_tag else \
        c["region"].upper() + " \u00b7 " + c["field"].upper()
    d.text((px(x + 26), px(ty)), tag_txt, font=f_tag, fill=MUTED)
    badge(x + w - 70, ty - 1, c["badge"])
    hy = ty + 16
    lines = wrap(d, c["head"], f_head, w - 20)
    assert len(lines) <= 2, f"headline too long: {c['head']}"
    for ln in lines:
        d.text((px(x + 10), px(hy)), ln, font=f_head, fill=INK)
        hy += head_lh
    head_bottom = hy
    src_y = y + h - 16
    src_txt = c["src"] + "  \u00b7  " + c["time"]
    src_w = d.textlength(src_txt, font=f_src)
    assert src_w <= px(w - 20), \
        f"source line too wide in card {c['n']}: {src_w / S:.0f}px > {w - 20:.0f}px"
    d.text((px(x + 10), px(src_y)), src_txt, font=f_src, fill=MUTED)
    full_blines = wrap(d, c["body"], f_body, w - 20)
    if len(full_blines) > max_body_lines:
        print(f"WARNING body truncated card {c['n']}: {len(full_blines)} lines > {max_body_lines}")
    blines = full_blines[:max_body_lines]
    body_top = src_y - 5 - len(blines) * body_lh
    assert head_bottom <= body_top + 2, \
        f"headline/body overlap in card {c['n']}: head_bottom={head_bottom:.0f} body_top={body_top:.0f}"
    by = body_top
    for ln in blines:
        d.text((px(x + 10), px(by)), ln, font=f_body, fill=INK)
        by += body_lh


# ================= big cards =================
BIG_Y, BIG_H, BIG_BANNER = 180, 220, 85
bw = (CWID - 2 * G) / 3
f_big_head = font(SERIF_B, 25)
f_big_body = font(SANS_R, 11)
f_src = font(SANS_R, 11)
f_banner_big = font(SANS_B, 30)
for i, c in enumerate(BIG):
    x = M + i * (bw + G)
    draw_card(x, BIG_Y, bw, BIG_H, BIG_BANNER, c, f_big_head, 26,
              f_big_body, 13, f_src, icon=c["icon"], banner_font=f_banner_big,
              max_body_lines=3)

# ================= medium cards =================
MED_Y = BIG_Y + BIG_H + G
MED_H, MED_BANNER = 132, 36
mw = (CWID - 4 * G) / 5
f_med_head = font(SERIF_B, 17)
f_med_body = font(SANS_R, 11)
f_banner_med = font(SANS_B, 19)
for i, c in enumerate(MEDIUM):
    row, col_i = divmod(i, 5)
    x = M + col_i * (mw + G)
    y = MED_Y + row * (MED_H + G)
    draw_card(x, y, mw, MED_H, MED_BANNER, c, f_med_head, 21,
              f_med_body, 13, f_src, icon=c["icon"], banner_font=f_banner_med,
              short_tag=True, max_body_lines=c.get("lines", 1))


# ================= list (3 columns x 8 rows) =================
LIST_Y = MED_Y + 2 * MED_H + G + G + 2  # +2px breathing room above list
f_list_head = font(SANS_B, 11)
f_list = font(SANS_R, 11)
f_list_b = font(SANS_B, 11)
d.text((px(M), px(LIST_Y)), "THE REST OF THE DAY", font=f_list_head, fill=INK)
d.line([(px(M), px(LIST_Y + 16)), (px(W - M), px(LIST_Y + 16))], fill=LINE, width=px(1))
list_col_w = (CWID - 2 * G) / 3
ly = LIST_Y + 22
row_h = 12.5
for i, (n, place, region, sent, src, t, tag) in enumerate(LIST):
    col_i, row_i = divmod(i, 8)
    x = M + col_i * (list_col_w + G)
    y = ly + row_i * row_h
    col = REGION[region]
    pre = f"{n} {place}: "
    d.text((px(x), px(y)), pre, font=f_list_b, fill=col)
    pre_w = d.textlength(pre, font=f_list_b) / S
    rest = sent + " \u2014 " + src + ", " + t
    if tag:
        rest += f" [{tag}]"
    d.text((px(x + pre_w), px(y)), rest, font=f_list, fill=INK)
    total_w = d.textlength(pre, font=f_list_b) + d.textlength(rest, font=f_list)
    if total_w > px(list_col_w):
        print(f"OVERFLOW list {n}: {total_w / S:.0f}px > {list_col_w:.0f}px")

# ================= bottom band: map + fields legend =================
MAP_Y = LIST_Y + 22 + 8 * row_h + 12  # +2px breathing room above map band
MAP_H = 80
map_x0, map_y0 = M, MAP_Y
map_w, map_h = 500, MAP_H
leg_x = M + map_w + 16
leg_w = W - M - leg_x
d.text((px(M), px(MAP_Y - 2)), "WHERE IT HAPPENED", font=f_list_head, fill=INK)
land = (208, 213, 219)
outline = (156, 163, 175)


def mxy(lon, lat):
    return (map_x0 + (lon + 180) / 360 * map_w,
            map_y0 + (90 - lat) / 150 * map_h)


def poly_ll(pts):
    d.polygon([(px(x), px(y)) for x, y in (mxy(lo, la) for lo, la in pts)],
              fill=land, outline=outline)


poly_ll([(-168, 66), (-140, 70), (-120, 71), (-95, 68), (-80, 62), (-75, 45),
         (-80, 32), (-90, 21), (-97, 26), (-105, 30), (-117, 33), (-125, 40),
         (-130, 55), (-155, 58), (-168, 66)])
poly_ll([(-80, 10), (-60, 8), (-50, 0), (-40, -8), (-35, -20), (-48, -28),
         (-58, -38), (-70, -52), (-73, -40), (-70, -18), (-80, 0), (-80, 10)])
poly_ll([(-10, 36), (-9, 43), (-2, 48), (0, 51), (8, 57), (18, 56), (28, 60),
         (30, 70), (40, 68), (45, 60), (40, 50), (28, 45), (22, 40), (12, 44),
         (3, 43), (-10, 36)])
poly_ll([(-17, 15), (-10, 30), (0, 36), (10, 37), (20, 32), (32, 31), (35, 28),
         (43, 12), (51, 11), (48, 0), (40, -12), (35, -26), (28, -33), (18, -35),
         (12, -18), (9, 0), (-8, 4), (-17, 15)])
poly_ll([(40, 68), (60, 70), (80, 73), (110, 74), (140, 72), (160, 70),
         (178, 66), (162, 60), (140, 40), (127, 35), (120, 30), (105, 10),
         (100, 8), (90, 22), (80, 8), (70, 20), (60, 25), (50, 29), (40, 60),
         (40, 68)])
poly_ll([(114, -22), (124, -15), (132, -12), (142, -11), (150, -22), (153, -27),
         (146, -39), (140, -38), (130, -32), (115, -35), (114, -22)])

for (lo, la), reg in zip(LIST_DOTS, LIST_DOT_REGIONS):
    cx, cy = mxy(lo, la)
    r = px(2.5)
    d.ellipse([px(cx) - r, px(cy) - r, px(cx) + r, px(cy) + r], fill=REGION[reg])
f_pin = font(SANS_B, 11)
for n, (lo, la) in PINS.items():
    cx, cy = mxy(lo, la)
    dx, dy = PIN_DXDY.get(n, (0, 0))
    cx, cy = cx + dx, cy + dy
    reg = (BIG + MEDIUM)[n - 1]["region"]
    col = REGION[reg]
    r = px(8)
    d.ellipse([px(cx) - r, px(cy) - r, px(cx) + r, px(cy) + r], fill=col,
              outline=(255, 255, 255), width=px(1))
    tw = d.textlength(str(n), font=f_pin)
    d.text((px(cx) - tw / 2, px(cy - 5.5)), str(n), font=f_pin, fill=(255, 255, 255))

d.text((px(leg_x), px(MAP_Y - 2)), "FIELDS (14)", font=f_list_head, fill=INK)
f_leg = font(SANS_R, 11)
fyy = MAP_Y + 16
fields_txt = " \u00b7 ".join(f"{n} {c}" for n, c in FIELD_COUNTS)
flines = wrap(d, fields_txt, f_leg, leg_w)
for ln in flines:
    d.text((px(leg_x), px(fyy)), ln, font=f_leg, fill=INK)
    fyy += 13
assert fyy <= MAP_Y + MAP_H + 2, f"fields legend overflows map band: {fyy:.0f}"


# ================= date check =================
DC_Y = MAP_Y + MAP_H + 8
DC_H = 76
f_dc_head = font(SANS_B, 11)
f_dc = font(SANS_R, 11)
d.rectangle([px(M), px(DC_Y), px(W - M), px(DC_Y + DC_H)], fill=BAND_BG)
d.text((px(M + 8), px(DC_Y + 5)), "DATE CHECK", font=f_dc_head, fill=INK)
lines = [
    "Every story on this page happened or was first reported on Tuesday "
    "24 November 2026, in any time zone (times in UTC).",
    "Left out, before Tuesday: " + LEFT_OUT,
    "Shown only as background: " + BACKGROUND,
    "Not yet: " + NOT_YET,
]
yy = DC_Y + 16
for ln in lines:
    wl = wrap(d, ln, f_dc, CWID - 16)
    for part in wl:
        d.text((px(M + 8), px(yy)), part, font=f_dc, fill=INK)
        yy += 11.5
assert yy <= DC_Y + DC_H - 2, f"date check overflows box: yy={yy:.0f} box bottom={DC_Y + DC_H}"

# ================= footer =================
F_Y = DC_Y + DC_H + 5
f_foot = font(SANS_R, 11)
foot = ("Badges: CONFIRMED 2+ outlets \u00b7 OFFICIAL authority's own word \u00b7 "
        "REPORTED not independently confirmed \u00b7 CLAIM one side says.  Sources: Reuters, AP, BBC, UN, "
        "WHO, ESA, CMSA, CAS, NY Post, FT.  Scenes are drawn illustrations, not photographs.")
fl = wrap(d, foot, f_foot, CWID)
for ln in fl:
    d.text((px(M), px(F_Y)), ln, font=f_foot, fill=MUTED)
    F_Y += 12

# ================= section separators (hairlines in existing gaps) =================
# Thin clean rules between the major sections: header/TODAY -> cards -> list ->
# map + FIELDS -> DATE CHECK. Drawn in the existing inter-section gaps; no
# content was moved for these, so pins, counts and data are untouched.
for hy in (174 + 3, BIG_Y + BIG_H + 4, LIST_Y - 5, MAP_Y - 7, MAP_Y + MAP_H + 4):
    d.line([(px(M), px(hy)), (px(W - M), px(hy))], fill=LINE, width=px(1))

# ================= save =================
out = img.resize((W, H), Image.LANCZOS)
out.save("entry.png", optimize=True)
data = open("entry.png", "rb").read()
print(f"entry.png: {len(data)} bytes, sha256={hashlib.sha256(data).hexdigest()}")
print(f"footer ends ~{F_Y:.0f}px of 1024")

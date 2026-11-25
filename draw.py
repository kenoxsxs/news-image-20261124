#!/usr/bin/env python3
"""draw.py — renders entry.png for news-image-20261124 (Tue 24 Nov 2026).
Draws OFFLINE at 3x (3072x3072) with PIL + Liberation fonts, downsamples to 1024x1024.
Written from scratch for this entry. Data: 28 verified stories (see verification-table.md).
Layout v3 (improvement pass): TODAY summary line under the date, icons on all
medium-card banners, Gaza promoted to 10th medium card, list renumbered 14-28.
Vertical room made by trimming UTC strip, big-card height, list rows, map and
date-check box — no headline or list text shrunk.
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
    "Asia-Pacific": (22, 101, 52),
    "Middle East": (146, 64, 14),
    "Americas": (153, 27, 27),
    "Africa": (107, 33, 168),
    "Global": (71, 85, 105),
}
BADGE_BG = {
    "OFFICIAL": (22, 101, 52),
    "CONFIRMED": (30, 64, 175),
    "REPORTED": (146, 64, 14),
    "CLAIM": (153, 27, 27),
}

N_STORIES = 28
REGION_COUNTS = [("Europe", 6), ("Asia-Pacific", 7), ("Middle East", 4),
                 ("Americas", 6), ("Africa", 3), ("Global", 2)]
FIELD_COUNTS = [("Law & justice", 1), ("Politics", 2), ("Business & economy", 2),
                ("Society & rights", 3), ("Diplomacy", 3), ("Sport", 2),
                ("Health", 3), ("Space & science", 2), ("Security", 4),
                ("War & defence", 4), ("Disaster", 1), ("Accident", 1)]

BIG = [
    dict(n=1, region="Americas", field="Law & justice", time="~20:20 UTC",
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
    dict(n=3, region="Europe", field="Business & economy", time="06:30 UTC",
         src="Sanofi release", badge="OFFICIAL", banner="$41BN", icon="pill",
         head="Sanofi buys Insmed for $41bn in cash",
         body="$175 a share, a 17% premium, for the maker of a lung-disease drug."),
]

MEDIUM = [
    dict(n=4, region="Global", field="Society & rights", time="07:00 UTC",
         src="UNODC + UN Women", badge="OFFICIAL", banner="47,000", icon="people",
         head="UN: 47,000 women killed by family",
         body="Killed by a partner or relative in 2025; 5 every hour, 129 a day."),
    dict(n=5, region="Asia-Pacific", field="Diplomacy", time="~03:02 UTC",
         src="SMH, ABC", badge="REPORTED", banner="PACT ENDS", icon="flag",
         head="Solomons to end China security pact",
         body="Won't renew the 2022 deal; Australia treaty expected Wednesday."),
    dict(n=6, region="Africa", field="Sport", time="~14:00 UTC",
         src="CAS ruling", badge="OFFICIAL", banner="TITLE BACK", icon="trophy",
         head="Senegal regain Africa Cup title",
         body="CAS overturns CAF ruling; Senegal's 1-0 final win stands."),
    dict(n=7, region="Americas", field="Politics", time="22:56 UTC",
         src="NY Post", badge="REPORTED", banner="PARDON TALK", icon="gavel",
         head="Trump floats Huang pardon",
         body="\u201cAlways an option, I guess, but I don't think it'll be necessary.\u201d"),
    dict(n=8, region="Africa", field="Health", time="13:32 UTC",
         src="UN News", badge="OFFICIAL", banner="3 DAYS", icon="cross",
         head="WHO evacuates Ebola staff in Ituri",
         body="Sheltered 3+ days amid fighting; 11,613 cases, 5,678 deaths."),
    dict(n=9, region="Asia-Pacific", field="Space & science", time="01:16 UTC",
         src="CMSA", badge="OFFICIAL", banner="SHENZHOU-24", icon="rocket",
         head="China names Shenzhou-24 crew",
         body="Includes a Pakistani astronaut, the first to visit Tiangong."),
    dict(n=10, region="Middle East", field="Security", time="~14:00 UTC",
         src="Haaretz, Times of Israel", badge="CLAIM", banner="IRAN CLAIM", icon="shield",
         head="Iran 'developing chemical arms'",
         body="Defence Minister Katz says so; Iran denies; unconfirmed."),
    dict(n=11, region="Europe", field="Sport", time="~21:45 UTC",
         src="UEFA, Reuters", badge="CONFIRMED", banner="5-1", icon="ball",
         head="Real Madrid beat PSV 5-1",
         body="Champions League; came from 0-1 down; Mbapp\u00e9 scored twice."),
    dict(n=12, region="Global", field="Space & science", time="~09:00 UTC",
         src="ESA", badge="OFFICIAL", banner="630M YRS", icon="star",
         head="Euclid spots most distant quasar",
         body="630m years after the Big Bang; a new Euclid record."),
    dict(n=13, region="Middle East", field="War & defence", time="~11:00 UTC",
         src="Reuters", badge="CONFIRMED", banner="HAMAS CHIEF", icon="blast",
         head="Gaza: Hamas security chief killed",
         body="Medics: 7 killed; IDF, Shin Bet struck a senior Hamas militant."),
]

LIST = [
    (14, "Indonesia", "Asia-Pacific", "civilian charged with treason over 'ACAB' shirt", "BBC Indonesia", "00:10", False),
    (15, "Nepal", "Asia-Pacific", "5.6 quake near Tibet border, no casualties", "NEMRC, EMSC", "01:32", False),
    (16, "Colombia", "Americas", "car bomb injures 23; president blames FARC dissidents", "AP", "~05:00", False),
    (17, "Zaporizhzhia", "Europe", "Russian strike kills 2, wounds 40", "Gov. Semikin", "05:35", False),
    (18, "Malaysia", "Asia-Pacific", "to send 6,803 Myanmar nationals home", "AP", "~09:45", False),
    (19, "South Korea", "Asia-Pacific", "Russian aircraft enter air defence zone", "Joint Chiefs", "~06:00", False),
    (20, "Japan", "Asia-Pacific", "to pay 2027 ICC dues early as US sanctions loom", "Reuters", "~06:00", False),
    (21, "Yemen", "Middle East", "Houthi media say Saudi strike toll hits 25 dead or missing", "Saba", "~02:50", True),
    (22, "UAE", "Middle East", "bus-truck crash kills 13 in Ras Al Khaimah", "Interior Ministry", "~08:00", False),
    (23, "US", "Americas", "Hegseth yet to approve 60 Patriot interceptors for Ukraine", "FT, Reuters", "08:39", False),
    (24, "Hungary", "Europe", "PM Magyar visits Ukraine, meets Zelensky", "Reuters", "11:40", False),
    (25, "Mexico", "Americas", "inflation hits six-month high, core eases", "Reuters", "13:08", False),
    (26, "UK", "Europe", "firms warned of Russian sabotage threat", "UK MoD, MI5", "13:17", False),
    (27, "Congo", "Africa", "Gavi to buy 1.5m Ebola vaccine doses", "Gavi, Reuters", "~14:00", False),
    (28, "Cuba", "Americas", "WHO chief pledges $2m for vaccination drive", "WHO", "14:52", False),
]

UTC_POINTS = [("05:35", "Zaporizhzhia strike"), ("06:30", "Sanofi"),
              ("07:00", "UN femicide report"), ("13:32", "Ebola evacuation"),
              ("19:15", "Zelensky"), ("~20:20", "Huawei")]

LEFT_OUT = ("CrowdStrike\u2013Zscaler $43.9bn (Mon 23) \u00b7 NATO AWACS to Poland (Mon 23) \u00b7 "
            "Rutte on space defence (Mon 23) \u00b7 US sanctions on Iranian shadow banking (Mon 23) \u00b7 "
            "Merkury corvette claim (sunk Sun 22, claimed Mon 23) \u00b7 FIFA 2031/2035 Women's "
            "World Cup hosts (Mon 23) \u00b7 COP31 collapses (Sun 22) \u00b7 Alcaraz wins ATP Finals (Sun 22).")
BACKGROUND = "Nvidia's reinstatement of Huang (Mon 23); Ebola totals as of 17 Nov."
NOT_YET = ("Australia\u2013Solomon Islands treaty signing (Wed 25 Nov); "
           "Huang's congressional testimony (next week).")

PINS = {1: (-74.0, 40.6), 2: (30.5, 50.4), 3: (2.35, 48.85), 4: (16.4, 48.2),
        5: (160.0, -9.4), 6: (-17.4, 14.7), 7: (-77.0, 38.9), 8: (30.0, 1.5),
        9: (100.3, 40.9), 10: (35.2, 31.8), 11: (-3.7, 40.4), 12: (8.65, 49.87),
        13: (34.5, 31.4)}
# manual offsets (final px) to separate the Europe / US-East clusters
PIN_DXDY = {1: (0, -8), 7: (-10, 10), 3: (-14, -8), 11: (-16, 8), 2: (12, -10),
            10: (14, 8), 12: (0, -14), 4: (10, -8), 9: (0, 0), 6: (-10, 12),
            5: (0, 0), 8: (0, 0), 13: (-22, 10)}
LIST_DOTS = [(113.0, -2.0), (84.0, 28.0), (-74.0, 4.6), (35.2, 47.8),
             (101.7, 3.1), (127.0, 37.5), (139.7, 35.7), (44.4, 15.3),
             (55.3, 25.2), (-77.0, 38.9), (19.0, 47.5),
             (-99.1, 19.4), (-0.1, 51.5), (25.0, -2.0), (-82.4, 23.1)]
LIST_DOT_REGIONS = ["Asia-Pacific", "Asia-Pacific", "Americas", "Europe",
                    "Asia-Pacific", "Asia-Pacific", "Asia-Pacific", "Middle East",
                    "Middle East", "Americas", "Europe",
                    "Americas", "Europe", "Africa", "Americas"]


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

# ================= top strip =================
y = M
f_strip = font(SANS_B, 10)
left_t = "THE WORLD IN ONE DAY \u00b7 ONE PAGE"
right_t = "28 STORIES \u00b7 6 REGIONS \u00b7 12 FIELDS \u00b7 ALL FROM TUESDAY 24 NOVEMBER 2026"
d.text((px(M), px(y)), left_t, font=f_strip, fill=INK)
rw = d.textlength(right_t, font=f_strip)
d.text((px(W - M) - rw, px(y)), right_t, font=f_strip, fill=INK)
d.line([(px(M), px(y + 15)), (px(W - M), px(y + 15))], fill=INK, width=px(1.5))

# ================= date (largest text) =================
y = 32
f_date = font(SERIF_B, 54)
date_t = "Tuesday 24 November 2026"
dw = d.textlength(date_t, font=f_date)
d.text((px(W / 2) - dw / 2, px(y)), date_t, font=f_date, fill=INK)

# ================= TODAY summary line (max 2 lines, 14px sans) =================
TODAY_TEXT = ("a US jury convicted Huawei on 10 of 12 counts \u00b7 Zelensky said Ukraine needs "
              "\u20ac115bn in 2027 \u00b7 Sanofi agreed to buy Insmed for $41bn \u00b7 Senegal regained "
              "the Africa Cup title \u00b7 WHO evacuated Ebola staff in Ituri")
TODAY_TEXT_4 = ("a US jury convicted Huawei on 10 of 12 counts \u00b7 Zelensky said Ukraine needs "
                "\u20ac115bn in 2027 \u00b7 Sanofi agreed to buy Insmed for $41bn \u00b7 Senegal regained "
                "the Africa Cup title")
y = 88
f_today_b = font(SANS_B, 14)
f_today = font(SANS_R, 14)
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

# ================= UTC strip (slot-centred points) =================
y = 122
f_utc_lab = font(SANS_B, 9)
f_utc = font(SANS_R, 10.5)
d.rectangle([px(M), px(y), px(W - M), px(y + 24)], fill=BAND_BG)
d.text((px(M + 8), px(y + 7)), "THE DAY IN UTC", font=f_utc_lab, fill=MUTED)
x0 = M + 128
span = CWID - 128 - 6
for i, (t, lab) in enumerate(UTC_POINTS):
    cx = x0 + span * (i + 0.5) / 6
    s = t + "  " + lab
    w = d.textlength(s, font=f_utc)
    d.text((px(cx) - w / 2, px(y + 7)), s, font=f_utc, fill=INK)

# ================= icons =================
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
    elif kind == "candle":
        d.line([(cx, y0 + px(4)), (cx, y1 - px(6))], fill=colour, width=w)
        d.ellipse([cx - px(3), y0, cx + px(3), y0 + px(7)], fill=colour)
        d.line([(x0 + px(4), y1 - px(2)), (x1 - px(4), y1 - px(2))], fill=colour, width=w)
    elif kind == "island":
        d.arc([x0, y0, x1, y1], 180, 360, fill=colour, width=w)
        d.line([(cx, y0 + px(2)), (cx, cy)], fill=colour, width=w)
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
    elif kind == "flask":
        d.line([(cx - px(3), y0), (cx + px(3), y0)], fill=colour, width=w)
        d.line([(cx - px(3), y0), (cx - px(8), y1 - px(4))], fill=colour, width=w)
        d.line([(cx + px(3), y0), (cx + px(8), y1 - px(4))], fill=colour, width=w)
        d.line([(cx - px(8), y1 - px(4)), (cx + px(8), y1 - px(4))], fill=colour, width=w)
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
    f = font(SANS_B, 8.5)
    tw = d.textlength(label, font=f)
    pad = 5
    d.rounded_rectangle([px(x), px(y), px(x) + tw + px(pad * 2), px(y) + px(13)],
                        radius=px(2), fill=BADGE_BG[label])
    d.text((px(x + pad), px(y + 1.5)), label, font=f, fill=(255, 255, 255))


def draw_card(x, y, w, h, banner_h, c, f_head, head_lh, f_body, body_lh,
              f_src, icon=None, banner_font=None, short_tag=False,
              max_body_lines=2):
    """Card with top-anchored headline and bottom-anchored body + source line.
    Asserts headline bottom stays above body top (no overlap)."""
    col = REGION[c["region"]]
    d.rounded_rectangle([px(x), px(y), px(x + w), px(y + h)],
                        radius=px(3), outline=LINE, width=px(1))
    d.rectangle([px(x + 1), px(y + 1), px(x + w - 1), px(y + banner_h)], fill=col)
    # banner label
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
    # tag row
    f_tag = font(SANS_B, 9)
    ty = y + banner_h + 6
    d.text((px(x + 10), px(ty)), str(c["n"]), font=f_tag, fill=col)
    tag_txt = c["region"].upper() if short_tag else \
        c["region"].upper() + " \u00b7 " + c["field"].upper()
    d.text((px(x + 26), px(ty)), tag_txt, font=f_tag, fill=MUTED)
    badge(x + w - 62, ty, c["badge"])
    # headline (top-anchored, max 2 lines)
    hy = ty + 15
    lines = wrap(d, c["head"], f_head, w - 20)
    assert len(lines) <= 2, f"headline too long: {c['head']}"
    for ln in lines:
        d.text((px(x + 10), px(hy)), ln, font=f_head, fill=INK)
        hy += head_lh
    head_bottom = hy
    # source line (bottom-anchored)
    src_y = y + h - 15
    d.text((px(x + 10), px(src_y)), c["src"] + "  \u00b7  " + c["time"],
           font=f_src, fill=MUTED)
    # body (bottom-anchored above source line)
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
BIG_Y, BIG_H, BIG_BANNER = 154, 205, 64
bw = (CWID - 2 * G) / 3
f_big_head = font(SERIF_B, 25)
f_big_body = font(SANS_R, 11.5)
f_src = font(SANS_R, 9.5)
f_banner_big = font(SANS_B, 30)
for i, c in enumerate(BIG):
    x = M + i * (bw + G)
    draw_card(x, BIG_Y, bw, BIG_H, BIG_BANNER, c, f_big_head, 27,
              f_big_body, 13.5, f_src, icon=c["icon"], banner_font=f_banner_big,
              max_body_lines=3)

# ================= medium cards =================
MED_Y = BIG_Y + BIG_H + G
MED_H, MED_BANNER = 150, 40
mw = (CWID - 4 * G) / 5
f_med_head = font(SERIF_B, 20)
f_med_body = font(SANS_R, 10.5)
f_banner_med = font(SANS_B, 19)
for i, c in enumerate(MEDIUM):
    row, col_i = divmod(i, 5)
    x = M + col_i * (mw + G)
    y = MED_Y + row * (MED_H + G)
    draw_card(x, y, mw, MED_H, MED_BANNER, c, f_med_head, 22,
              f_med_body, 12, f_src, icon=c["icon"], banner_font=f_banner_med,
              short_tag=True)

# ================= list =================
LIST_Y = MED_Y + 2 * MED_H + G + G
f_list_head = font(SANS_B, 10)
f_list = font(SANS_R, 11.5)
f_list_b = font(SANS_B, 11.5)
d.text((px(M), px(LIST_Y)), "THE REST OF THE DAY", font=f_list_head, fill=INK)
d.line([(px(M), px(LIST_Y + 15)), (px(W - M), px(LIST_Y + 15))], fill=LINE, width=px(1))
list_col_w = (CWID - G) / 2
ly = LIST_Y + 20
row_h = 12.5
for i, (n, place, region, sent, src, t, claim) in enumerate(LIST):
    col_i, row_i = divmod(i, 8)
    x = M + col_i * (list_col_w + G)
    y = ly + row_i * row_h
    col = REGION[region]
    pre = f"{n}  {place}: "
    d.text((px(x), px(y)), pre, font=f_list_b, fill=col)
    pre_w = d.textlength(pre, font=f_list_b) / S
    rest = sent + " \u2014 " + src + ", " + t
    if claim:
        rest += "  [CLAIM]"
    d.text((px(x + pre_w), px(y)), rest, font=f_list, fill=INK)
    total_w = d.textlength(pre, font=f_list_b) + d.textlength(rest, font=f_list)
    if total_w > px(list_col_w):
        print(f"OVERFLOW list {n}: {total_w / S:.0f}px > {list_col_w:.0f}px")

# ================= bottom band: map + legend =================
MAP_Y = LIST_Y + 20 + 8 * row_h + 10
MAP_H = 92
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
f_pin = font(SANS_B, 9)
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
    d.text((px(cx) - tw / 2, px(cy - 5)), str(n), font=f_pin, fill=(255, 255, 255))

d.text((px(leg_x), px(MAP_Y - 2)), "REGIONS", font=f_list_head, fill=INK)
f_leg = font(SANS_R, 11)
lyy = MAP_Y + 16
for name, cnt in REGION_COUNTS:
    d.rectangle([px(leg_x), px(lyy), px(leg_x + 10), px(lyy + 10)], fill=REGION[name])
    d.text((px(leg_x + 14), px(lyy - 1)), f"{name}  \u00b7  {cnt}", font=f_leg, fill=INK)
    lyy += 15
f_leg2 = font(SANS_R, 9.5)
fields_txt = "Fields: " + ", ".join(f"{n} {c}" for n, c in FIELD_COUNTS)
flines = wrap(d, fields_txt, f_leg2, leg_w)
fyy = lyy + 2
for ln in flines:
    d.text((px(leg_x), px(fyy)), ln, font=f_leg2, fill=MUTED)
    fyy += 12

# ================= date check =================
DC_Y = MAP_Y + MAP_H + 10
DC_H = 80
f_dc_head = font(SANS_B, 10)
f_dc = font(SANS_R, 10)
d.rectangle([px(M), px(DC_Y), px(W - M), px(DC_Y + DC_H)], fill=BAND_BG)
d.text((px(M + 8), px(DC_Y + 5)), "DATE CHECK", font=f_dc_head, fill=INK)
lines = [
    "Every story on this page happened or was first reported on Tuesday "
    "24 November 2026, in any time zone (times in UTC).",
    "Left out, before Tuesday: " + LEFT_OUT,
    "Shown only as background: " + BACKGROUND,
    "Not yet: " + NOT_YET,
]
yy = DC_Y + 20
for ln in lines:
    wl = wrap(d, ln, f_dc, CWID - 16)
    for part in wl:
        d.text((px(M + 8), px(yy)), part, font=f_dc, fill=INK)
        yy += 11
    yy += 0.5
assert yy <= DC_Y + DC_H - 2, f"date check overflows box: yy={yy:.0f} box bottom={DC_Y + DC_H}"

# ================= footer =================
F_Y = DC_Y + DC_H + 6
f_foot = font(SANS_R, 9)
foot = ("Badges: CONFIRMED 2+ outlets \u00b7 OFFICIAL an authority's own word \u00b7 "
        "REPORTED one outlet \u00b7 CLAIM one side says.  Sources: Reuters, AP, BBC, UN, "
        "WHO, ESA, CMSA, CAS, NY Post, FT.  Scenes are drawn illustrations, not photographs.")
fl = wrap(d, foot, f_foot, CWID)
for ln in fl:
    d.text((px(M), px(F_Y)), ln, font=f_foot, fill=MUTED)
    F_Y += 11

# ================= save =================
out = img.resize((W, H), Image.LANCZOS)
out.save("entry.png", optimize=True)
data = open("entry.png", "rb").read()
print(f"entry.png: {len(data)} bytes, sha256={hashlib.sha256(data).hexdigest()}")
print(f"footer ends ~{F_Y:.0f}px of 1024")

"""Capa do perfil: Criação de Adão em pontos (dither).

Adão (esquerda) vira o braço robótico de ref/robot.jpg.
Deus (direita) fica orgânico: densidade de '0' segue a luz (bayer).
"""
import sys
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

S = sys.argv[1]
OUT = f"{S}/profile/assets"
CELL = 6                       # px por caractere na imagem final
COLS, ROWS = 300, 66
FONT = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 7)
BOLD = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", 7)
BIG = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", 13)
THEMES = {
    "dark": {"hi": (230, 237, 243, 255), "mid": (150, 160, 170, 255), "lo": (88, 96, 105, 255)},
    "light": {"hi": (31, 35, 40, 255), "mid": (87, 96, 106, 255), "lo": (160, 168, 176, 255)},
}

src = Image.open(f"{S}/ref/adam.jpg").convert("RGB").crop((235, 195, 775, 313)).resize((COLS, ROWS), Image.LANCZOS)
hsv = np.asarray(src.convert("HSV")).astype(float) / 255
rgb = np.asarray(src).astype(float) / 255
skin = (hsv[..., 1] > 0.18) & (hsv[..., 1] < 0.62) & (hsv[..., 0] > 0.02) & (hsv[..., 0] < 0.11) & (hsv[..., 2] > 0.45)
dens = cv2.blur(skin.astype(np.float32), (3, 3))
skin &= dens > 0.4
lum = rgb @ [0.299, 0.587, 0.114]
lum = (lum - lum[skin].min()) / (np.ptp(lum[skin]) + 1e-6)

split = 140       # entre os dedos
# Adão robótico: braço da referência (ref/robot.jpg), recortado por GrabCut em ref/robot-mask.png.
# Grade cheia e regular; o metal é sombreado por tom, não por densidade.
rm = cv2.imread(f"{S}/ref/robot-mask.png", 0) > 0
rl = cv2.cvtColor(cv2.imread(f"{S}/ref/robot.jpg"), cv2.COLOR_BGR2GRAY).astype(float) / 255
ys, xs = np.nonzero(rm)
tip_x = xs.max(); tip_y = int(np.median(ys[xs > tip_x - 6]))
scale = 0.31                                         # células por pixel da referência
xoff = 137 - int(tip_x * scale)                      # ponta do dedo na coluna 137
gh, gw = int(rm.shape[0] * scale), int(rm.shape[1] * scale)
m_small = cv2.resize(rm.astype(np.float32), (gw, gh), interpolation=cv2.INTER_AREA)
l_small = cv2.resize(rl, (gw, gh), interpolation=cv2.INTER_AREA)
off = 42 - int(tip_y * scale)                        # ponta logo abaixo do dedo de Deus
robot = np.zeros((ROWS, COLS), np.uint8); rlum = np.zeros((ROWS, COLS))
for y in range(ROWS):
    sy = y - off
    if 0 <= sy < gh:
        for x in range(COLS):
            sx = x - xoff
            if sx < 0:
                sx %= 6                              # estende o braço até a borda repetindo o metal
            if sx < gw:
                robot[y, x] = m_small[sy, sx] > 0.5
                rlum[y, x] = l_small[sy, sx]
lo_, hi_ = np.percentile(rlum[robot > 0], [5, 95])
rlum = np.clip((rlum - lo_) / (hi_ - lo_ + 1e-6), 0, 1)
edge = robot - cv2.erode(robot, np.ones((3, 3), np.uint8))

# Deus orgânico: bayer sobre a luminância
bayer = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16
th = np.tile(bayer, (ROWS // 4 + 1, COLS // 4 + 1))[:ROWS, :COLS]
god = skin.copy(); god[:, :split] = False
god_on = god & (lum * 0.6 + 0.48 > th)

for theme, c in THEMES.items():
    im = Image.new("RGBA", (COLS * CELL, ROWS * CELL), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    put = lambda x, y, col, f=None: d.rectangle((x * CELL, y * CELL, x * CELL + CELL - 1, y * CELL + CELL - 1), fill=c["hi"])  # ponto
    for y in range(ROWS):
        for x in range(COLS):
            if robot[y, x]:
                if edge[y, x] or rlum[y, x] * 0.6 + 0.45 > th[y, x]:
                    put(x, y, c["hi"])
            elif god_on[y, x]:
                put(x, y, c["hi"] if lum[y, x] > 0.55 else c["mid"])
    # janela de terminal feita de 0, entre as mãos
    x0, y0, x1, y1 = 144, 1, 198, 15
    for x in range(x0, x1 + 1):
        put(x, y0, c["hi"], BOLD); put(x, y0 + 3, c["hi"], BOLD); put(x, y1, c["hi"], BOLD)
    for y in range(y0, y1 + 1):
        put(x0, y, c["hi"], BOLD); put(x1, y, c["hi"], BOLD)
    for x in range(x0 + 1, x1):                   # limpa o miolo e escreve
        for y in (y0 + 1, y0 + 2, *range(y0 + 4, y1)):
            d.rectangle((x * CELL, y * CELL, x * CELL + CELL - 1, y * CELL + CELL - 1), fill=(0, 0, 0, 0))
    d.text(((x0 + 2) * CELL, (y0 + 1) * CELL - 1), "ROBERTO.EXE", fill=c["hi"], font=BIG)
    d.text(((x1 - 9) * CELL, (y0 + 1) * CELL - 1), "0 0 0", fill=c["hi"], font=BIG)
    d.text(((x0 + 3) * CELL, (y0 + 6) * CELL), "> agents.run()", fill=c["hi"], font=BIG)
    d.text(((x0 + 3) * CELL, (y0 + 10) * CELL), "> 0 errors", fill=c["mid"], font=BIG)
    im.save(f"{OUT}/banner-{theme}.png", optimize=True)
    bg = Image.new("RGB", im.size, (13, 17, 23) if theme == "dark" else (255, 255, 255))
    bg.paste(im, mask=im); bg.save(f"{S}/prev-banner0-{theme}.png")
print(im.size)

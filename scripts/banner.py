"""Capa do perfil: Criação de Adão desenhada só com '0'.

Adão (esquerda) vira braço robótico: contorno poligonal, grade uniforme, juntas.
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
# Adão robótico: desenhado em geometria na pose do original (coordenadas em células)
robot = np.zeros((ROWS, COLS), np.uint8)
joints = np.zeros((ROWS, COLS), np.uint8)
P = lambda pts: np.array(pts, np.int32)
cv2.fillPoly(robot, [P([(0, 44), (84, 33), (88, 46), (0, 63)])], 1)          # antebraço
cv2.fillPoly(robot, [P([(97, 30), (111, 29), (113, 42), (99, 45)])], 1)      # palma
fingers = [  # (pontos, espessura)
    ([(112, 31), (121, 30), (130, 31), (137, 33)], 3),                     # indicador, esticado
    ([(113, 36), (120, 38), (125, 43), (124, 48)], 2),
    ([(112, 40), (118, 44), (121, 49), (119, 53)], 2),
    ([(110, 43), (114, 48), (115, 52)], 2),
    ([(99, 44), (104, 50), (111, 52)], 2),                                  # polegar
]
for f, w in fingers:
    for a, b in zip(f, f[1:]):
        cv2.line(robot, a, b, 1, w)
    for j in f[1:-1]:
        joints[j[1], j[0]] = 1
cv2.circle(joints, (92, 40), 6, 1, 1)                                       # punho
cv2.circle(robot, (92, 40), 6, 1, -1)
edge = robot - cv2.erode(robot, np.ones((3, 3), np.uint8))
seam = np.zeros_like(robot)
for x in range(8, 84, 13):                                                  # placas do antebraço
    seam[:, x] = 1
seam[:, 105] = 1
inner = cv2.erode(robot, np.ones((3, 3), np.uint8))
seam &= inner
edge |= joints & robot

# Deus orgânico: bayer sobre a luminância
bayer = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16
th = np.tile(bayer, (ROWS // 4 + 1, COLS // 4 + 1))[:ROWS, :COLS]
god = skin.copy(); god[:, :split] = False
god_on = god & (lum * 0.7 + 0.42 > th)

for theme, c in THEMES.items():
    im = Image.new("RGBA", (COLS * CELL, ROWS * CELL), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    put = lambda x, y, col, f=FONT, ch="0": d.text((x * CELL + 1, y * CELL - 2), ch, fill=col, font=f)
    for y in range(ROWS):
        for x in range(COLS):
            if robot[y, x]:
                if edge[y, x]:
                    put(x, y, c["hi"], BOLD)
                elif not seam[y, x]:
                    put(x, y, c["mid"])
            elif god_on[y, x]:
                put(x, y, c["hi"] if lum[y, x] > 0.55 else c["mid"])
    # janela de terminal feita de 0, entre as mãos
    x0, y0, x1, y1 = 112, 1, 168, 16
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

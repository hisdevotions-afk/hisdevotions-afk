"""Capa do perfil: a versão inicial (Criação de Adão pontilhada), com o braço de Adão
trocado pelo braço robótico de ref/robot.jpg (máscara em ref/robot-mask.png).
"""
import sys
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

S = sys.argv[1]
OUT = f"{S}/profile/assets"
INK = {"dark": (230, 237, 243, 255), "light": (31, 35, 40, 255)}
BAYER = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16

# --- mão de Deus: idêntica à versão inicial ---
src = Image.open(f"{S}/ref/adam.jpg").convert("RGB").crop((185, 185, 745, 315))
W = 300
src = src.resize((W, int(src.height * W / src.width)), Image.LANCZOS)
hsv = np.asarray(src.convert("HSV")).astype(float) / 255
rgb = np.asarray(src).astype(float) / 255
skin = (hsv[..., 1] > 0.18) & (hsv[..., 1] < 0.62) & (hsv[..., 0] > 0.02) & (hsv[..., 0] < 0.11) & (hsv[..., 2] > 0.45)
lum = rgb @ [0.299, 0.587, 0.114]
lum = (lum - lum[skin].min()) / (np.ptp(lum[skin]) + 1e-6)
h, w = lum.shape
th = np.tile(BAYER, (h // 4 + 1, w // 4 + 1))[:h, :w]
mask = skin & (lum * 0.85 + 0.25 > th)
dens = np.asarray(Image.fromarray((skin * 255).astype(np.uint8)).filter(ImageFilter.BoxBlur(3))) / 255
mask &= dens > 0.45

SPLIT = 165                                   # entre os dedos: à esquerda era Adão
mask[:, :SPLIT] = False
god_cols = np.nonzero(mask.any(axis=0))[0]
god_tip_x = god_cols.min()
god_tip_y = int(np.median(np.nonzero(mask[:, god_tip_x:god_tip_x + 3].any(axis=1))[0]))

# --- braço robótico no lugar de Adão, com o mesmo dither ---
rm = cv2.imread(f"{S}/ref/robot-mask.png", 0) > 0
gray = cv2.cvtColor(cv2.imread(f"{S}/ref/robot.jpg"), cv2.COLOR_BGR2GRAY)
gray = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8)).apply(gray)     # contraste local do cromado
rl = gray.astype(float) / 255
# arestas entre as peças (falanges, punho, placas), só dentro do braço
edges = cv2.Canny(cv2.GaussianBlur(gray, (5, 5), 0), 110, 220) > 0
edges &= cv2.erode(rm.astype(np.uint8), np.ones((5, 5), np.uint8)) > 0
ys, xs = np.nonzero(rm)
tip_x = xs.max(); tip_y = int(np.median(ys[xs > tip_x - 6]))
scale = 0.22
gh, gw = int(rm.shape[0] * scale), int(rm.shape[1] * scale)
m_small = cv2.resize(rm.astype(np.float32), (gw, gh), interpolation=cv2.INTER_AREA) > 0.5
l_small = cv2.resize(rl, (gw, gh), interpolation=cv2.INTER_AREA)
e_small = cv2.resize(edges.astype(np.float32), (gw, gh), interpolation=cv2.INTER_AREA) > 0.4
xoff = god_tip_x - 6 - int(tip_x * scale)     # ponta robótica 6 pontos antes do dedo de Deus
# altura: o topo do braço sob a janela (colunas 123 a 186) fica logo abaixo dela (linha 32)
under = rm[:, int((123 - xoff) / scale):]
yoff = 32 - int(np.nonzero(under.any(axis=1))[0].min() * scale)
# Antebraço da referência (x < WRIST px) esticado ao longo do eixo até a borda esquerda;
# a mão (x >= WRIST) fica na escala original.
WRIST = 165
xh = xoff + int(WRIST * scale)                 # coluna onde começa a mão
def area(a, size):
    return cv2.resize(a.astype(np.float32), size, interpolation=cv2.INTER_AREA)
fa_m = area(rm[:, :WRIST], (xh, gh)) > 0.5
fa_l = area(rl[:, :WRIST], (xh, gh))
fa_e = area(edges[:, :WRIST], (xh, gh)) > 0.4
robot = np.zeros((h, w), bool); rlum = np.zeros((h, w)); line = np.zeros((h, w), bool)
for y in range(h):
    sy = y - yoff
    if not 0 <= sy < gh:
        continue
    for x in range(SPLIT):
        if x < xh:
            robot[y, x], rlum[y, x], line[y, x] = fa_m[sy, x], fa_l[sy, x], fa_e[sy, x]
        elif (sx := x - xoff) < gw:
            robot[y, x], rlum[y, x], line[y, x] = m_small[sy, sx], l_small[sy, sx], e_small[sy, sx]
lo_, hi_ = np.percentile(rlum[robot], [5, 95])
rlum = np.clip((rlum - lo_) / (hi_ - lo_ + 1e-6), 0, 1)
outline = robot & ~cv2.erode(robot.astype(np.uint8), np.ones((3, 3), np.uint8)).astype(bool)
fill = robot & (rlum * 0.8 + 0.33 > th) & ~line          # aresta vira fresta escura dentro do metal
mask |= fill | outline

# --- render: igual à versão inicial ---
for theme, c in INK.items():
    a = np.zeros((h, w, 4), np.uint8); a[mask] = c
    im = Image.fromarray(a).resize((w * 3, h * 3), Image.NEAREST)
    d = ImageDraw.Draw(im)
    x0, y0, x1, y1 = 370, 6, 560, 92
    d.rectangle((x0, y0, x1, y1), fill=(0, 0, 0, 0))
    d.rectangle((x0, y0, x1, y1), outline=c, width=3)
    d.line((x0, y0 + 20, x1, y0 + 20), fill=c, width=3)
    for i in range(3):
        d.rectangle((x1 - 18 - i * 16, y0 + 6, x1 - 8 - i * 16, y0 + 14), outline=c, width=2)
    d.text((x0 + 8, y0 + 5), "ROBERTO.EXE", fill=c)
    d.text((x0 + 12, y0 + 34), "> agents.run()", fill=c)
    im.save(f"{OUT}/banner-{theme}.png", optimize=True)
    bg = Image.new("RGB", im.size, (13, 17, 23) if theme == "dark" else (255, 255, 255))
    bg.paste(im, mask=im); bg.save(f"{S}/prev-v1-{theme}.png")
print(im.size, "dedo de Deus", god_tip_x, god_tip_y, "ponta robô", xoff + int(tip_x * scale), yoff + int(tip_y * scale))

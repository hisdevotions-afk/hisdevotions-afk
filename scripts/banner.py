"""Capa do perfil na composição da referência: duas mãos grandes em pontilhado
estocástico, janela de terminal vazada no centro. A mão de Adão (esquerda) é o
braço robótico de ref/robot.jpg; a de Deus (direita) vem do afresco.
"""
import sys
import cv2
import numpy as np
from PIL import Image, ImageDraw

S = sys.argv[1]
OUT = f"{S}/profile/assets"
GW, GH, DOT = 700, 239, 2                      # grade de pontos e tamanho do ponto em px
INK = {"dark": (230, 237, 243, 255), "light": (31, 35, 40, 255)}
rng = np.random.default_rng(7)
noise = rng.random((GH, GW))


def place(mask, lum, anchor, scale, at, edges=None):
    """Escala a fonte e põe o ponto `anchor` (px da fonte) na célula `at` da grade."""
    M = np.float32([[scale, 0, at[0] - anchor[0] * scale], [0, scale, at[1] - anchor[1] * scale]])
    warp = lambda a: cv2.warpAffine(a.astype(np.float32), M, (GW, GH), flags=cv2.INTER_AREA)
    out = warp(mask) > 0.5, warp(lum)
    return out + ((warp(edges) > 0.35),) if edges is not None else out


# Deus: pele do afresco
fresco = cv2.imread(f"{S}/ref/adam-1920.jpg")   # coordenadas abaixo estão na versão de 1280 px
K = fresco.shape[1] / 1280
hsv = cv2.cvtColor(fresco, cv2.COLOR_BGR2HSV_FULL).astype(float) / 255
skin = (hsv[..., 1] > 0.16) & (hsv[..., 1] < 0.65) & (hsv[..., 0] > 0.015) & (hsv[..., 0] < 0.12) & (hsv[..., 2] > 0.38)
skin = cv2.morphologyEx(skin.astype(np.uint8), cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
skin = cv2.morphologyEx(skin, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8)) > 0
arm = np.zeros(skin.shape, np.uint8)            # só o braço e a mão de Deus, sem os anjos
cv2.fillPoly(arm, [np.int32(K * np.array([(482, 250), (530, 240), (620, 222), (680, 205), (730, 185), (790, 178),
                             (790, 242), (700, 252), (620, 275), (565, 282), (548, 306), (498, 306), (482, 275)]))], 1)
skin &= arm > 0
flum = cv2.cvtColor(fresco, cv2.COLOR_BGR2GRAY).astype(float) / 255
god_tip = (488 * K, 262 * K)                          # ponta do indicador de Deus no afresco
g_mask, g_lum = place(skin, flum, god_tip, 2.45 / K, (int(GW * 0.522), int(GH * 0.47)))

# Adão robótico
robot_img = cv2.imread(f"{S}/ref/robot.jpg")
rmask = cv2.imread(f"{S}/ref/robot-mask.png", 0) > 0
rgray = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8)).apply(cv2.cvtColor(robot_img, cv2.COLOR_BGR2GRAY))
redges = cv2.Canny(cv2.GaussianBlur(rgray, (5, 5), 0), 110, 220) > 0
redges &= cv2.erode(rmask.astype(np.uint8), np.ones((5, 5), np.uint8)) > 0
ys, xs = np.nonzero(rmask)
r_tip = (xs.max(), int(np.median(ys[xs > xs.max() - 6])))
r_mask, r_lum, r_edge = place(rmask, rgray.astype(float) / 255, r_tip, 1.2, (int(GW * 0.5), int(GH * 0.62)), redges)
r_mask[:, int(GW * 0.515):] = False


def norm(lum, m):
    lo, hi = np.percentile(lum[m], [3, 97])
    return np.clip((lum - lo) / (hi - lo + 1e-6), 0, 1)


dots = (g_mask & (norm(g_lum, g_mask) * 0.8 + 0.1 > noise)) | \
       (r_mask & ~r_edge & (norm(r_lum, r_mask) * 0.72 + 0.12 > noise))

for theme, c in INK.items():
    a = np.zeros((GH, GW, 4), np.uint8); a[dots] = c
    im = Image.fromarray(a).resize((GW * DOT, GH * DOT), Image.NEAREST)
    d = ImageDraw.Draw(im)
    W, H = im.size
    x0, y0, x1, y1 = int(W * 0.373), int(H * 0.09), int(W * 0.672), int(H * 0.72)
    d.rectangle((x0, y0, x1, y1), outline=c, width=3)
    d.line((x0, y0 + 26, x1, y0 + 26), fill=c, width=2)
    d.text((x0 + 12, y0 + 8), "ROBERTO.EXE", fill=c)
    for i in range(3):
        d.rectangle((x1 - 22 - i * 18, y0 + 8, x1 - 10 - i * 18, y0 + 18), outline=c, width=2)
    im = im.crop((0, 0, W, 410))                # corta a faixa vazia de baixo
    im.save(f"{OUT}/banner-{theme}.png", optimize=True)
    bg = Image.new("RGB", im.size, (13, 17, 23) if theme == "dark" else (255, 255, 255))
    bg.paste(im, mask=im); bg.save(f"{S}/prev-ref-{theme}.png")
print(im.size)

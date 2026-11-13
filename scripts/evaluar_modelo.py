"""Evalua un modelo YOLO sobre un set etiquetado (carpetas images/ y labels/).

Mide el % de acierto de la clase principal (clase mayoritaria en el label vs. la deteccion
de mayor confianza; sin detecciones cuenta como "sana") y las cajas por imagen para
varios umbrales de confianza. Usa el mismo pipeline que el backend (PIL RGB, iou 0.45,
NMS agnostico), asi los numeros son comparables entre modelos.

Uso:
    python scripts/evaluar_modelo.py --model app/models/best.pt --data <ruta>/test
"""
import argparse
import collections
import glob
import os

from PIL import Image, ImageOps
from ultralytics import YOLO

SANA = 4


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--data", required=True, help="carpeta con images/ y labels/")
    ap.add_argument("--iou", type=float, default=0.45)
    ap.add_argument("--imgsz", type=int, default=640)
    args = ap.parse_args()

    model = YOLO(args.model)
    print(f"Modelo: {args.model}  clases: {model.names}")

    data, gt_boxes = [], 0
    for p in sorted(glob.glob(os.path.join(args.data, "images", "*"))):
        lab = os.path.join(args.data, "labels", os.path.splitext(os.path.basename(p))[0] + ".txt")
        if not os.path.exists(lab):
            continue
        cls = [int(l.split()[0]) for l in open(lab) if l.strip()]
        if not cls:
            continue
        gt_boxes += len(cls)
        gt = collections.Counter(cls).most_common(1)[0][0]
        im = ImageOps.exif_transpose(Image.open(p)).convert("RGB")
        b = model(im, conf=0.10, iou=args.iou, imgsz=args.imgsz, agnostic_nms=True, verbose=False)[0].boxes
        data.append((gt, b.conf.tolist(), [int(c) for c in b.cls.tolist()]))

    n = len(data)
    print(f"Imagenes: {n}  cajas reales por imagen: {gt_boxes / n:.2f}\n")
    print("conf  | acierto clase principal | cajas/imagen")
    for t in (0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50):
        ok = nb = 0
        for gt, confs, clss in data:
            keep = [(c, k) for c, k in zip(confs, clss) if c >= t]
            nb += len(keep)
            ok += (max(keep)[1] if keep else SANA) == gt
        print(f"{t:.2f}  | {ok / n:22.1%} | {nb / n:.2f}")


if __name__ == "__main__":
    main()

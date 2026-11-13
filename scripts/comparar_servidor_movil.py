"""Compara el modelo del servidor (best.pt) con el del celular (TFLite) sobre las mismas imagenes.

1. Corre best.pt con el pipeline del backend (PIL RGB + EXIF, conf 0.30, iou 0.45, NMS
   agnostico) y mide el tiempo por imagen en la PC.
2. Lee resultados.json del benchmark del celular (integration_test/benchmark_test.dart).
3. Reporta: latencia de cada uno, concordancia de la clase principal (deteccion de mayor
   confianza; sin detecciones = "sana", igual que la app) y emparejamiento de cajas
   (misma clase e IoU >= 0.5).

Uso:
    python scripts/comparar_servidor_movil.py --imgs D:/ProyectoInvestigacion/para_roboflow/test/images --movil resultados.json
"""
import argparse
import json
import os
import statistics
import time

from PIL import Image, ImageOps
from ultralytics import YOLO


def iou(a, b):
    ax2, ay2, bx2, by2 = a[0] + a[2], a[1] + a[3], b[0] + b[2], b[1] + b[3]
    iw = max(0.0, min(ax2, bx2) - max(a[0], b[0]))
    ih = max(0.0, min(ay2, by2) - max(a[1], b[1]))
    inter = iw * ih
    union = a[2] * a[3] + b[2] * b[3] - inter
    return inter / union if union > 0 else 0.0


def principal(dets):
    return max(dets, key=lambda d: d["confidence"])["label"] if dets else "sana"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--imgs", required=True)
    ap.add_argument("--movil", required=True)
    ap.add_argument("--model", default="app/models/best.pt")
    ap.add_argument("--salida", default="comparacion_servidor_movil.json")
    args = ap.parse_args()

    movil = json.load(open(args.movil, encoding="utf-8"))
    model = YOLO(args.model)
    names = model.names

    srv, tiempos = {}, []
    for r in movil["images"]:
        im = ImageOps.exif_transpose(Image.open(os.path.join(args.imgs, r["file"]))).convert("RGB")
        t0 = time.perf_counter()
        b = model(im, conf=0.30, iou=0.45, imgsz=640, agnostic_nms=True, verbose=False)[0].boxes
        tiempos.append((time.perf_counter() - t0) * 1000)
        dets = []
        for (x1, y1, x2, y2), c, k in zip(b.xyxyn.tolist(), b.conf.tolist(), b.cls.tolist()):
            dets.append({"rect": [x1, y1, x2 - x1, y2 - y1], "label": names[int(k)], "confidence": c})
        srv[r["file"]] = dets

    n = len(movil["images"])
    igual_clase = cajas_srv = cajas_mov = emparejadas = 0
    for r in movil["images"]:
        s, m = srv[r["file"]], r["detections"]
        igual_clase += principal(s) == principal(m)
        cajas_srv += len(s)
        cajas_mov += len(m)
        libres = list(m)
        for d in s:
            mejor = max(libres, key=lambda e: iou(d["rect"], e["rect"]) if e["label"] == d["label"] else -1, default=None)
            if mejor and mejor["label"] == d["label"] and iou(d["rect"], mejor["rect"]) >= 0.5:
                emparejadas += 1
                libres.remove(mejor)

    ms_mov = [r["ms"] for r in movil["images"]][1:]  # la primera es calentamiento
    ms_srv = tiempos[1:]
    res = {
        "imagenes": n,
        "movil_ms_media": statistics.mean(ms_mov),
        "movil_ms_de": statistics.stdev(ms_mov),
        "movil_ms_mediana": statistics.median(ms_mov),
        "movil_carga_modelo_ms": movil.get("load_ms"),
        "servidor_pc_ms_media": statistics.mean(ms_srv),
        "servidor_pc_ms_de": statistics.stdev(ms_srv),
        "concordancia_clase_principal": igual_clase / n,
        "cajas_servidor": cajas_srv,
        "cajas_movil": cajas_mov,
        "cajas_emparejadas_iou50": emparejadas,
        "recall_cajas_movil_vs_servidor": emparejadas / cajas_srv if cajas_srv else None,
        "precision_cajas_movil_vs_servidor": emparejadas / cajas_mov if cajas_mov else None,
    }
    json.dump(res, open(args.salida, "w", encoding="utf-8"), indent=2)
    for k, v in res.items():
        print(f"{k:36} {v:.3f}" if isinstance(v, float) else f"{k:36} {v}")


if __name__ == "__main__":
    main()

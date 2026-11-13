"""Agrupa las fotos de campo por planta/rafaga y asigna train/valid/test por GRUPO.

Evita la fuga de datos (Regla 5 de la guia de etiquetado): las fotos tomadas
seguidas a la misma planta y los cuadros de un mismo video nunca quedan
repartidos entre subconjuntos.

Agrupacion (a partir del nombre AAAAMMDD_HHMMSS*.jpg):
  - Cuadros de video  (..._frame_NNNNNN.jpg): un grupo por video.
  - Fotos: se ordenan por hora dentro de cada carpeta; si entre una foto y la
    siguiente pasan mas de --gap segundos, empieza un grupo nuevo.

Asignacion: dentro de cada carpeta (sesion/hora) los grupos se reparten
70/20/10 de forma reproducible (semilla fija), asi cada hora del dia queda
representada en los tres subconjuntos.

Uso:
  python scripts/agrupar_split.py --src D:/ProyectoInvestigacion/dataset_procesado
  python scripts/agrupar_split.py --src ... --copiar D:/ProyectoInvestigacion/para_roboflow
"""
import argparse
import csv
import random
import re
import shutil
from collections import defaultdict
from datetime import datetime
from pathlib import Path

PAT = re.compile(r"(\d{8})_(\d{6})(?:_frame_(\d+))?")
EXTS = {".jpg", ".jpeg", ".png"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True)
    # 30 s: con 90 s varias plantas fotografiadas caminando por el surco quedaban en un solo grupo
    ap.add_argument("--gap", type=int, default=30, help="segundos sin fotos que separan una planta de otra")
    ap.add_argument("--valid", type=float, default=0.2)
    ap.add_argument("--test", type=float, default=0.1)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--copiar", help="carpeta destino en formato YOLO (train/valid/test) para subir a Roboflow")
    ap.add_argument("--etiquetas", help="dataset YOLO previo (con train/labels...) cuyas etiquetas se reutilizan")
    ap.add_argument("--max-lado", type=int, default=2048, help="lado mayor maximo de las imagenes copiadas")
    args = ap.parse_args()
    src = Path(args.src)

    por_carpeta = defaultdict(list)
    sin_fecha = []
    for p in sorted(src.rglob("*")):
        if p.suffix.lower() not in EXTS:
            continue
        m = PAT.search(p.stem)
        if not m:
            sin_fecha.append(p)
            continue
        t = datetime.strptime(m.group(1) + m.group(2), "%Y%m%d%H%M%S")
        por_carpeta[p.parent.relative_to(src).as_posix()].append((t, m.group(3) is not None, p))

    filas = []
    rng = random.Random(args.seed)
    resumen = defaultdict(lambda: defaultdict(int))
    for carpeta, items in sorted(por_carpeta.items()):
        grupos = defaultdict(list)
        n, prev = 0, None
        for t, es_frame, p in sorted(items, key=lambda x: (x[0], x[2].name)):
            if es_frame:
                gid = f"{carpeta}/video_{t:%Y%m%d_%H%M%S}"
            else:
                if prev is None or (t - prev).total_seconds() > args.gap:
                    n += 1
                prev = t
                gid = f"{carpeta}/g{n:03d}"
            grupos[gid].append((t, p))
        ids = sorted(grupos)
        rng.shuffle(ids)
        # Cada grupo va al subconjunto que mas lejos esta de su proporcion objetivo
        # (en numero de imagenes), asi los grupos grandes no desbalancean el split.
        meta = {"test": args.test, "valid": args.valid, "train": 1 - args.test - args.valid}
        cuenta = {k: 0 for k in meta}
        total = sum(len(grupos[g]) for g in ids)
        for gid in sorted(ids, key=lambda g: -len(grupos[g])):
            split = max(meta, key=lambda k: meta[k] * total - cuenta[k]) if len(ids) >= 3 else "train"
            cuenta[split] += len(grupos[gid])
            for t, p in grupos[gid]:
                filas.append((p.relative_to(src).as_posix(), carpeta, gid, split, t.isoformat()))
                resumen[carpeta][split] += 1
            resumen[carpeta]["grupos"] += 1

    out = src / "split_por_grupo.csv"
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["archivo", "carpeta", "grupo", "split", "fecha_hora"])
        w.writerows(filas)

    tot = defaultdict(int)
    print(f"{'carpeta':32} {'grupos':>6} {'train':>6} {'valid':>6} {'test':>6}")
    for c, r in sorted(resumen.items()):
        print(f"{c:32} {r['grupos']:6} {r['train']:6} {r['valid']:6} {r['test']:6}")
        for k in ("grupos", "train", "valid", "test"):
            tot[k] += r[k]
    print(f"{'TOTAL':32} {tot['grupos']:6} {tot['train']:6} {tot['valid']:6} {tot['test']:6}")
    if sin_fecha:
        print(f"\n{len(sin_fecha)} imagen(es) sin fecha en el nombre (revisar a mano), ej: {sin_fecha[0].name}")
    print(f"\nCSV: {out}")

    if args.copiar:
        copiar_yolo(src, Path(args.copiar), filas, args.etiquetas, args.max_lado)


NOMBRES = ["mildiu", "mosca_blanca", "oidio", "polilla", "sana"]


def copiar_yolo(src, dst, filas, etiquetas, max_lado):
    """Carpeta en formato YOLO (split/images + split/labels + data.yaml) para
    arrastrar a Roboflow: respeta el split por planta al subir.

    Las etiquetas viejas (export de Roboflow "stretch" a 640x640) estan en
    coordenadas normalizadas, por eso valen tal cual sobre la foto original.
    """
    from PIL import Image

    viejas = {}
    if etiquetas:
        for txt in Path(etiquetas).glob("*/labels/*.txt"):
            viejas[re.sub(r"_(jpg|jpeg|png)\.rf\..*$", "", txt.stem, flags=re.I)] = txt
    con, sin = 0, 0
    for archivo, _, gid, split, _ in filas:
        img_dir, lbl_dir = dst / split / "images", dst / split / "labels"
        img_dir.mkdir(parents=True, exist_ok=True)
        lbl_dir.mkdir(parents=True, exist_ok=True)
        # el grupo va en el nombre para poder rastrear la planta en Roboflow
        nombre = gid.replace("/", "__") + "__" + Path(archivo).stem
        im = Image.open(src / archivo).convert("RGB")
        if max(im.size) > max_lado:  # reduce peso; sin deformar (la proporcion se mantiene)
            im.thumbnail((max_lado, max_lado), Image.LANCZOS)
        im.save(img_dir / f"{nombre}.jpg", quality=92)
        txt = viejas.get(Path(archivo).stem)
        if txt:
            shutil.copy2(txt, lbl_dir / f"{nombre}.txt")
            con += 1
        else:
            sin += 1
    (dst / "data.yaml").write_text(
        "train: train/images\nval: valid/images\ntest: test/images\n\n"
        f"nc: {len(NOMBRES)}\nnames: {NOMBRES}\n", encoding="utf-8")
    print(f"Listo en {dst}: {con} con etiquetas previas, {sin} sin etiquetar")


if __name__ == "__main__":
    main()

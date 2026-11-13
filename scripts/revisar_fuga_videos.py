"""Detecta fuga entre videos y rafagas de fotos de la misma planta y propone a que split moverlas.

agrupar_split.py agrupa fotos por rafaga (< 30 s) y cada video por separado. Pero un video grabado a
segundos de una rafaga es casi seguro la misma planta, y pudo caer en otro subconjunto.

Regla: un video y un grupo de fotos se unen si sus horarios se acercan a menos de --gap segundos
(el video dura desde su inicio hasta su ultimo cuadro, a --fps). Los grupos unidos se juntan en
componentes; cada componente se lleva entero al split que ya tiene mas imagenes (se mueve lo minimo).

Uso:
  python scripts/revisar_fuga_videos.py --csv D:/ProyectoInvestigacion/dataset_procesado/split_por_grupo.csv \
      --salida D:/ProyectoInvestigacion/app/tareas/movimientos_split_v5.csv
"""
import argparse
import collections
import csv
import datetime as dt
import re

ap = argparse.ArgumentParser()
ap.add_argument("--csv", required=True)
ap.add_argument("--salida", required=True)
ap.add_argument("--gap", type=float, default=30)
ap.add_argument("--fps", type=float, default=30)
a = ap.parse_args()

filas = list(csv.DictReader(open(a.csv, encoding="utf-8")))
G = collections.defaultdict(list)
for x in filas:
    G[x["grupo"]].append(x)


def es_video(v):
    return "frames" in v[0]["carpeta"]


def rango(v):
    if es_video(v):
        ini = dt.datetime.strptime(re.search(r"video_(\d{8}_\d{6})", v[0]["grupo"]).group(1), "%Y%m%d_%H%M%S")
        cuadros = [int(re.search(r"frame_(\d+)", x["archivo"]).group(1)) for x in v]
        return ini + dt.timedelta(seconds=min(cuadros) / a.fps), ini + dt.timedelta(seconds=max(cuadros) / a.fps)
    t = sorted(dt.datetime.fromisoformat(x["fecha_hora"]) for x in v)
    return t[0], t[-1]


R = {g: rango(v) for g, v in G.items()}
padre = {g: g for g in G}


def raiz(g):
    while padre[g] != g:
        padre[g] = padre[padre[g]]
        g = padre[g]
    return g


gap = dt.timedelta(seconds=a.gap)
videos = [g for g in G if es_video(G[g])]
fotos = [g for g in G if not es_video(G[g])]
for v in videos:
    for f in fotos:
        (a0, a1), (b0, b1) = R[v], R[f]
        if b0 - gap <= a1 and b1 + gap >= a0:
            padre[raiz(v)] = raiz(f)

comp = collections.defaultdict(list)
for g in G:
    comp[raiz(g)].append(g)

mov = []
for gs in comp.values():
    splits = collections.Counter(x["split"] for g in gs for x in G[g])
    if len(splits) < 2:
        continue
    destino = splits.most_common(1)[0][0]
    for g in gs:
        for x in G[g]:
            if x["split"] != destino:
                nombre = g.replace("/", "__") + "__" + x["archivo"].replace("\\", "/").rsplit("/", 1)[-1]
                mov.append({"nombre_roboflow": nombre, "archivo": x["archivo"], "grupo": g, "componente": "+".join(sorted(gs)),
                            "de": x["split"], "a": destino})

with open(a.salida, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["nombre_roboflow", "archivo", "grupo", "componente", "de", "a"])
    w.writeheader()
    w.writerows(mov)

print(f"Componentes con fuga: {sum(1 for gs in comp.values() if len({x['split'] for g in gs for x in G[g]}) > 1)}")
print(f"Imagenes a mover: {len(mov)}", dict(collections.Counter((m['de'], m['a']) for m in mov)))
nuevo = collections.Counter(x["split"] for x in filas)
for m in mov:
    nuevo[m["de"]] -= 1
    nuevo[m["a"]] += 1
print("Antes:", dict(collections.Counter(x["split"] for x in filas)), "Despues:", dict(nuevo))

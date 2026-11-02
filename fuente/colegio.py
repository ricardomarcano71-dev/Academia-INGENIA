#!/usr/bin/env python3
"""Pone clases que ya están en la plataforma también en "Mi colegio" de un colegio.
Uso: python3 fuente/colegio.py REPO <colegio> <AAAA-MM-DD> <id> [<id> ...]
  colegio: idea | fatima (ver COLEGIOS en llaves.py)
  fecha:   el día de la clase en el colegio (la página las ordena por fecha)
La clase no se vuelve a cifrar: su llave se envuelve también con la llave del colegio, así la
abren sus alumnos aunque no tengan el plan del nivel. Las llaves salen de llaves-por-nivel.json.
Clases nuevas, solo del colegio: usa agregar_clase.py con --colegio y --fecha."""
import sys, os, json
here = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, here)
from llaves import ARCHIVO_LLAVES, COLEGIOS, aes_planes, verificar, agregar_planes, planes_del_archivo

repo, col, fecha, ids = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4:]
assert col in COLEGIOS, 'colegio desconocido: ' + col
assert len(fecha) == 10 and fecha[4] == '-' and fecha[7] == '-', 'fecha AAAA-MM-DD'
dp = os.path.join(repo, 'datos.json'); D = json.load(open(dp, encoding='utf-8'))
aes = aes_planes(json.load(open(ARCHIVO_LLAVES)), D); verificar(aes, D)
C = {c['id']: c for c in D['clases']}
for cid in ids:
    c = C[cid]; f = os.path.join(repo, 'c', cid + '.bin')
    if not c.get('gratis'):
        raw = agregar_planes(open(f, 'rb').read(), aes, [COLEGIOS[col]])
        open(f, 'wb').write(raw)
        print(cid, '→ la abren:', ', '.join(planes_del_archivo(raw)))
    c['colegios'] = list(dict.fromkeys((c.get('colegios') or []) + [col])); c['fecha'] = fecha
json.dump(D, open(dp, 'w', encoding='utf-8'), ensure_ascii=False)

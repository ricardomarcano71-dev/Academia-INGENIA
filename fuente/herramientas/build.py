#!/usr/bin/env python3
"""Arma herramientas/<id>.html a partir de kit.html y datos/<id>.js.
Uso: python3 fuente/herramientas/build.py [id ...]   (sin ids arma todas)"""
import sys, pathlib, re
aqui = pathlib.Path(__file__).resolve().parent
raiz = aqui.parent.parent
kit = (aqui / 'kit.html').read_text()
ids = sys.argv[1:] or [p.stem for p in sorted((aqui / 'datos').glob('*.js'))]
for i in ids:
    d = (aqui / 'datos' / f'{i}.js').read_text()
    m = {k: re.search(rf'//\s*{k}:\s*(.+)', d).group(1).strip() for k in ('TITULO', 'ICONO')}
    h = kit.replace('{{DATA}}', d).replace('{{TITULO}}', m['TITULO']).replace('{{ICONO}}', m['ICONO']).replace('{{ID}}', i)
    (raiz / 'herramientas' / f'{i}.html').write_text(h)
    print('armada', i)

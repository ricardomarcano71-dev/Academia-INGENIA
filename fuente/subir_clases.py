#!/usr/bin/env python3
"""Sube clases nuevas o cambiadas sin conocer la llave: las cifra con la llave pública
de la plataforma (fuente/publica.pem) y GitHub Actions las pasa a la llave del mes.
Uso: python3 subir_clases.py REPO id1 id2 ...   (ids de catalogo.json; 'todas' = todas)"""
import sys, os, json, shutil
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
here = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, here)
repo = sys.argv[1]; ids = sys.argv[2:]; src = '/mnt/project-files'
from build import quitar_descarga
pub = serialization.load_pem_public_key(open(os.path.join(repo, 'fuente/publica.pem'), 'rb').read())
cat = json.load(open(os.path.join(here, 'catalogo.json'), encoding='utf-8'))
D = json.load(open(os.path.join(repo, 'datos.json'), encoding='utf-8'))
os.makedirs(os.path.join(repo, 'entrantes'), exist_ok=True); pubs = []
for c in cat:
    data = quitar_descarga(open(os.path.join(src, c['archivo']), 'rb').read())
    e = dict(c); del e['archivo']; e['mb'] = round(len(data) / 1e6, 1); pubs.append(e)
    if 'todas' not in ids and c['id'] not in ids: continue
    if c.get('gratis'):
        open(os.path.join(repo, 'c', c['id'] + '.html'), 'wb').write(data)
    else:
        k = AESGCM.generate_key(256); iv = os.urandom(12)
        w = pub.encrypt(k, padding.OAEP(mgf=padding.MGF1(hashes.SHA256()), algorithm=hashes.SHA256(), label=None))
        open(os.path.join(repo, 'entrantes', c['id'] + '.enc'), 'wb').write(len(w).to_bytes(2, 'big') + w + iv + AESGCM(k).encrypt(iv, data, None))
    print('preparada:', c['id'])
D['clases'] = pubs
json.dump(D, open(os.path.join(repo, 'datos.json'), 'w', encoding='utf-8'), ensure_ascii=False)

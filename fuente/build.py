#!/usr/bin/env python3
"""Construye la plataforma: cifra cada clase con la clave de la semana.
Uso: python3 build.py "CLAVE-DE-LA-SEMANA" [carpeta_clases] [carpeta_salida]
"""
import sys, os, json, base64, shutil, datetime
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

ITER = 150000
here = os.path.dirname(os.path.abspath(__file__))
SIN_DESCARGA = (b'<style>#dl,.dlb{display:none!important}</style>'
    b'<script>document.addEventListener("DOMContentLoaded",function(){'
    b'document.querySelectorAll("button,a").forEach(function(e){if(/Descargar/i.test(e.textContent+(e.title||"")))e.remove()})})</script>')
def quitar_descarga(html):
    i = html.lower().find(b'</head>')
    return html[:i] + SIN_DESCARGA + html[i:] if i >= 0 else SIN_DESCARGA + html

if __name__ == '__main__':
    sys.exit('build.py ya no se usa para cifrar: las clases van con una llave por nivel. Usa agregar_clase.py (o subir_clases.py si existe fuente/publica.pem).')
    clave = sys.argv[1].strip().upper()
    src = sys.argv[2] if len(sys.argv) > 2 else '/mnt/project-files'
    out = sys.argv[3] if len(sys.argv) > 3 else os.path.join(here, 'sitio')

    salt = os.urandom(16)
    key = PBKDF2HMAC(hashes.SHA256(), 32, salt, ITER).derive(clave.encode())
    aes = AESGCM(key)
    b64 = lambda b: base64.b64encode(b).decode()

    if os.path.exists(out): shutil.rmtree(out)
    os.makedirs(os.path.join(out, 'c'))
    cat = json.load(open(os.path.join(here, 'catalogo.json'), encoding='utf-8'))
    pub = []
    for c in cat:
        data = quitar_descarga(open(os.path.join(src, c['archivo']), 'rb').read())
        e = dict(c); del e['archivo']
        if c.get('gratis'):
            open(os.path.join(out, 'c', c['id'] + '.html'), 'wb').write(data)
        else:
            iv = os.urandom(12)
            open(os.path.join(out, 'c', c['id'] + '.bin'), 'wb').write(iv + aes.encrypt(iv, data, None))
        e['mb'] = round(len(data) / 1e6, 1)
        pub.append(e)
    iv = os.urandom(12)
    cfg = {"salt": b64(salt), "iter": ITER, "semana": datetime.date.today().isoformat(),
           "check": b64(iv + aes.encrypt(iv, b"INGENIA-OK", None)), "clases": pub}
    open(os.path.join(out, 'datos.json'), 'w', encoding='utf-8').write(json.dumps(cfg, ensure_ascii=False))
    for f in ('index.html', 'ver.html', 'admin.html', 'fb.js', 'firebase-config.js', 'programa.json'):
        shutil.copy(os.path.join(here, f), os.path.join(out, f))
    for f in os.listdir(os.path.join(here, 'pwa')):
        shutil.copy(os.path.join(here, 'pwa', f), os.path.join(out, f))
    for f in ():
        shutil.copy(os.path.join(here, f), os.path.join(out, f))
    open(os.path.join(out, '.nojekyll'), 'w').close()
    print('Listo:', out, '-', len(pub), 'clases, clave', clave)

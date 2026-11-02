"""Cifrado de clases por nivel (plan): cada nivel tiene su propia llave.
Planes: primaria (INGENIA Kids), teen (bachillerato) y campus (universidad),
y una llave por colegio ("Mi colegio"): col-idea, col-fatima.

Formato de c/<id>.bin (versión 2):
  b'IG2' + n (1 byte) + n entradas [plan (1 byte) + iv (12) + llave de la clase cifrada (48)]
  + iv (12) + clase cifrada con AES-GCM.
La llave de la clase es aleatoria; va cifrada una vez por cada plan que puede abrirla,
con la llave del plan derivada por PBKDF2-SHA256 (salt e iter de datos.json)."""
import os, base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

NIVELES = ['primaria', 'teen', 'campus']
# Colegios: id en datos.json -> plan (documento secreto/<plan> en Firestore). Para un colegio nuevo,
# agrégalo aquí con el siguiente código libre, en fb.js (COLEGIOS) y en ver.html (COD).
COLEGIOS = {'idea': 'col-idea', 'fatima': 'col-fatima'}
PLANES = NIVELES + list(COLEGIOS.values())
COD = {'primaria': 1, 'teen': 2, 'campus': 3, 'col-idea': 4, 'col-fatima': 5}
DE_NIVEL = {'Primaria': 'primaria', 'Bachillerato': 'teen', 'Universidad': 'campus'}
ARCHIVO_LLAVES = '/mnt/project-files/plataforma/llaves-por-nivel.json'  # nunca se sube al repo


def planes_de(niveles, colegios=()):
    p = sorted({DE_NIVEL[n] for n in niveles if n in DE_NIVEL} | {COLEGIOS[c] for c in colegios}, key=COD.get)
    assert p, 'la clase no tiene nivel ni colegio: ' + repr(niveles)
    return p


def planes_clase(c):
    """Planes que abren una clase de datos.json: los de sus niveles y los de sus colegios."""
    return planes_de(c.get('niveles') or [], c.get('colegios') or [])


def derivar(clave, salt, it):
    return AESGCM(PBKDF2HMAC(hashes.SHA256(), 32, salt, it).derive(clave.encode()))


def aes_planes(llaves, D):
    """llaves: {plan: clave} -> {plan: AESGCM}"""
    salt = base64.b64decode(D['salt'])
    return {p: derivar(c, salt, D['iter']) for p, c in llaves.items()}


def cifrar(html, aes, planes):
    k = AESGCM.generate_key(256)
    out = bytearray(b'IG2' + bytes([len(planes)]))
    for p in planes:
        iv = os.urandom(12)
        out += bytes([COD[p]]) + iv + aes[p].encrypt(iv, k, None)
    iv = os.urandom(12)
    return bytes(out) + iv + AESGCM(k).encrypt(iv, html, None)


def descifrar(raw, aes):
    """Prueba las llaves de plan disponibles en aes ({plan: AESGCM})."""
    assert raw[:3] == b'IG2', 'formato viejo'
    n = raw[3]; pos = 4; k = None
    inv = {v: p for p, v in COD.items()}
    for _ in range(n):
        p = inv.get(raw[pos]); iv = raw[pos + 1:pos + 13]; w = raw[pos + 13:pos + 61]; pos += 61
        if k is None and p in aes:
            try: k = aes[p].decrypt(iv, w, None)
            except Exception: pass
    if k is None: raise ValueError('ninguna llave abre esta clase')
    return AESGCM(k).decrypt(raw[pos:pos + 12], raw[pos + 12:], None)


def agregar_planes(raw, aes, planes):
    """Deja que más planes abran una clase ya cifrada, sin tocar la clase: saca su llave con una
    llave que ya la abre y la envuelve también para cada plan nuevo."""
    assert raw[:3] == b'IG2', 'formato viejo'
    n = raw[3]; pos = 4; k = None; tiene = []
    inv = {v: p for p, v in COD.items()}
    for _ in range(n):
        p = inv.get(raw[pos]); iv = raw[pos + 1:pos + 13]; w = raw[pos + 13:pos + 61]; tiene.append(p); pos += 61
        if k is None and p in aes:
            try: k = aes[p].decrypt(iv, w, None)
            except Exception: pass
    if k is None: raise ValueError('ninguna llave abre esta clase')
    nuevos = [p for p in planes if p not in tiene]
    out = bytearray(b'IG2' + bytes([n + len(nuevos)])) + raw[4:pos]
    for p in nuevos:
        iv = os.urandom(12); out += bytes([COD[p]]) + iv + aes[p].encrypt(iv, k, None)
    return bytes(out) + raw[pos:]


def planes_del_archivo(raw):
    inv = {v: p for p, v in COD.items()}
    return [inv[raw[4 + 61 * i]] for i in range(raw[3])]


def checks(aes):
    out = {}
    for p, a in aes.items():
        iv = os.urandom(12); out[p] = base64.b64encode(iv + a.encrypt(iv, b'INGENIA-OK', None)).decode()
    return out


def verificar(aes, D):
    for p, a in aes.items():
        c = base64.b64decode(D['checks'][p])
        assert a.decrypt(c[:12], c[12:], None) == b'INGENIA-OK', 'la llave de ' + p + ' no coincide'

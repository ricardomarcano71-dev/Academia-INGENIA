#!/usr/bin/env python3
"""Agrega (o actualiza) una clase hecha con el motor de clases y la enlaza a su tema del programa.
Uso: python3 fuente/agregar_clase.py REPO ruta/clase.js [--gratis]   (clase en pizarra; también acepta .json del motor viejo)
     Clase de un colegio ("Mi colegio"): en "plataforma" pon "colegio": "idea" y "fecha": "AAAA-MM-DD"
     (o pásalos aquí: --colegio idea --fecha 2026-11-02 [--materia "Cs. Sociales"] [--grado "1.º grado"]).
     Pon también "clase": "repaso" (lo que la maestra explicó) o "tarea" (lo que mandó para la casa).
     Sin "niveles", solo la abren los alumnos de ese colegio; con "niveles", también los de ese nivel.
La clase .json debe traer un bloque "plataforma":
  {"materia": "Matemática", "niveles": ["Primaria"], "grado": "1.º grado", "tipo": "Clase con voz",
   "desc": "...", "programa": ["Primaria", "Matemática", "1.º grado", "Contar, comparar y ordenar hasta 100"]}
y su .html ya armado con motor/build.py al lado (mismo nombre).
- Si el repo ya tiene fuente/publica.pem, cifra con la llave pública (como subir_clases.py) y
  GitHub Actions la pasa a la llave vigente.
- Si no, la cifra con la llave de su nivel (Kids, Teen o Campus), tomada de
  /mnt/project-files/plataforma/llaves-por-nivel.json (nunca se sube al repo).
Nunca sube la clase sin cifrar, salvo con --gratis."""
import sys, os, json, base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
here = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, here)
from build import quitar_descarga
repo, src = sys.argv[1], sys.argv[2]; gratis = '--gratis' in sys.argv
if src.endswith('.js'):  # clase en pizarra: los datos salen de K.finish({...})
    import subprocess
    lib = '/mnt/project-files/clases-programa/pizarra/lib.js'
    C = json.loads(subprocess.check_output(['node', '-e', f"require({json.dumps(lib)});require({json.dumps(os.path.abspath(src))});const L=globalThis.LESSON;console.log(JSON.stringify({{id:L.id,titulo:L.titulo,icono:L.icono,plataforma:L.plataforma}}))"]))
else:
    C = json.load(open(src, encoding='utf-8'))
P = dict(C.get('plataforma') or {}); cid = C['id']
for flag in ('colegio', 'fecha', 'materia', 'grado', 'tipo', 'desc', 'clase'):
    if '--' + flag in sys.argv: P[flag] = sys.argv[sys.argv.index('--' + flag) + 1]
colegios = [P['colegio']] if P.get('colegio') else []
import re
if colegios and not re.fullmatch(r'\d{4}-\d{2}-\d{2}', str(P.get('fecha', ''))): sys.exit('falta la fecha de la clase (AAAA-MM-DD) para Mi colegio')
# si la clase ya estaba en algún colegio, lo conserva (por ejemplo al regrabar una clase de Teen que también es de Fátima)
antes = next((c for c in json.load(open(os.path.join(repo, 'datos.json'), encoding='utf-8'))['clases'] if c['id'] == cid), {})
colegios = list(dict.fromkeys(colegios + antes.get('colegios', [])))
if antes.get('fecha'): P.setdefault('fecha', antes['fecha'])
P.setdefault('niveles', []); P.setdefault('grado', ''); P.setdefault('materia', '')
P.setdefault('desc', C.get('desc') or ''); P.setdefault('tipo', 'Mini clase con voz' if colegios else 'Clase con voz')
html_path = os.path.splitext(src)[0] + '.html'
if not os.path.exists(html_path): html_path = os.path.join(os.path.dirname(os.path.abspath(src)), cid + '.html')
data = quitar_descarga(open(html_path, 'rb').read())
rel = os.path.relpath(os.path.abspath(html_path), '/mnt/project-files')

# 1) archivo de la clase
for ext in ('.html', '.bin'):
    f = os.path.join(repo, 'c', cid + ext)
    if os.path.exists(f): os.remove(f)
if gratis:
    open(os.path.join(repo, 'c', cid + '.html'), 'wb').write(data)
elif os.path.exists(os.path.join(repo, 'fuente', 'publica.pem')):
    pub = serialization.load_pem_public_key(open(os.path.join(repo, 'fuente/publica.pem'), 'rb').read())
    k = AESGCM.generate_key(256); iv = os.urandom(12)
    w = pub.encrypt(k, padding.OAEP(mgf=padding.MGF1(hashes.SHA256()), algorithm=hashes.SHA256(), label=None))
    os.makedirs(os.path.join(repo, 'entrantes'), exist_ok=True)
    open(os.path.join(repo, 'entrantes', cid + '.enc'), 'wb').write(len(w).to_bytes(2, 'big') + w + iv + AESGCM(k).encrypt(iv, data, None))
    print('cifrada con la llave pública: GitHub Actions la activa al hacer push')
else:
    from llaves import ARCHIVO_LLAVES, aes_planes, verificar, cifrar, planes_de, COLEGIOS
    assert all(c in COLEGIOS for c in colegios), 'colegio desconocido: ' + repr(colegios)
    D = json.load(open(os.path.join(repo, 'datos.json'), encoding='utf-8'))
    aes = aes_planes(json.load(open(ARCHIVO_LLAVES)), D); verificar(aes, D)
    open(os.path.join(repo, 'c', cid + '.bin'), 'wb').write(cifrar(data, aes, planes_de(P['niveles'], colegios)))
    print('cifrada para:', ', '.join(planes_de(P['niveles'], colegios)))

# 2) catálogo y datos.json
e = {"id": cid, "titulo": C['titulo'], "desc": P['desc'], "materia": P['materia'], "niveles": P['niveles'],
     "grado": P['grado'], "tipo": P.get('tipo', 'Clase con voz'), "icono": C.get('icono') or '📘'}
if gratis: e['gratis'] = True
if colegios: e['colegios'] = colegios
if P.get('fecha'): e['fecha'] = P['fecha']
if colegios and P.get('clase') in ('repaso', 'tarea'): e['clase'] = P['clase']  # repaso de la clase o tarea para la casa
for path in [os.path.join(here, 'catalogo.json'), '/mnt/project-files/plataforma/catalogo.json']:
    if not os.path.exists(path): continue
    cat = [c for c in json.load(open(path, encoding='utf-8')) if c['id'] != cid]
    cat.append(dict(e, archivo=rel)); json.dump(cat, open(path, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
D = json.load(open(os.path.join(repo, 'datos.json'), encoding='utf-8'))
D['clases'] = [c for c in D['clases'] if c['id'] != cid] + [dict(e, mb=round(len(data) / 1e6, 1))]
json.dump(D, open(os.path.join(repo, 'datos.json'), 'w', encoding='utf-8'), ensure_ascii=False)

# 3) enlazar al tema del programa (las clases solo de un colegio no van en el programa)
if not P.get('programa'):
    print('lista:', cid, '· en Mi colegio:', ', '.join(colegios) or '¿?'); sys.exit(0)
nv, mt, gr, tm = P['programa']; ok = False
for path in [os.path.join(here, 'programa.json'), os.path.join(repo, 'programa.json'), '/mnt/project-files/plataforma/programa.json']:
    if not os.path.exists(path): continue
    PR = json.load(open(path, encoding='utf-8'))
    for N in PR['niveles']:
        for M in N['materias']:
            for G in M['grados']:
                for T in G['temas']:
                    if (N['n'], M['m'], G['g'], T['t']) == (nv, mt, gr, tm):
                        T.setdefault('c', []); ok = True
                        if cid not in T['c']: T['c'].insert(0, cid)
    json.dump(PR, open(path, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('lista:', cid, '· tema enlazado' if ok else '· OJO: no encontré el tema ' + ' | '.join(P['programa']))

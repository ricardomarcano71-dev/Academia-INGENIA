#!/usr/bin/env python3
"""Mantenimiento automático de la plataforma (lo corre GitHub Actions).
  python3 fuente/rotar.py reglas     -> publica fuente/firestore.rules en Firebase
  python3 fuente/rotar.py entrantes  -> cifra con la llave actual las clases nuevas de entrantes/
  python3 fuente/rotar.py rotar      -> crea una llave nueva y vuelve a cifrar todas las clases
Necesita la variable FIREBASE_SA con el JSON de la cuenta de servicio de Firebase."""
import os, sys, json, glob, base64, secrets, datetime, requests
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from google.oauth2 import service_account
import google.auth.transport.requests as gtr

SA = json.loads(os.environ['FIREBASE_SA']); P = SA['project_id']
cred = service_account.Credentials.from_service_account_info(SA, scopes=['https://www.googleapis.com/auth/cloud-platform'])
cred.refresh(gtr.Request()); H = {'Authorization': 'Bearer ' + cred.token}
DOC = f'https://firestore.googleapis.com/v1/projects/{P}/databases/(default)/documents/secreto/clave'
b64 = lambda b: base64.b64encode(b).decode()

def leer_llave():
    r = requests.get(DOC, headers=H); r.raise_for_status(); f = r.json()['fields']
    return f['clave']['stringValue'], f.get('anterior', {}).get('stringValue')
def guardar_llave(nueva, anterior):
    body = {'fields': {'clave': {'stringValue': nueva}, 'anterior': {'stringValue': anterior},
                       'cambiada': {'timestampValue': datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}}}
    requests.patch(DOC, headers=H, json=body).raise_for_status()
def derivar(clave, salt, it): return AESGCM(PBKDF2HMAC(hashes.SHA256(), 32, salt, it).derive(clave.encode()))

def asegurar_publica():
    """Deja en fuente/publica.pem la llave pública de la cuenta de servicio (para recibir clases nuevas cifradas)."""
    priv = serialization.load_pem_private_key(SA['private_key'].encode(), None)
    pem = priv.public_key().public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo)
    if not os.path.exists('fuente/publica.pem') or open('fuente/publica.pem', 'rb').read() != pem:
        open('fuente/publica.pem', 'wb').write(pem); print('publica.pem actualizada')
    return priv

def reglas():
    src = open('fuente/firestore.rules').read()
    base = f'https://firebaserules.googleapis.com/v1/projects/{P}'
    r = requests.post(base + '/rulesets', headers=H, json={'source': {'files': [{'name': 'firestore.rules', 'content': src}]}}); r.raise_for_status()
    rs = r.json()['name']
    rel = f'projects/{P}/releases/cloud.firestore'
    r = requests.patch(f'https://firebaserules.googleapis.com/v1/{rel}', headers=H, json={'release': {'name': rel, 'rulesetName': rs}})
    if r.status_code == 404:
        r = requests.post(base + '/releases', headers=H, json={'name': rel, 'rulesetName': rs})
    r.raise_for_status(); print('reglas publicadas', rs)

def entrantes():
    priv = asegurar_publica(); D = json.load(open('datos.json'))
    clave, _ = leer_llave(); aes = derivar(clave, base64.b64decode(D['salt']), D['iter']); n = 0
    for f in sorted(glob.glob('entrantes/*.enc')):
        raw = open(f, 'rb').read(); L = int.from_bytes(raw[:2], 'big')
        k = priv.decrypt(raw[2:2 + L], padding.OAEP(mgf=padding.MGF1(hashes.SHA256()), algorithm=hashes.SHA256(), label=None))
        rest = raw[2 + L:]; html = AESGCM(k).decrypt(rest[:12], rest[12:], None)
        iv = os.urandom(12); cid = os.path.basename(f)[:-4]
        open(f'c/{cid}.bin', 'wb').write(iv + aes.encrypt(iv, html, None)); os.remove(f); n += 1
        print('clase lista:', cid)
    print(n, 'clases nuevas cifradas')

def rotar():
    D = json.load(open('datos.json')); clave, _ = leer_llave()
    vieja = derivar(clave, base64.b64decode(D['salt']), D['iter'])
    nueva_clave = secrets.token_urlsafe(18).upper(); salt = os.urandom(16)
    nueva = derivar(nueva_clave, salt, D['iter'])
    planos = {}
    for f in sorted(glob.glob('c/*.bin')):
        raw = open(f, 'rb').read(); planos[f] = vieja.decrypt(raw[:12], raw[12:], None)
    # 1) Firebase primero: la página prueba la llave nueva y la anterior, así nadie queda sin acceso
    guardar_llave(nueva_clave, clave)
    for f, html in planos.items():
        iv = os.urandom(12); open(f, 'wb').write(iv + nueva.encrypt(iv, html, None))
    iv = os.urandom(12)
    D['salt'] = b64(salt); D['check'] = b64(iv + nueva.encrypt(iv, b'INGENIA-OK', None))
    D['llave_cambiada'] = datetime.date.today().isoformat()
    json.dump(D, open('datos.json', 'w'), ensure_ascii=False)
    print('llave cambiada;', len(planos), 'clases cifradas de nuevo')

if __name__ == '__main__':
    asegurar_publica()
    for paso in sys.argv[1:]: {'reglas': reglas, 'entrantes': entrantes, 'rotar': rotar}[paso]()

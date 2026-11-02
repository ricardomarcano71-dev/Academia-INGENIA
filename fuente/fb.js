// Conexión con Firebase: inicio de sesión de alumnos y entrega de la llave de las clases.
import { initializeApp } from 'https://www.gstatic.com/firebasejs/10.14.1/firebase-app.js';
import { getAuth, onAuthStateChanged, signInWithEmailAndPassword, signOut } from 'https://www.gstatic.com/firebasejs/10.14.1/firebase-auth.js';
import { getFirestore, doc, getDoc, collection, addDoc, getDocs, query, orderBy, limit, serverTimestamp } from 'https://www.gstatic.com/firebasejs/10.14.1/firebase-firestore.js';
import { firebaseConfig } from './firebase-config.js';

export const app = initializeApp(firebaseConfig);
export const auth = getAuth(app);
export const db = getFirestore(app);
export const DOMINIO = '@alumnos.ingenia.app';
export const correo = u => { u = u.trim().toLowerCase(); return u.includes('@') ? u : u + DOMINIO; };

// Planes (niveles con llave propia): primaria = INGENIA Kids, teen = bachillerato, campus = universidad
export const PLANES = ['primaria', 'teen', 'campus'];
export const NOMBRE_PLAN = { primaria: 'INGENIA Kids (primaria)', teen: 'INGENIA Teen (bachillerato)', campus: 'INGENIA Campus (universidad)' };
export const PLAN_DE_NIVEL = { Primaria: 'primaria', Bachillerato: 'teen', Universidad: 'campus' };
export const planesDeClase = c => [...new Set((c.niveles || []).map(n => PLAN_DE_NIVEL[n]).filter(Boolean))];

// Devuelve {estado:'fuera'|'vencido'|'ok', alumno, planes, llaves:{plan:[clave, anterior]}}
export async function revisar(user) {
  if (!user) return { estado: 'fuera' };
  let alumno = null;
  try { const a = await getDoc(doc(db, 'alumnos', user.uid)); alumno = a.exists() ? a.data() : null; } catch (e) {}
  const planes = (alumno && Array.isArray(alumno.planes)) ? alumno.planes : PLANES, llaves = {};
  await Promise.all(planes.map(async p => {
    try { const s = await getDoc(doc(db, 'secreto', p)); if (s.exists()) { const d = s.data(); llaves[p] = [d.clave, d.anterior].filter(Boolean); } } catch (e) {}
  }));
  if (Object.keys(llaves).length) return { estado: 'ok', alumno, planes, llaves };
  return { estado: 'vencido', alumno, planes };
}
export const listo = () => new Promise(r => { const off = onAuthStateChanged(auth, u => { off(); r(u); }); });
export const entrar = (u, p) => signInWithEmailAndPassword(auth, correo(u), p);
export const salir = () => signOut(auth);

// ---- Registro de accesos y aviso de cuenta compartida ----
export function dispositivo() {
  let d = null;
  try { d = localStorage.getItem('ingenia-disp'); if (!d) { d = Math.random().toString(36).slice(2, 10) + Date.now().toString(36).slice(-4); localStorage.setItem('ingenia-disp', d); } } catch (e) { d = 'sin-almacen'; }
  return d;
}
export function equipo(ua = navigator.userAgent) {
  const so = /Android/i.test(ua) ? 'Android' : /iPhone|iPad/i.test(ua) ? 'iPhone/iPad' : /Windows/i.test(ua) ? 'Windows' : /Mac OS/i.test(ua) ? 'Mac' : /Linux/i.test(ua) ? 'Linux' : 'Otro';
  const nav = /Edg\//.test(ua) ? 'Edge' : /OPR\//.test(ua) ? 'Opera' : /SamsungBrowser/.test(ua) ? 'Samsung' : /Firefox/.test(ua) ? 'Firefox' : /Chrome/.test(ua) ? 'Chrome' : /Safari/.test(ua) ? 'Safari' : 'Navegador';
  return so + ' · ' + nav;
}
async function miIP() {
  try { const c = new AbortController(); setTimeout(() => c.abort(), 3000); return (await (await fetch('https://api.ipify.org?format=json', { signal: c.signal })).json()).ip; } catch (e) { return ''; }
}
export const DIAS_VENTANA = 7, LIMITE_DISP = 3;
// Resume una lista de accesos: dispositivos distintos en los últimos 7 días
export function resumen(accesos) {
  const desde = Date.now() - DIAS_VENTANA * 864e5, disp = new Map(), ips = new Set();
  accesos.forEach(a => { const t = a.t && a.t.toMillis ? a.t.toMillis() : 0; if (t >= desde) { disp.set(a.disp, a.equipo); if (a.ip) ips.add(a.ip); } });
  return { dispositivos: disp.size, equipos: [...disp.values()], ips: ips.size, compartida: disp.size >= LIMITE_DISP };
}
export async function accesosDe(uid, n = 40) {
  const s = await getDocs(query(collection(db, 'alumnos', uid, 'accesos'), orderBy('t', 'desc'), limit(n)));
  return s.docs.map(d => d.data());
}
// Registra el acceso actual y devuelve el resumen (para avisar al alumno)
export async function registrar(user, clase) {
  if (!user) return null;
  try {
    await addDoc(collection(db, 'alumnos', user.uid, 'accesos'), { disp: dispositivo(), equipo: equipo(), ip: await miIP(), clase: clase || '', t: serverTimestamp() });
    return resumen(await accesosDe(user.uid));
  } catch (e) { return null; }
}

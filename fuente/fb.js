// Conexión con Firebase: inicio de sesión de alumnos y entrega de la llave de las clases.
import { initializeApp } from 'https://www.gstatic.com/firebasejs/10.14.1/firebase-app.js';
import { getAuth, onAuthStateChanged, signInWithEmailAndPassword, signOut } from 'https://www.gstatic.com/firebasejs/10.14.1/firebase-auth.js';
import { getFirestore, doc, getDoc } from 'https://www.gstatic.com/firebasejs/10.14.1/firebase-firestore.js';
import { firebaseConfig } from './firebase-config.js';

export const app = initializeApp(firebaseConfig);
export const auth = getAuth(app);
export const db = getFirestore(app);
export const DOMINIO = '@alumnos.ingenia.app';
export const correo = u => { u = u.trim().toLowerCase(); return u.includes('@') ? u : u + DOMINIO; };

// Devuelve {estado:'fuera'|'vencido'|'ok', alumno, clave}
export async function revisar(user) {
  if (!user) return { estado: 'fuera' };
  let alumno = null;
  try { const a = await getDoc(doc(db, 'alumnos', user.uid)); alumno = a.exists() ? a.data() : null; } catch (e) {}
  try {
    const s = await getDoc(doc(db, 'secreto', 'clave'));
    if (s.exists()) return { estado: 'ok', alumno, clave: s.data().clave };
  } catch (e) {}
  return { estado: 'vencido', alumno };
}
export const listo = () => new Promise(r => { const off = onAuthStateChanged(auth, u => { off(); r(u); }); });
export const entrar = (u, p) => signInWithEmailAndPassword(auth, correo(u), p);
export const salir = () => signOut(auth);

"""Genera la narración del video con la voz de Sebastián (Microsoft, es-VE).
Rama temporal: no forma parte de la plataforma."""
import asyncio, json, os, sys
import edge_tts

VOZ = "es-VE-SebastianNeural"
RITMOS = {"r0": "+0%", "r8": "+8%", "r15": "+15%"}
AQUI = os.path.dirname(os.path.abspath(__file__))
SALIDA = os.path.join(AQUI, "audio")


async def una(texto, ritmo, ruta):
    for intento in range(5):
        try:
            await edge_tts.Communicate(texto, VOZ, rate=ritmo).save(ruta)
            if os.path.getsize(ruta) > 1000:
                return
        except Exception as e:  # el servicio falla a veces: reintentar
            print("reintento", intento, os.path.basename(ruta), repr(e)[:120])
        await asyncio.sleep(2 + 2 * intento)
    sys.exit("No se pudo generar " + ruta)


async def main():
    os.makedirs(SALIDA, exist_ok=True)
    guion = json.load(open(os.path.join(AQUI, "guion.json"), encoding="utf-8"))
    for linea in guion:
        for clave, ritmo in RITMOS.items():
            await una(linea["texto"], ritmo, os.path.join(SALIDA, f'{linea["id"]}_{clave}.mp3'))
        print("ok", linea["id"])

asyncio.run(main())

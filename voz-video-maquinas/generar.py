"""Genera la narración con la voz de Sebastián (Microsoft) para los videos de las máquinas."""
import asyncio, json, os, sys
import edge_tts

VOZ = "es-VE-SebastianNeural"
RATE, PITCH = "+5%", "+0Hz"
AQUI = os.path.dirname(os.path.abspath(__file__))
SAL = os.path.join(AQUI, "audio")

async def uno(seg):
    com = edge_tts.Communicate(seg["text"], VOZ, rate=RATE, pitch=PITCH)
    with open(os.path.join(SAL, seg["id"] + ".mp3"), "wb") as f:
        async for ch in com.stream():
            if ch["type"] == "audio":
                f.write(ch["data"])

async def main():
    os.makedirs(SAL, exist_ok=True)
    segs = json.load(open(os.path.join(AQUI, "textos.json"), encoding="utf-8"))
    for seg in segs:
        if os.path.exists(os.path.join(SAL, seg["id"] + ".mp3")):
            continue          # ya generado: no se repite
        for intento in range(5):
            try:
                await uno(seg)
                if os.path.getsize(os.path.join(SAL, seg["id"] + ".mp3")) > 2000:
                    print("ok", seg["id"]); break
                raise RuntimeError("audio vacío")
            except Exception as e:
                print("reintento", seg["id"], e); await asyncio.sleep(6)
        else:
            sys.exit("No se pudo generar " + seg["id"])

asyncio.run(main())

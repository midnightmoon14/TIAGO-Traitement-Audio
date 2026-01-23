# Script pour tester et calibrer le seuil de volume du micro
import pyaudio
import numpy as np
import time

def test_volume_threshold():
    """Teste le volume du micro pour trouver le bon seuil"""
    pa = pyaudio.PyAudio()
    samplerate = 16000
    chunk = 1024
    
    print("🎤 Test du volume du micro")
    print("Parlez normalement pour voir le volume détecté")
    print("Appuyez sur Ctrl+C pour arrêter\n")
    
    stream = pa.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=samplerate,
        input=True,
        frames_per_buffer=chunk,
    )
    
    try:
        while True:
            frames = []
            for _ in range(int(samplerate / chunk * 0.5)):  # 0.5 seconde
                frames.append(stream.read(chunk, exception_on_overflow=False))
            
            audio_i16 = np.frombuffer(b"".join(frames), dtype=np.int16)
            volume = np.abs(audio_i16).mean()
            
            # Barre de volume visuelle
            bar_length = int(volume / 50)
            bar = "█" * min(bar_length, 50)
            
            status = "🔊 PAROLE" if volume > 300 else "🔇 SILENCE"
            print(f"\r{status} | Volume: {volume:6.0f} | {bar}", end="", flush=True)
            
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\n\n✅ Test terminé")
        print("\n💡 Conseil: Si le volume reste toujours en dessous de 300 quand vous parlez,")
        print("   augmentez le volume_threshold dans STT.__init__()")
        print("   Si le volume monte trop même en silence, diminuez-le")
    finally:
        stream.stop_stream()
        stream.close()
        pa.terminate()

if __name__ == "__main__":
    test_volume_threshold()

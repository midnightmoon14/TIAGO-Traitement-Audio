# Script de test simple pour vérifier la détection du wake word
from stt import STT
from main import is_wake

print("🧪 Test de détection du wake word")
print("=" * 50)

# Test de la fonction is_wake
test_cases = [
    "bonjour tiago",
    "salut tiago",
    "hey tiago",
    "bonjour tiago comment ça va",
    "tiago bonjour",
    "bonjour",
    "tiago",
    "bonjour je m'appelle tiago",
]

print("\n📝 Tests de la fonction is_wake():")
for test in test_cases:
    result = is_wake(test)
    status = "✅" if result else "❌"
    print(f"{status} '{test}' -> {result}")

print("\n" + "=" * 50)
print("🎤 Test avec le micro (appuyez sur Ctrl+C pour arrêter)")
print("Dites 'Bonjour Tiago' pour tester la détection\n")

stt = STT(model_size="small", device="cpu", compute_type="int8")

try:
    while True:
        print("🎤 Écoute...")
        heard = stt.listen(seconds=3.0)
        
        if heard:
            print(f"📢 Entendu: '{heard}'")
            if is_wake(heard):
                print("✅ WAKE WORD DÉTECTÉ !")
            else:
                print("❌ Pas un wake word")
        else:
            print("🔇 Silence ou volume trop faible")
        print()
except KeyboardInterrupt:
    print("\n✅ Test terminé")

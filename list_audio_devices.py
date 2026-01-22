import sounddevice as sd

print(sd.query_devices())
print("\nDEFAULT INPUT:", sd.default.device[0])
print("DEFAULT OUTPUT:", sd.default.device[1])

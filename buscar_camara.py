"""
============================================================
 BUSCAR CAMARA  ·  Torreta autonoma
------------------------------------------------------------
 Correlo UNA vez para saber que numero tiene tu webcam USB.
 Anota el numero y ponlo en deteccion_cara.py
============================================================
"""

import platform

import cv2

# Calla los warnings internos de OpenCV al buscar camaras que no existen
cv2.utils.logging.setLogLevel(cv2.utils.logging.LOG_LEVEL_SILENT)

# En Windows, DSHOW abre las camaras mucho mas rapido.
# En Mac/Linux se usa el backend por defecto.
BACKEND = cv2.CAP_DSHOW if platform.system() == "Windows" else cv2.CAP_ANY

print("\nBuscando camaras conectadas... (tarda unos segundos)\n")

encontradas = []

for i in range(5):
    cap = cv2.VideoCapture(i, BACKEND)
    if cap.isOpened():
        ret, frame = cap.read()
        if ret:
            alto, ancho = frame.shape[:2]
            encontradas.append(i)
            print(f"   [OK]  Camara {i}   {ancho}x{alto}")
    cap.release()

if not encontradas:
    print("   [X]  No se encontro ninguna camara.")
    print("\n   Revisa que la webcam este bien conectada al USB")
    print("   y que ningun otro programa (Zoom, Teams) la este usando.\n")
    raise SystemExit

print(f"\nSe encontraron {len(encontradas)} camara(s).")
print("Ahora te muestro cada una para que veas cual es cual.")
print("Presiona Q para pasar a la siguiente.\n")

for i in encontradas:
    cap = cv2.VideoCapture(i, BACKEND)
    print(f"   Mostrando camara {i} ...")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        cv2.putText(
            frame,
            f"CAMARA {i}  -  presiona Q",
            (15, 35),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 0),
            2,
        )
        cv2.imshow("Buscando camara", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()

cv2.destroyAllWindows()

print("\n------------------------------------------------------------")
print(" Anota el numero de tu webcam USB (la nueva, no la del laptop)")
print(" y ponlo en la linea NUMERO_CAMARA de deteccion_cara.py")
print("------------------------------------------------------------\n")
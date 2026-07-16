"""
TORRETA - TRACKER FINAL
Detecta caras y manda el ERROR al ESP32 (no angulos absolutos).
"""

import os
import time
import platform
import urllib.request

import cv2
import serial

# ==================== CONFIGURACION ====================
PUERTO   = "COM5"        # el puerto de tu ESP32
BAUDIOS  = 115200

NUMERO_CAMARA = 0
ESPEJO = True

ESCALA_DETECCION = 0.5
VECINOS_MINIMOS  = 6
CARA_MINIMA      = 70

RESPUESTA   = 0.35       # suavizado del blanco
ZONA_MUERTA = 35         # px para considerar "centrado"

INTERVALO_ENVIO = 0.04   # 40ms = 25 envios/seg (throttling)
# =======================================================

cv2.utils.logging.setLogLevel(cv2.utils.logging.LOG_LEVEL_SILENT)

VERDE, ROJO, GRIS, AMARILLO = (0,255,0), (0,0,255), (130,130,130), (0,200,255)

ARCHIVO = "haarcascade_frontalface_default.xml"
URL = ("https://raw.githubusercontent.com/opencv/opencv/4.x/"
       "data/haarcascades/haarcascade_frontalface_default.xml")

def encontrar_cascade():
    carpeta = os.path.dirname(os.path.abspath(__file__))
    local = os.path.join(carpeta, ARCHIVO)
    if os.path.exists(local):
        return local
    try:
        ruta = cv2.data.haarcascades + ARCHIVO
        if os.path.exists(ruta):
            return ruta
    except AttributeError:
        pass
    print("Descargando el detector...")
    urllib.request.urlretrieve(URL, local)
    return local

detector = cv2.CascadeClassifier(encontrar_cascade())
if detector.empty():
    print("No cargo el detector."); raise SystemExit

# ---- Conectar al ESP32 ----
esp32 = None
try:
    esp32 = serial.Serial(PUERTO, BAUDIOS, timeout=0)
    time.sleep(2)          # el ESP32 se reinicia al abrir el puerto
    print(f"ESP32 conectado en {PUERTO}")
except Exception as e:
    print(f"\nNo se pudo abrir {PUERTO}: {e}")
    print("  - Cierra el Monitor Serie de Arduino")
    print("  - Revisa el puerto en el Administrador de dispositivos")
    print("  - Sigo SIN mandar datos (modo solo vision)\n")

BACKEND = cv2.CAP_DSHOW if platform.system() == "Windows" else cv2.CAP_ANY
cap = cv2.VideoCapture(NUMERO_CAMARA, BACKEND)
if not cap.isOpened():
    print(f"No abrio la camara {NUMERO_CAMARA}"); raise SystemExit

print("Corriendo. Q para salir.\n")

blanco_x = blanco_y = None
ultimo_envio = 0.0
tiempo_previo = time.time()
fps = 0.0
cara_min_chica = max(20, int(CARA_MINIMA * ESCALA_DETECCION))

while True:
    ret, frame = cap.read()
    if not ret:
        break
    if ESPEJO:
        frame = cv2.flip(frame, 1)

    alto, ancho = frame.shape[:2]
    cx, cy = ancho // 2, alto // 2

    gris = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    chico = cv2.equalizeHist(cv2.resize(gris, None,
                fx=ESCALA_DETECCION, fy=ESCALA_DETECCION))

    det = detector.detectMultiScale(chico, scaleFactor=1.1,
            minNeighbors=VECINOS_MINIMOS,
            minSize=(cara_min_chica, cara_min_chica))

    caras = [(int(x/ESCALA_DETECCION), int(y/ESCALA_DETECCION),
              int(w/ESCALA_DETECCION), int(h/ESCALA_DETECCION))
             for (x, y, w, h) in det]

    # mira + zona muerta
    cv2.line(frame, (cx-15, cy), (cx+15, cy), GRIS, 1)
    cv2.line(frame, (cx, cy-15), (cx, cy+15), GRIS, 1)
    cv2.rectangle(frame, (cx-ZONA_MUERTA, cy-ZONA_MUERTA),
                  (cx+ZONA_MUERTA, cy+ZONA_MUERTA), GRIS, 1)

    hay_blanco = len(caras) > 0
    centrado = False
    error_x = error_y = 0

    if hay_blanco:
        i = max(range(len(caras)), key=lambda k: caras[k][2]*caras[k][3])
        for k, (x, y, w, h) in enumerate(caras):
            cv2.rectangle(frame, (x, y), (x+w, y+h),
                          VERDE if k == i else GRIS, 2 if k == i else 1)

        x, y, w, h = caras[i]
        mx, my = x + w//2, y + h//2

        if blanco_x is None:
            blanco_x, blanco_y = float(mx), float(my)
        else:
            blanco_x = (1-RESPUESTA)*blanco_x + RESPUESTA*mx
            blanco_y = (1-RESPUESTA)*blanco_y + RESPUESTA*my

        bx, by = int(blanco_x), int(blanco_y)
        cv2.circle(frame, (mx, my), 3, AMARILLO, -1)
        cv2.circle(frame, (bx, by), 6, ROJO, -1)
        cv2.line(frame, (cx, cy), (bx, by), ROJO, 1)

        error_x, error_y = bx - cx, by - cy
        centrado = abs(error_x) < ZONA_MUERTA and abs(error_y) < ZONA_MUERTA
    else:
        blanco_x = blanco_y = None

    # ---- ENVIO AL ESP32 (throttled) ----
    ahora = time.time()
    if esp32 and ahora - ultimo_envio >= INTERVALO_ENVIO:
        ultimo_envio = ahora
        try:
            if hay_blanco:
                esp32.write(f"T,{error_x},{error_y}\n".encode())
            else:
                esp32.write(b"N\n")
        except Exception as e:
            print("Se perdio el serial:", e)
            esp32 = None

    if centrado:
        cv2.rectangle(frame, (cx-ZONA_MUERTA, cy-ZONA_MUERTA),
                      (cx+ZONA_MUERTA, cy+ZONA_MUERTA), VERDE, 2)
        estado, color = "CENTRADO", VERDE
    elif hay_blanco:
        estado, color = "APUNTANDO", AMARILLO
    else:
        estado, color = "BUSCANDO", GRIS

    cv2.putText(frame, estado, (15, alto-50),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
    cv2.putText(frame, f"error X:{error_x:+5d} Y:{error_y:+5d}",
                (15, alto-20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

    fps = 0.9*fps + 0.1*(1.0/max(ahora - tiempo_previo, 1e-6))
    tiempo_previo = ahora
    link = "ESP32 OK" if esp32 else "SIN ESP32"
    cv2.putText(frame, f"{fps:4.0f} FPS | {link}", (15, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, VERDE, 2)

    cv2.imshow("Torreta (Q para salir)", frame)
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

if esp32:
    esp32.write(b"N\n")
    esp32.close()
cap.release()
cv2.destroyAllWindows()
print("Cerrado.\n")
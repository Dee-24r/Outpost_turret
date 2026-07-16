"""
============================================================
 FASE 1 v2  ·  DETECCION DE CARAS  ·  Torreta autonoma
------------------------------------------------------------
 Mejoras sobre la v1:
   1. Detecta en imagen reducida  -> mas FPS
   2. Suavizado del blanco        -> los servos no van a temblar
   3. Zona muerta                 -> avisa cuando ya esta centrado
   4. Menos falsos positivos      -> ajustable

 Presiona Q para salir.
============================================================
"""

import os
import platform
import time
import urllib.request

import cv2

cv2.utils.logging.setLogLevel(cv2.utils.logging.LOG_LEVEL_SILENT)


# ==================== CONFIGURACION ====================

NUMERO_CAMARA = 0

ESPEJO = True

# --- VELOCIDAD ---
# Detecta en una imagen mas chica. La imagen que ves NO cambia.
#   1.0 = tamano completo (lento)
#   0.5 = mitad (como 3x mas rapido)  <- recomendado
#   0.35 = mas rapido pero se le escapan caras lejanas
ESCALA_DETECCION = 0.5

# --- FALSOS POSITIVOS ---
# Que tantos "votos" necesita algo para contar como cara.
#   Subelo (7, 8) si detecta paredes o cosas que no son caras.
#   Bajalo (3, 4) si no te detecta a ti.
VECINOS_MINIMOS = 6

# Cara mas chica que cuenta, en pixeles de la imagen real.
CARA_MINIMA = 70

# --- SUAVIZADO ---
# Que tanto se pega el blanco a la medicion nueva.
#   0.15 = muy suave, responde lento
#   0.35 = balanceado           <- recomendado
#   1.00 = sin suavizado, brinca (como la v1)
RESPUESTA = 0.35

# --- ZONA MUERTA ---
# Si el blanco esta a menos de estos pixeles del centro,
# se considera CENTRADO. La torreta dejaria de corregir aqui.
ZONA_MUERTA = 35

# =======================================================


BACKEND = cv2.CAP_DSHOW if platform.system() == "Windows" else cv2.CAP_ANY

VERDE = (0, 255, 0)
ROJO = (0, 0, 255)
GRIS = (130, 130, 130)
AMARILLO = (0, 200, 255)

ARCHIVO_CASCADE = "haarcascade_frontalface_default.xml"
URL_CASCADE = (
    "https://raw.githubusercontent.com/opencv/opencv/4.x/"
    "data/haarcascades/haarcascade_frontalface_default.xml"
)


def encontrar_cascade():
    """Busca el XML del detector en 3 lugares. Si no esta, lo descarga."""
    carpeta = os.path.dirname(os.path.abspath(__file__))
    local = os.path.join(carpeta, ARCHIVO_CASCADE)

    if os.path.exists(local):
        return local

    try:
        de_opencv = cv2.data.haarcascades + ARCHIVO_CASCADE
        if os.path.exists(de_opencv):
            return de_opencv
    except AttributeError:
        pass

    print(f"No encontre {ARCHIVO_CASCADE}. Descargandolo de GitHub...")
    try:
        urllib.request.urlretrieve(URL_CASCADE, local)
        print(f"Listo. Guardado en:\n   {local}\n")
        return local
    except Exception as e:
        print(f"\nNo se pudo descargar: {e}")
        print(f"\n>> Bajalo a mano de:\n   {URL_CASCADE}")
        print(f">> Y ponlo en:\n   {carpeta}\n")
        return None


ruta_cascade = encontrar_cascade()
if ruta_cascade is None:
    raise SystemExit

detector = cv2.CascadeClassifier(ruta_cascade)
if detector.empty():
    print(f"El archivo existe pero no cargo:\n   {ruta_cascade}")
    print("Borralo y vuelve a correr esto.")
    raise SystemExit

cap = cv2.VideoCapture(NUMERO_CAMARA, BACKEND)
if not cap.isOpened():
    print(f"No se pudo abrir la camara {NUMERO_CAMARA}.")
    print("Corre buscar_camara.py para ver que numeros hay.")
    raise SystemExit

print("\nDetectando. Presiona Q para salir.\n")

# El blanco suavizado. None = todavia no hay.
blanco_x = None
blanco_y = None

tiempo_previo = time.time()
fps = 0.0

# La cara minima medida en la imagen REDUCIDA
cara_minima_chica = max(20, int(CARA_MINIMA * ESCALA_DETECCION))

while True:
    ret, frame = cap.read()
    if not ret:
        print("Se perdio la imagen de la camara.")
        break

    if ESPEJO:
        frame = cv2.flip(frame, 1)

    alto, ancho = frame.shape[:2]
    centro_x = ancho // 2
    centro_y = alto // 2

    # ---- DETECCION EN IMAGEN REDUCIDA (aqui esta la ganancia de FPS) ----
    gris = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    chico = cv2.resize(gris, None, fx=ESCALA_DETECCION, fy=ESCALA_DETECCION)

    # Ecualizar ayuda cuando hay poca luz o contraluz
    chico = cv2.equalizeHist(chico)

    detecciones = detector.detectMultiScale(
        chico,
        scaleFactor=1.1,
        minNeighbors=VECINOS_MINIMOS,
        minSize=(cara_minima_chica, cara_minima_chica),
    )

    # Regresar las coordenadas al tamano real
    caras = []
    for x, y, w, h in detecciones:
        caras.append(
            (
                int(x / ESCALA_DETECCION),
                int(y / ESCALA_DETECCION),
                int(w / ESCALA_DETECCION),
                int(h / ESCALA_DETECCION),
            )
        )

    # ---- CRUZ DEL CENTRO + ZONA MUERTA ----
    cv2.line(frame, (centro_x - 15, centro_y), (centro_x + 15, centro_y), GRIS, 1)
    cv2.line(frame, (centro_x, centro_y - 15), (centro_x, centro_y + 15), GRIS, 1)
    cv2.rectangle(
        frame,
        (centro_x - ZONA_MUERTA, centro_y - ZONA_MUERTA),
        (centro_x + ZONA_MUERTA, centro_y + ZONA_MUERTA),
        GRIS,
        1,
    )

    centrado = False

    if len(caras) > 0:
        # La cara mas grande = la persona mas cercana = el blanco
        idx = max(range(len(caras)), key=lambda k: caras[k][2] * caras[k][3])

        for k, (x, y, w, h) in enumerate(caras):
            if k == idx:
                cv2.rectangle(frame, (x, y), (x + w, y + h), VERDE, 2)
            else:
                cv2.rectangle(frame, (x, y), (x + w, y + h), GRIS, 1)

        x, y, w, h = caras[idx]
        medido_x = x + w // 2
        medido_y = y + h // 2

        # ---- SUAVIZADO (esto evita que los servos tiemblen) ----
        if blanco_x is None:
            blanco_x, blanco_y = float(medido_x), float(medido_y)
        else:
            blanco_x = (1 - RESPUESTA) * blanco_x + RESPUESTA * medido_x
            blanco_y = (1 - RESPUESTA) * blanco_y + RESPUESTA * medido_y

        bx, by = int(blanco_x), int(blanco_y)

        # Punto amarillo = medicion cruda (brinca)
        cv2.circle(frame, (medido_x, medido_y), 3, AMARILLO, -1)
        # Punto rojo = blanco suavizado (esto seguiria la torreta)
        cv2.circle(frame, (bx, by), 6, ROJO, -1)
        cv2.line(frame, (centro_x, centro_y), (bx, by), ROJO, 1)

        error_x = bx - centro_x
        error_y = by - centro_y

        centrado = abs(error_x) < ZONA_MUERTA and abs(error_y) < ZONA_MUERTA

        etiqueta = f"error  X:{error_x:+5d}   Y:{error_y:+5d}"
        color_etiqueta = VERDE if centrado else ROJO
    else:
        # Sin blanco: olvida la posicion anterior
        blanco_x = None
        blanco_y = None
        etiqueta = "sin blanco"
        color_etiqueta = GRIS

    # ---- ESTADO (esto es la logica de disparo de la Fase 6) ----
    if centrado:
        cv2.rectangle(
            frame,
            (centro_x - ZONA_MUERTA, centro_y - ZONA_MUERTA),
            (centro_x + ZONA_MUERTA, centro_y + ZONA_MUERTA),
            VERDE,
            2,
        )
        estado = "CENTRADO"
        color_estado = VERDE
    elif len(caras) > 0:
        estado = "APUNTANDO"
        color_estado = AMARILLO
    else:
        estado = "BUSCANDO"
        color_estado = GRIS

    cv2.putText(
        frame, estado, (15, alto - 50),
        cv2.FONT_HERSHEY_SIMPLEX, 0.7, color_estado, 2,
    )
    cv2.putText(
        frame, etiqueta, (15, alto - 20),
        cv2.FONT_HERSHEY_SIMPLEX, 0.6, color_etiqueta, 2,
    )

    ahora = time.time()
    fps = 0.9 * fps + 0.1 * (1.0 / max(ahora - tiempo_previo, 1e-6))
    tiempo_previo = ahora

    cv2.putText(
        frame, f"{fps:4.0f} FPS   |   {len(caras)} cara(s)", (15, 30),
        cv2.FONT_HERSHEY_SIMPLEX, 0.6, VERDE, 2,
    )

    cv2.imshow("Fase 1 v2 - deteccion (Q para salir)", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
print("Cerrado.\n")
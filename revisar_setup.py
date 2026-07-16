"""
============================================================
 REVISAR SETUP  ·  Torreta autonoma
------------------------------------------------------------
 Corre ESTE archivo primero si algo no jala.
 Te dice exactamente que falta y como arreglarlo.
============================================================
"""

import sys

print()
print("=" * 62)
print(" REVISION DE SETUP   ·   Torreta autonoma")
print("=" * 62)

problemas = []


# ---------- 1. QUE PYTHON ESTA CORRIENDO ESTO ----------
print("\n[1]  PYTHON")
v = sys.version_info
print(f"     Version:   {v.major}.{v.minor}.{v.micro}")
print(f"     Ruta:      {sys.executable}")

if v.major == 3 and 8 <= v.minor <= 13:
    print("     Estado:    OK")
else:
    print(f"     Estado:    OJO - Python {v.major}.{v.minor} puede dar problemas")
    print("                Si OpenCV falla abajo, cambia el interprete")
    print("                de VS Code (abajo a la derecha) a Python 3.12")


# ---------- 2. OPENCV ----------
print("\n[2]  OPENCV")
cv2 = None
try:
    import cv2  # noqa: E402

    # Calla los warnings internos de OpenCV al buscar camaras que no existen
    cv2.utils.logging.setLogLevel(cv2.utils.logging.LOG_LEVEL_SILENT)

    print(f"     Version:   {cv2.__version__}")
    print(f"     Ruta:      {cv2.__file__}")
    print("     Estado:    OK")
except ImportError as e:
    print("     Estado:    NO INSTALADO en este Python")
    print(f"     Error:     {e}")
    print()
    print("     >> COMO ARREGLARLO:")
    print("        Este Python no tiene OpenCV, pero puede que OTRO si.")
    print()
    print("        Opcion A (la mas rapida):")
    print("          Abajo a la derecha en VS Code, dale click a la version")
    print("          de Python y elige la 3.12. Vuelve a correr esto.")
    print()
    print("        Opcion B (instalarlo en ESTE Python):")
    print(f'          "{sys.executable}" -m pip install opencv-python')
    problemas.append("OpenCV no esta en este Python")


# ---------- 3. NUMPY ----------
print("\n[3]  NUMPY")
try:
    import numpy  # noqa: E402

    print(f"     Version:   {numpy.__version__}")
    print("     Estado:    OK")
except ImportError:
    print("     Estado:    NO INSTALADO")
    print("     >> Se instala solo junto con OpenCV. Arregla el paso [2].")
    problemas.append("numpy no esta instalado")


# ---------- 4. DETECTOR DE CARAS ----------
print("\n[4]  DETECTOR DE CARAS (Haar Cascade)")
if cv2 is None:
    print("     Estado:    NO SE PUDO REVISAR (falta OpenCV)")
elif not hasattr(cv2, "CascadeClassifier"):
    print("     Estado:    NO EXISTE en esta version de OpenCV")
    print(f"     Tu OpenCV: {cv2.__version__}")
    print()
    print("     >> CAUSA:")
    print("        OpenCV 5 (junio 2026) movio los Haar Cascades al")
    print("        paquete 'contrib'. Ya no vienen en opencv-python.")
    print()
    print("     >> ARREGLO (2 comandos):")
    print("        pip uninstall opencv-python -y")
    print("        pip install opencv-contrib-python")
    problemas.append("Falta CascadeClassifier -> instala opencv-contrib-python")
else:
    ruta = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    detector = cv2.CascadeClassifier(ruta)
    if detector.empty():
        print("     Estado:    NO SE PUDO CARGAR")
        print(f"     Buscando:  {ruta}")
        print("     >> Reinstala: pip install --upgrade opencv-python")
        problemas.append("El detector de caras no carga")
    else:
        print(f"     Ruta:      {ruta}")
        print("     Estado:    OK")


# ---------- 5. CAMARAS ----------
print("\n[5]  CAMARAS")
if cv2 is None:
    print("     Estado:    NO SE PUDO REVISAR (falta OpenCV)")
else:
    import platform  # noqa: E402

    backend = cv2.CAP_DSHOW if platform.system() == "Windows" else cv2.CAP_ANY

    print("     Buscando... (tarda unos segundos)")
    encontradas = []
    for i in range(5):
        cap = cv2.VideoCapture(i, backend)
        if cap.isOpened():
            ret, frame = cap.read()
            if ret:
                alto, ancho = frame.shape[:2]
                encontradas.append(i)
                print(f"       Camara {i}   {ancho}x{alto}")
        cap.release()

    if encontradas:
        print(f"     Estado:    OK  -  {len(encontradas)} camara(s)")
        print(f"     >> Numeros disponibles: {encontradas}")
        print("        Corre buscar_camara.py para ver cual es cual.")
    else:
        print("     Estado:    NINGUNA CAMARA")
        print("     >> Revisa que la webcam este conectada al USB y que")
        print("        ningun otro programa (Zoom, Teams) la este usando.")
        problemas.append("No se detecto ninguna camara")


# ---------- RESUMEN ----------
print("\n" + "=" * 62)
if problemas:
    print(f" FALTAN {len(problemas)} COSA(S):")
    for p in problemas:
        print(f"   -  {p}")
    print("\n Arregla lo de arriba y vuelve a correr este archivo.")
else:
    print(" TODO LISTO. Ya puedes correr buscar_camara.py")
print("=" * 62)
print()
Safe setup notes for the vision side of the project.

This repo contains Python scripts for camera discovery and face detection.
Use them to verify the webcam, OpenCV, and face-tracking display before you connect any motion or trigger hardware.

## What you need

- Python 3.12 or 3.13
- OpenCV with Haar cascade support
- A USB webcam

## Install OpenCV

If OpenCV is missing, install it in the active Python environment:

```powershell
python -m pip install opencv-contrib-python
```

## Test order

1. Run `revisar_setup.py` to check Python, OpenCV, and camera access.
2. Run `buscar_camara.py` to find the webcam index.
3. Update `NUMERO_CAMARA` in `deteccion_cara_v2.py` if needed.
4. Run `deteccion_cara_v2.py` and confirm the green face box and status text appear.

## Expected results

- `revisar_setup.py` should report OpenCV as installed.
- `buscar_camara.py` should list at least one camera.
- `deteccion_cara_v2.py` should show a live preview and detect a face when one is visible.

If `cv2` still fails to import, make sure VS Code is using the same Python interpreter where OpenCV was installed.
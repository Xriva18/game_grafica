# config.py
import numpy as np

# Configuración de pantalla y OpenGL
DISPLAY_WIDTH = 800
DISPLAY_HEIGHT = 600
FOV = 45
NEAR_PLANE = 0.1
FAR_PLANE = 1000.0

# Física y velocidad
GRAVITY = 0.01
JUMP_SPEED = 0.3
BASE_SPEED = 0.07

# Escalas
CUBE_SCALE = 1.0       # Escala del cubo (jugador)
PYRAMID_SCALE = 0.5    # Escala de la pirámide (obstáculo)
MINI_SCALE = 0.5       # Escala para los fragmentos

# Límite para dibujar el piso
FLOOR_LIMIT = 200

# Offset de cámara por defecto (relativo al jugador)
CAMERA_OFFSET = np.array([-15, 5, -20], dtype=float)

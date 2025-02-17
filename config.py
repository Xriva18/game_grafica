# config.py
# Este archivo contiene constantes y configuraciones globales usadas en el proyecto.
import numpy as np

# Configuración de pantalla y parámetros de proyección OpenGL
DISPLAY_WIDTH = 800
DISPLAY_HEIGHT = 600
FOV = 45             # Campo de visión (en grados) para la proyección en perspectiva.
NEAR_PLANE = 0.1     # Distancia al plano cercano.
FAR_PLANE = 1000.0   # Distancia al plano lejano.

# Parámetros de física y velocidad del juego
GRAVITY = 0.01       # Valor de la aceleración gravitacional (para los saltos y la animación de explosión).
JUMP_SPEED = 0.3     # Velocidad inicial al saltar.
BASE_SPEED = 0.07    # Velocidad base del jugador (que se incrementará con la puntuación).

# Escalas para los modelos
CUBE_SCALE = 1.0       # Escala del cubo (jugador)
PYRAMID_SCALE = 0.5    # Escala de la pirámide (obstáculo)
MINI_SCALE = 0.5       # Escala para los fragmentos (mini cubos) resultantes de la explosión del cubo

# Límite para dibujar el piso (se usa para limitar las líneas del fondo)
FLOOR_LIMIT = 200

# Offset de cámara por defecto (relativo al jugador)
CAMERA_OFFSET = np.array([-15, 5, -20], dtype=float)

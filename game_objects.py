# game_objects.py
"""
Este módulo contiene las definiciones de los objetos del juego:
- El cubo (jugador)
- La pirámide (obstáculo)
- El mini cubo (fragmento) para la animación de explosión
- Las clases básicas: GameObject, Player, Obstacle, Fragment
- La función create_fragments_from_player que genera fragmentos a partir del cubo
"""

import numpy as np
import math, random
from render_utils import rotation_z
from config import CUBE_SCALE, PYRAMID_SCALE, MINI_SCALE

# --- Definiciones para el cubo (jugador) ---
cube_vertices = [
    np.array([-0.5, -0.5, -0.5]) * CUBE_SCALE,
    np.array([ 0.5, -0.5, -0.5]) * CUBE_SCALE,
    np.array([ 0.5,  0.5, -0.5]) * CUBE_SCALE,
    np.array([-0.5,  0.5, -0.5]) * CUBE_SCALE,
    np.array([-0.5, -0.5,  0.5]) * CUBE_SCALE,
    np.array([ 0.5, -0.5,  0.5]) * CUBE_SCALE,
    np.array([ 0.5,  0.5,  0.5]) * CUBE_SCALE,
    np.array([-0.5,  0.5,  0.5]) * CUBE_SCALE
]
cube_triangles = [
    (0,1,2), (0,2,3),
    (4,6,5), (4,7,6),
    (4,5,1), (4,1,0),
    (5,6,2), (5,2,1),
    (6,7,3), (6,3,2),
    (7,4,0), (7,0,3)
]
# El pivot_offset se usa para trasladar el cubo de modo que su base (y=-0.5) quede en y=0.
cube_pivot_offset = np.array([0, 0.5, 0], dtype=float)

# --- Definiciones para la pirámide (obstáculo) ---
pyramid_vertices = [
    np.array([0, 1, 0]) * PYRAMID_SCALE,       # Vértice superior (apex)
    np.array([-1, -1, 1]) * PYRAMID_SCALE,
    np.array([1, -1, 1]) * PYRAMID_SCALE,
    np.array([1, -1, -1]) * PYRAMID_SCALE,
    np.array([-1, -1, -1]) * PYRAMID_SCALE
]
pyramid_triangles = [
    (0,1,2), (0,2,3), (0,3,4), (0,4,1),
    (1,2,3), (1,3,4)
]
# Ajuste para que la base de la pirámide quede en y=0
pyramid_pivot_offset = np.array([0, 0.5, 0], dtype=float)

# --- Definiciones para el mini cubo (fragmentos de explosión) ---
mini_cube_vertices = [v * MINI_SCALE for v in cube_vertices]
mini_cube_triangles = cube_triangles[:]  # Se usan los mismos triángulos
mini_cube_pivot_offset = np.array([0, 0.5*MINI_SCALE, 0], dtype=float)

# Clase base para objetos del juego
class GameObject:
    def __init__(self, base_vertices, triangles, pos, pivot_offset):
        self.base_vertices = base_vertices      # Lista de vértices en espacio local
        self.triangles = triangles              # Lista de triángulos (índices)
        self.pos = np.array(pos, dtype=float)   # Posición en espacio mundial
        self.pivot_offset = pivot_offset.copy() # Offset para ajustar el pivot (por ejemplo, para que la base quede en y=0)
        self.rotation_z = 0.0                   # Ángulo de rotación alrededor del eje Z

    def get_transformed_vertices(self):
        """
        Aplica la transformación al objeto: rotación (matriz de rotación),
        traslación (suma de la posición) y el pivot offset.
        
        Fórmula: v_world = R * (v_local + pivot_offset) + pos
        donde R es la matriz de rotación obtenida de rotation_z.
        """
        R = rotation_z(self.rotation_z)
        transformed = []
        for v in self.base_vertices:
            local = np.dot(R, (v + self.pivot_offset))
            world = local + self.pos
            transformed.append(world)
        return transformed

# Clase Player (jugador) basada en GameObject
class Player(GameObject):
    def __init__(self, pos):
        super().__init__(cube_vertices, cube_triangles, pos, cube_pivot_offset)
        self.vel_y = 0.0      # Velocidad en el eje Y para saltos y gravedad
        self.on_ground = True # Bandera que indica si el jugador está en el suelo

# Clase Obstacle (obstáculo, pirámide)
class Obstacle(GameObject):
    def __init__(self, pos):
        super().__init__(pyramid_vertices, pyramid_triangles, pos, pyramid_pivot_offset)
        self.passed = False   # Para contar puntos una única vez al pasar

# Clase Fragment (mini cubo, usado en la explosión)
class Fragment:
    def __init__(self, pos, vel, rotation_z, angular_vel):
        self.pos = np.array(pos, dtype=float)   # Posición inicial del fragmento
        self.vel = np.array(vel, dtype=float)   # Velocidad inicial (vector) asignada al fragmento
        self.rotation_z = rotation_z            # Ángulo de rotación inicial (en radianes)
        self.angular_vel = angular_vel          # Velocidad angular (rotación por segundo)

    def update(self, dt, gravity):
        """
        Actualiza la posición y rotación del fragmento.
        Aplica la fórmula de movimiento rectilíneo:
            pos = pos + vel * dt
        Y actualiza la velocidad en Y aplicando gravedad:
            vel_y = vel_y - gravity * dt
        También actualiza la rotación:
            rotation_z = rotation_z + angular_vel * dt
        """
        self.pos += self.vel * dt
        self.vel[1] -= gravity * dt
        self.rotation_z += self.angular_vel * dt

    def get_transformed_vertices(self):
        """
        Devuelve los vértices transformados del fragmento.
        Utiliza el mismo método que en GameObject, pero aplicado a mini_cube_vertices.
        """
        R = rotation_z(self.rotation_z)
        transformed = []
        for v in mini_cube_vertices:
            local = np.dot(R, (v + mini_cube_pivot_offset))
            world = local + self.pos
            transformed.append(world)
        return transformed

def create_fragments_from_player(player):
    """
    Genera fragmentos (mini cubos) a partir del jugador.
    Se subdivide el cubo en 8 partes (utilizando offsets en X, Y y Z).
    Para cada fragmento se calcula un vector dirección (desde el centro del cubo)
    y se asigna una velocidad inicial (con un poco de aleatoriedad) y una velocidad angular.
    Esto simula la explosión del cubo.
    """
    fragments = []
    center = player.pos + np.array([0, 0.5, 0], dtype=float)  # Centro del cubo (jugador)
    offsets = []
    for dx in [-0.25, 0.25]:
        for dy in [0.25, 0.75]:
            for dz in [-0.25, 0.25]:
                offsets.append(np.array([dx, dy, dz]))
    R = rotation_z(player.rotation_z)
    for off in offsets:
        world_off = np.dot(R, off + cube_pivot_offset)
        frag_pos = player.pos + world_off
        dir_vec = frag_pos - center
        norm = np.linalg.norm(dir_vec)
        if norm != 0:
            dir_vec /= norm
        else:
            dir_vec = np.array([0,1,0], dtype=float)
        speed = random.uniform(0.5, 1.5)
        vel = dir_vec * speed + np.random.uniform(-0.2, 0.2, size=3)
        ang_vel = random.uniform(-math.pi, math.pi)
        fragments.append(Fragment(frag_pos, vel, player.rotation_z, ang_vel))
    return fragments

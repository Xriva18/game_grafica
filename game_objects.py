# game_objects.py
import numpy as np
import math, random
from render_utils import rotation_z
from config import CUBE_SCALE, PYRAMID_SCALE, MINI_SCALE

# Definiciones base del cubo (jugador)
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
cube_pivot_offset = np.array([0, 0.5, 0], dtype=float)

# Definiciones base de la pirámide (obstáculo)
pyramid_vertices = [
    np.array([0, 1, 0]) * PYRAMID_SCALE,
    np.array([-1, -1, 1]) * PYRAMID_SCALE,
    np.array([1, -1, 1]) * PYRAMID_SCALE,
    np.array([1, -1, -1]) * PYRAMID_SCALE,
    np.array([-1, -1, -1]) * PYRAMID_SCALE
]
pyramid_triangles = [
    (0,1,2), (0,2,3), (0,3,4), (0,4,1),
    (1,2,3), (1,3,4)
]
pyramid_pivot_offset = np.array([0, 0.5, 0], dtype=float)

# Para los fragmentos (mini cubos) se usan los mismos vértices del cubo, escalados
mini_cube_vertices = [v * MINI_SCALE for v in cube_vertices]
mini_cube_triangles = cube_triangles[:]  # mismos triángulos
mini_cube_pivot_offset = np.array([0, 0.5*MINI_SCALE, 0], dtype=float)

class GameObject:
    def __init__(self, base_vertices, triangles, pos, pivot_offset):
        self.base_vertices = base_vertices
        self.triangles = triangles
        self.pos = np.array(pos, dtype=float)
        self.pivot_offset = pivot_offset.copy()
        self.rotation_z = 0.0

    def get_transformed_vertices(self):
        R = rotation_z(self.rotation_z)
        transformed = []
        for v in self.base_vertices:
            local = np.dot(R, (v + self.pivot_offset))
            world = local + self.pos
            transformed.append(world)
        return transformed

class Player(GameObject):
    def __init__(self, pos):
        super().__init__(cube_vertices, cube_triangles, pos, cube_pivot_offset)
        self.vel_y = 0.0
        self.on_ground = True

class Obstacle(GameObject):
    def __init__(self, pos):
        super().__init__(pyramid_vertices, pyramid_triangles, pos, pyramid_pivot_offset)
        self.passed = False

class Fragment:
    def __init__(self, pos, vel, rotation_z, angular_vel):
        self.pos = np.array(pos, dtype=float)
        self.vel = np.array(vel, dtype=float)
        self.rotation_z = rotation_z
        self.angular_vel = angular_vel

    def update(self, dt, gravity):
        self.pos += self.vel * dt
        self.vel[1] -= gravity * dt
        self.rotation_z += self.angular_vel * dt

    def get_transformed_vertices(self):
        R = rotation_z(self.rotation_z)
        transformed = []
        for v in mini_cube_vertices:
            local = np.dot(R, (v + mini_cube_pivot_offset))
            world = local + self.pos
            transformed.append(world)
        return transformed

def create_fragments_from_player(player):
    fragments = []
    center = player.pos + np.array([0, 0.5, 0], dtype=float)
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
            dir_vec = np.array([0, 1, 0], dtype=float)
        speed = random.uniform(0.5, 1.5)
        vel = dir_vec * speed + np.random.uniform(-0.2, 0.2, size=3)
        ang_vel = random.uniform(-math.pi, math.pi)
        fragments.append(Fragment(frag_pos, vel, player.rotation_z, ang_vel))
    return fragments

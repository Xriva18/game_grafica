import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import numpy as np
import math, random, sys

# ---------------------------------------------------
# Configuración de pygame y ventana OpenGL
# ---------------------------------------------------
pygame.init()
display = (800, 600)
pygame.display.set_mode(display, DOUBLEBUF | OPENGL)
clock = pygame.time.Clock()

glMatrixMode(GL_PROJECTION)
glLoadIdentity()
gluPerspective(45, (display[0]/display[1]), 0.1, 1000.0)
glMatrixMode(GL_MODELVIEW)

# Desactivamos el z-buffer (usamos painter’s algorithm manual)
glDisable(GL_DEPTH_TEST)

# Activamos blending para la sombra semitransparente
glEnable(GL_BLEND)
glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

# ---------------------------------------------------
# Funciones de ayuda (rotación, culling, painter, etc.)
# ---------------------------------------------------
def rotation_z(angle):
    """Matriz de rotación 3x3 alrededor de Z."""
    c = math.cos(angle)
    s = math.sin(angle)
    return np.array([
        [ c, -s, 0],
        [ s,  c, 0],
        [ 0,  0, 1]
    ], dtype=float)

def backface_cull(triangles, vertices, cam_pos):
    """Devuelve los triángulos que miran hacia la cámara."""
    visibles = []
    for tri in triangles:
        v0 = vertices[tri[0]]
        v1 = vertices[tri[1]]
        v2 = vertices[tri[2]]
        edge1 = v1 - v0
        edge2 = v2 - v0
        normal = np.cross(edge1, edge2)
        view_dir = cam_pos - v0
        if np.dot(normal, view_dir) > 0:
            visibles.append(tri)
    return visibles

def painter_sort(triangles, vertices):
    """Ordena los triángulos según la profundidad promedio (z)."""
    tri_depths = []
    for tri in triangles:
        z_avg = (vertices[tri[0]][2] + vertices[tri[1]][2] + vertices[tri[2]][2]) / 3.0
        tri_depths.append((tri, z_avg))
    tri_depths.sort(key=lambda x: x[1], reverse=True)
    return [t for (t, _) in tri_depths]

def draw_object(vertices, triangles, color):
    """Dibuja los triángulos de un objeto con un color RGBA."""
    glColor4f(*color)
    glBegin(GL_TRIANGLES)
    for tri in triangles:
        for idx in tri:
            glVertex3fv(vertices[idx])
    glEnd()

def project_shadow(vertex, light_dir):
    """Proyecta un vértice sobre el plano y=0 según la dirección de la luz."""
    if light_dir[1] == 0:
        return vertex.copy()
    t = -vertex[1] / light_dir[1]
    return vertex + light_dir * t

# ---------------------------------------------------
# Modelos (cubo y pirámide) con escalas parecidas
# ---------------------------------------------------
CUBE_SCALE = 1.0
PYRAMID_SCALE = 0.5

# --- Cubo ---
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
    (0,1,2), (0,2,3),      # cara inferior
    (4,6,5), (4,7,6),      # cara superior
    (4,5,1), (4,1,0),      # cara frontal
    (5,6,2), (5,2,1),      # cara derecha
    (6,7,3), (6,3,2),      # cara trasera
    (7,4,0), (7,0,3)       # cara izquierda
]
cube_pivot_offset = np.array([0, 0.5, 0], dtype=float)

# --- Pirámide ---
pyramid_vertices = [
    np.array([ 0,  1,  0]) * PYRAMID_SCALE,
    np.array([-1, -1,  1]) * PYRAMID_SCALE,
    np.array([ 1, -1,  1]) * PYRAMID_SCALE,
    np.array([ 1, -1, -1]) * PYRAMID_SCALE,
    np.array([-1, -1, -1]) * PYRAMID_SCALE
]
pyramid_triangles = [
    (0,1,2), (0,2,3), (0,3,4), (0,4,1),
    (1,2,3), (1,3,4)
]
pyramid_pivot_offset = np.array([0, 0.5, 0], dtype=float)

# ---------------------------------------------------
# Clases de objetos (jugador y obstáculo)
# ---------------------------------------------------
class GameObject:
    def __init__(self, base_vertices, triangles, pos, pivot_offset):
        self.base_vertices = base_vertices
        self.triangles = triangles
        self.pos = np.array(pos, dtype=float)
        self.pivot_offset = pivot_offset.copy()
        self.rotation_z = 0.0

    def get_transformed_vertices(self):
        """Aplica rotación Z, pivot y traslación."""
        R = rotation_z(self.rotation_z)
        transformed = []
        for v in self.base_vertices:
            local_v = np.dot(R, (v + self.pivot_offset))
            world_v = local_v + self.pos
            transformed.append(world_v)
        return transformed

class Player(GameObject):
    def __init__(self, pos):
        super().__init__(cube_vertices, cube_triangles, pos, cube_pivot_offset)
        self.vel_y = 0.0
        self.on_ground = True

class Obstacle(GameObject):
    def __init__(self, pos):
        super().__init__(pyramid_vertices, pyramid_triangles, pos, pyramid_pivot_offset)

# ---------------------------------------------------
# Función para generar obstáculos en un rango de X
# ---------------------------------------------------
def spawn_obstacles_in_range(start_x, end_x):
    """
    Genera pirámides desde start_x hasta end_x (de mayor a menor),
    separadas por 5..10 unidades aleatoriamente.
    Ej: start_x=-30, end_x=-100
    """
    x = start_x
    while x > end_x:
        obstacles.append(Obstacle(pos=[x, 0, 0]))
        x -= random.randint(5, 10)

# ---------------------------------------------------
# Inicialización del juego
# ---------------------------------------------------
player = Player(pos=[0, 0, 0])  # El jugador inicia en x=0
obstacles = []

# Dirección de la luz para la sombra
light_dir = np.array([0.5, -1, 0.5], dtype=float)
light_dir /= np.linalg.norm(light_dir)

GRAVITY = 0.01
JUMP_SPEED = 0.3
PLAYER_SPEED = 0.07  # El jugador se moverá hacia la izquierda

game_over = False
game_over_printed = False

# 1) Generamos un “bloque” inicial de obstáculos desde -30 hasta -300
spawn_obstacles_in_range(-30, -300)
current_end_x = -300  # Hasta dónde hemos generado

# ---------------------------------------------------
# Función de colisión (AABB 2D)
# ---------------------------------------------------
def check_collision(p, obs):
    dx = abs(p.pos[0] - obs.pos[0])
    dy = abs(p.pos[1] - obs.pos[1])
    if dx < 0.6 and dy < 0.6:
        return True
    return False

# ---------------------------------------------------
# Dibujo del piso con líneas (y=0)
# ---------------------------------------------------
def draw_floor_lines():
    spacing = 5
    glColor4f(0, 0, 0, 1)
    for x in range(-1000, 1005, spacing):
        glBegin(GL_LINES)
        glVertex3f(x, 0, -1000)
        glVertex3f(x, 0,  1000)
        glEnd()
    for z in range(-1000, 1005, spacing):
        glBegin(GL_LINES)
        glVertex3f(-1000, 0, z)
        glVertex3f( 1000, 0, z)
        glEnd()

# ---------------------------------------------------
# Bucle principal
# ---------------------------------------------------
while True:
    # Manejo de eventos
    for event in pygame.event.get():
        if event.type == QUIT:
            pygame.quit()
            sys.exit()
        elif event.type == KEYDOWN:
            if event.key == K_ESCAPE:
                pygame.quit()
                sys.exit()
            # Salto
            if event.key == K_SPACE and player.on_ground and not game_over:
                player.vel_y = JUMP_SPEED
                player.on_ground = False

    # Si estamos en Game Over, solo dibujamos para poder salir con ESC
    if game_over:
        if not game_over_printed:
            print("Game Over. Pulsa ESC para salir.")
            game_over_printed = True
        # Dibujamos escena "congelada"
        glLoadIdentity()
        # ********* CÁMARA MÁS CERCA DEL JUGADOR *********
        gluLookAt(player.pos[0] - 15, 5, -20,  # <--- offset reducido
                  player.pos[0], 0, 0,
                  0, 1, 0)
        glClearColor(0.5, 0.8, 1.0, 1.0)
        glClear(GL_COLOR_BUFFER_BIT)
        draw_floor_lines()
        pygame.display.flip()
        clock.tick(60)
        continue

    # --- LÓGICA DEL JUEGO ---
    # El jugador se mueve hacia la izquierda
    player.pos[0] -= PLAYER_SPEED

    # Aplicar gravedad/salto
    if not player.on_ground:
        player.vel_y -= GRAVITY
    player.pos[1] += player.vel_y
    if player.pos[1] < 0:
        player.pos[1] = 0
        player.vel_y = 0
        player.on_ground = True
        # Ajustar rotación al múltiplo de 90°
        player.rotation_z = round(player.rotation_z / (math.pi/2)) * (math.pi/2)
    if not player.on_ground:
        player.rotation_z += 0.1

    # Generar más obstáculos si el jugador se acerca al final del rango actual
    if player.pos[0] < (current_end_x + 20):
        new_end_x = current_end_x - 100
        spawn_obstacles_in_range(current_end_x, new_end_x)
        current_end_x = new_end_x

    # Comprobar colisiones
    for obs in obstacles:
        if check_collision(player, obs):
            game_over = True
            break

    # --- RENDERIZADO ---
    glLoadIdentity()
    # ********* CÁMARA MÁS CERCA DEL JUGADOR *********
    gluLookAt(player.pos[0] - 15, 5, -20,  # <--- offset reducido
              player.pos[0], player.pos[1], player.pos[2],
              0, 1, 0)

    # Limpiamos pantalla con color celeste
    glClearColor(0.5, 0.8, 1.0, 1.0)
    glClear(GL_COLOR_BUFFER_BIT)

    # Dibujamos el piso
    draw_floor_lines()

    # Posición aproximada de la cámara (para culling)
    cam_pos = np.array([player.pos[0] - 15, 5, -20], dtype=float)

    # Dibujamos el jugador (backface culling + painter)
    p_verts = player.get_transformed_vertices()
    visible_p = backface_cull(player.triangles, p_verts, cam_pos)
    sorted_p = painter_sort(visible_p, p_verts)
    draw_object(p_verts, sorted_p, (0, 0.5, 1, 1))  # Cubo en azul

    # Sombra del jugador
    shadow_p = [project_shadow(v, light_dir) for v in p_verts]
    draw_object(shadow_p, sorted_p, (0, 0, 0, 0.5))

    # Dibujamos cada pirámide
    for obs in obstacles:
        o_verts = obs.get_transformed_vertices()
        # Omitimos culling para que siempre se vean
        sorted_o = painter_sort(obs.triangles, o_verts)
        draw_object(o_verts, sorted_o, (1, 0, 0, 1))  # Rojo
        # Sombra
        shadow_o = [project_shadow(v, light_dir) for v in o_verts]
        draw_object(shadow_o, sorted_o, (0, 0, 0, 0.4))

    pygame.display.flip()
    clock.tick(60)

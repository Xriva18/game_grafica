import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import numpy as np
import math, random, sys

# ============================
# Configuración de Pygame y OpenGL
# ============================
pygame.init()
display = (800, 600)
pygame.display.set_mode(display, DOUBLEBUF | OPENGL)
clock = pygame.time.Clock()

glMatrixMode(GL_PROJECTION)
glLoadIdentity()
gluPerspective(45, (display[0] / display[1]), 0.1, 1000.0)
glMatrixMode(GL_MODELVIEW)

# Desactivar el Z-buffer (painter’s algorithm manual)
glDisable(GL_DEPTH_TEST)
# Activar blending para transparencias (sombras)
glEnable(GL_BLEND)
glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

# Fuente para texto
font = pygame.font.SysFont("Arial", 24)
def draw_text(x, y, text):
    """Dibuja texto en la ventana en (x,y) en píxeles."""
    text_surface = font.render(text, True, (255, 255, 255))
    text_data = pygame.image.tostring(text_surface, "RGBA", True)
    glWindowPos2d(x, y)
    glDrawPixels(text_surface.get_width(), text_surface.get_height(), GL_RGBA, GL_UNSIGNED_BYTE, text_data)

# ============================
# Funciones de ayuda (rotación, culling, painter, etc.)
# ============================
def rotation_z(angle):
    c = math.cos(angle)
    s = math.sin(angle)
    return np.array([[ c, -s, 0],
                     [ s,  c, 0],
                     [ 0,  0, 1]], dtype=float)

def backface_cull(triangles, vertices, cam_pos):
    visibles = []
    for tri in triangles:
        v0, v1, v2 = vertices[tri[0]], vertices[tri[1]], vertices[tri[2]]
        normal = np.cross(v1 - v0, v2 - v0)
        if np.dot(normal, cam_pos - v0) > 0:
            visibles.append(tri)
    return visibles

def painter_sort(triangles, vertices):
    tri_depths = []
    for tri in triangles:
        z_avg = (vertices[tri[0]][2] + vertices[tri[1]][2] + vertices[tri[2]][2]) / 3.0
        tri_depths.append((tri, z_avg))
    tri_depths.sort(key=lambda t: t[1], reverse=True)
    return [t for (t, _) in tri_depths]

def draw_object(vertices, triangles, color):
    glColor4f(*color)
    glBegin(GL_TRIANGLES)
    for tri in triangles:
        for idx in tri:
            glVertex3fv(vertices[idx])
    glEnd()

def project_shadow(vertex, light_dir):
    if light_dir[1] == 0:
        return vertex.copy()
    t = -vertex[1] / light_dir[1]
    return vertex + light_dir * t

# ============================
# Modelos base y escalado
# ============================
CUBE_SCALE = 1.0       # Tamaño del cubo jugador
PYRAMID_SCALE = 0.5    # Tamaño de la pirámide (obstáculo)

# Cubo (jugador): vértices de -0.5 a 0.5, pivot_offset = [0,0.5,0] para que la base esté en y=0.
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

# Pirámide (obstáculo): vértices con apex en (0,1,0) y base en y=-1, escalados para que la base quede en y=0.
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

# Para los fragmentos (mini cubos) usaremos una versión del cubo reducida a la mitad:
mini_scale = 0.5
mini_cube_vertices = [v * mini_scale for v in cube_vertices]  # cada vértice reducido
mini_cube_triangles = cube_triangles[:]  # mismo índice
mini_cube_pivot_offset = np.array([0, 0.5*mini_scale, 0], dtype=float)  # para que la base esté en y=0

# ============================
# Clases de objetos
# ============================
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
        self.passed = False  # para contar puntos solo una vez

# Clase para fragmentos (mini cubos)
class Fragment:
    def __init__(self, pos, vel, rotation_z, angular_vel):
        self.pos = np.array(pos, dtype=float)
        self.vel = np.array(vel, dtype=float)
        self.rotation_z = rotation_z
        self.angular_vel = angular_vel
    def update(self, dt):
        self.pos += self.vel * dt
        # Aplicamos gravedad a la componente Y
        self.vel[1] -= GRAVITY * dt
        self.rotation_z += self.angular_vel * dt

    def get_transformed_vertices(self):
        R = rotation_z(self.rotation_z)
        transformed = []
        for v in mini_cube_vertices:
            local = np.dot(R, (v + mini_cube_pivot_offset))
            world = local + self.pos
            transformed.append(world)
        return transformed

# ============================
# Variables globales del juego y cámara
# ============================
score = 0
high_score = 0
base_speed = 0.07  # velocidad base del jugador
PLAYER_SPEED = base_speed
# La cámara se controla con un offset relativo al jugador:
camera_offset = np.array([-15, 5, -20], dtype=float)

# Estados del juego: "running", "exploding", "game_over"
state = "running"
explosion_start_time = None
fragments = []  # lista de Fragment

# ============================
# Función para generar obstáculos en un rango de X
# ============================
def spawn_obstacles_in_range(start_x, end_x):
    x = start_x
    while x > end_x:
        obstacles.append(Obstacle(pos=[x, 0, 0]))
        x -= random.randint(5, 10)

# ============================
# Inicialización del juego
# ============================
player = Player(pos=[0, 0, 0])
obstacles = []
# Generamos un bloque inicial de obstáculos desde x = -30 hasta -300
spawn_obstacles_in_range(-30, -300)
current_end_x = -300

# Dirección de la luz para las sombras
light_dir = np.array([0.5, -1, 0.5], dtype=float)
light_dir /= np.linalg.norm(light_dir)
GRAVITY = 0.01
JUMP_SPEED = 0.3

# Para optimizar el fondo, definimos un límite:
floor_limit = 200

# ============================
# Función de colisión (AABB 2D)
# ============================
def check_collision(p, obs):
    dx = abs(p.pos[0] - obs.pos[0])
    dy = abs(p.pos[1] - obs.pos[1])
    return (dx < 0.6 and dy < 0.6)

# ============================
# Dibujo del piso (líneas en y=0) con límite
# ============================
def draw_floor_lines():
    spacing = 5
    glColor4f(0, 0, 0, 1)
    for x in range(-floor_limit, floor_limit+1, spacing):
        glBegin(GL_LINES)
        glVertex3f(x, 0, -floor_limit)
        glVertex3f(x, 0, floor_limit)
        glEnd()
    for z in range(-floor_limit, floor_limit+1, spacing):
        glBegin(GL_LINES)
        glVertex3f(-floor_limit, 0, z)
        glVertex3f(floor_limit, 0, z)
        glEnd()

# ============================
# Función para crear fragmentos (mini cubos) a partir del jugador
# ============================
def create_fragments_from_player():
    global fragments
    # El centro del cubo (jugador) es:
    center = player.pos + np.array([0, 0.5, 0], dtype=float)
    # Para subdividir, usamos 2 valores en cada dirección:
    offsets = []
    for dx in [-0.25, 0.25]:
        for dy in [0.25, 0.75]:
            for dz in [-0.25, 0.25]:
                offsets.append(np.array([dx, dy, dz]))
    # Aplicamos la rotación del jugador al offset (recordando el pivot offset ya aplicado)
    R = rotation_z(player.rotation_z)
    fragments = []
    for off in offsets:
        # La posición mundial del fragmento:
        world_off = np.dot(R, off + cube_pivot_offset)
        frag_pos = player.pos + world_off
        # Dirección: desde el centro del cubo hacia el fragmento
        dir_vec = frag_pos - center
        norm = np.linalg.norm(dir_vec)
        if norm != 0:
            dir_vec = dir_vec / norm
        else:
            dir_vec = np.array([0,1,0], dtype=float)
        # Asignamos una velocidad inicial: base + un factor aleatorio
        speed = random.uniform(0.5, 1.5)
        vel = dir_vec * speed
        # Añadimos un pequeño componente aleatorio extra
        vel += np.random.uniform(-0.2, 0.2, size=3)
        # Angular velocity aleatoria (en radianes/segundo)
        ang_vel = random.uniform(-math.pi, math.pi)
        fragments.append(Fragment(frag_pos, vel, player.rotation_z, ang_vel))

# ============================
# Bucle principal del juego
# ============================
while True:
    dt = clock.get_time() / 1000.0  # dt en segundos
    # Manejo de eventos
    for event in pygame.event.get():
        if event.type == QUIT:
            pygame.quit()
            sys.exit()
        elif event.type == KEYDOWN:
            if event.key == K_ESCAPE:
                pygame.quit()
                sys.exit()
            # En estado running: salto
            if state == "running":
                if event.key == K_SPACE and player.on_ground:
                    player.vel_y = JUMP_SPEED
                    player.on_ground = False
            # En estado game_over: reiniciar con R
            if state in ["game_over", "exploding"] and event.key == K_r:
                if score > high_score:
                    high_score = score
                score = 0
                PLAYER_SPEED = base_speed
                player = Player(pos=[0, 0, 0])
                obstacles = []
                spawn_obstacles_in_range(-30, -300)
                current_end_x = -300
                state = "running"
                fragments = []
    # Permitir cambiar la perspectiva con las flechas en cualquier estado
    keys = pygame.key.get_pressed()
    if keys[K_LEFT]:
        camera_offset[0] -= 0.2
    if keys[K_RIGHT]:
        camera_offset[0] += 0.2
    if keys[K_UP]:
        camera_offset[1] += 0.2
    if keys[K_DOWN]:
        camera_offset[1] -= 0.2

    # ============================
    # Actualización según estado
    # ============================
    if state == "running":
        # Actualizar velocidad según score
        PLAYER_SPEED = base_speed + (score / 5000.0)
        player.pos[0] -= PLAYER_SPEED  # El jugador se mueve hacia la izquierda
        # Actualizar salto y gravedad
        if not player.on_ground:
            player.vel_y -= GRAVITY
        player.pos[1] += player.vel_y
        if player.pos[1] < 0:
            player.pos[1] = 0
            player.vel_y = 0
            player.on_ground = True
            player.rotation_z = round(player.rotation_z / (math.pi/2)) * (math.pi/2)
        if not player.on_ground:
            player.rotation_z += 0.1
        # Sumar puntos: cada obstáculo que se pasa (una sola vez)
        for obs in obstacles:
            if not obs.passed and player.pos[0] < obs.pos[0]:
                score += 10
                obs.passed = True
        # Generar más obstáculos dinámicamente
        if player.pos[0] < (current_end_x + 20):
            new_end_x = current_end_x - 100
            spawn_obstacles_in_range(current_end_x, new_end_x)
            current_end_x = new_end_x
        # Comprobar colisiones
        for obs in obstacles:
            if check_collision(player, obs):
                # Al colisionar, en vez de game_over, iniciamos la explosión
                create_time = pygame.time.get_ticks()
                explosion_start_time = create_time
                create_fragments_from_player()
                state = "exploding"
                break

    elif state == "exploding":
        # Actualizar la animación de fragmentos durante 1.5 segundos
        current_time = pygame.time.get_ticks()
        elapsed = current_time - explosion_start_time
        if elapsed < 1500:
            for frag in fragments:
                frag.update(dt)
        else:
            # Una vez pasados 1.5 segundos, congelamos la animación y pasamos a game_over
            state = "game_over"
        # En estado explosion, no actualizamos el jugador ni los obstáculos (se congelan)

    elif state == "game_over":
        # En game_over, todo se congela (no se actualizan posiciones)
        pass

    # ============================
    # Renderizado (común a todos los estados)
    # ============================
    glLoadIdentity()
    # La cámara se posiciona según el offset actual
    # Usamos: posición = player.pos + camera_offset (o, si ya explotó, se usa el último player.pos)
    cam_pos = player.pos + camera_offset
    gluLookAt(cam_pos[0], cam_pos[1], cam_pos[2],
              player.pos[0], player.pos[1], player.pos[2],
              0, 1, 0)
    glClearColor(0.5, 0.8, 1.0, 1.0)
    glClear(GL_COLOR_BUFFER_BIT)
    draw_floor_lines()
    # En estado "running", dibujamos jugador y obstáculos; en "exploding" y "game_over", el jugador se destruyó
    if state == "running":
        # Dibujar jugador
        p_verts = player.get_transformed_vertices()
        vis_p = backface_cull(player.triangles, p_verts, cam_pos)
        sorted_p = painter_sort(vis_p, p_verts)
        draw_object(p_verts, sorted_p, (0, 0.5, 1, 1))
    elif state in ["exploding", "game_over"]:
        # Dibujar los fragmentos (mini cubos)
        for frag in fragments:
            frag_verts = frag.get_transformed_vertices()
            # No aplicamos culling para que se vean todos
            sorted_frag = painter_sort(cube_triangles, frag_verts)
            draw_object(frag_verts, sorted_frag, (0, 0.5, 1, 1))
    # Dibujar obstáculos (siempre se dibujan)
    for obs in obstacles:
        o_verts = obs.get_transformed_vertices()
        sorted_o = painter_sort(obs.triangles, o_verts)
        draw_object(o_verts, sorted_o, (1, 0, 0, 1))
        shadow_o = [project_shadow(v, light_dir) for v in o_verts]
        draw_object(shadow_o, sorted_o, (0, 0, 0, 0.4))
    # Dibujar la sombra del jugador (solo en running)
    if state == "running":
        shadow_p = [project_shadow(v, light_dir) for v in p_verts]
        draw_object(shadow_p, sorted_p, (0, 0, 0, 0.5))
    # Si estamos en estado game_over (o explosion terminada), dibujar mensaje de Game Over
    if state == "game_over":
        draw_text(10, display[1] - 30, f"Game Over! Score: {score}   Record: {high_score}")
        draw_text(10, display[1] - 60, "Press R to restart")
    # Dibujar puntaje (si no es game_over, o incluso también)
    if state == "running":
        draw_text(10, display[1] - 30, f"Score: {score}   Record: {high_score}")
    pygame.display.flip()
    clock.tick(60)

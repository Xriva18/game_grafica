# main.py
"""
Archivo principal del juego.
Aquí se inicializan Pygame y OpenGL, se carga la música de fondo, se
configuran los módulos y se ejecuta el bucle principal del juego.
Se importan los módulos de configuración, utilidades de renderizado y objetos del juego.
Además, se implementa la lógica de juego:
- Movimiento del jugador y obstáculos.
- Sistema de puntuación y aumento de velocidad.
- Detección de colisiones.
- Animación de explosión (fragmentación del cubo) durante 1.5 segundos.
- Modo Game Over con mensaje y reinicio al presionar la tecla R.
- Control de perspectiva con las flechas.
"""

import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import numpy as np
import math, random, sys
import time

# Importar configuraciones
from config import DISPLAY_WIDTH, DISPLAY_HEIGHT, FOV, NEAR_PLANE, FAR_PLANE, GRAVITY, JUMP_SPEED, BASE_SPEED, FLOOR_LIMIT, CAMERA_OFFSET
# Importar funciones de renderizado
from render_utils import draw_text, rotation_z, backface_cull, painter_sort, draw_object, project_shadow, draw_floor_lines
# Importar objetos del juego
from game_objects import Player, Obstacle, create_fragments_from_player, cube_triangles

pygame.init()

# --- Música de fondo ---
# Inicializa el mezclador de audio y reproduce Music.mp3 en bucle.
pygame.mixer.init()
pygame.mixer.music.load("Music.mp3")
pygame.mixer.music.play(-1)

# Configuración de la ventana
display = (DISPLAY_WIDTH, DISPLAY_HEIGHT)
pygame.display.set_mode(display, DOUBLEBUF | OPENGL)
clock = pygame.time.Clock()

# Configurar la proyección en OpenGL
glMatrixMode(GL_PROJECTION)
glLoadIdentity()
gluPerspective(FOV, (DISPLAY_WIDTH / DISPLAY_HEIGHT), NEAR_PLANE, FAR_PLANE)
glMatrixMode(GL_MODELVIEW)
glDisable(GL_DEPTH_TEST)
glEnable(GL_BLEND)
glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

# Fuente para dibujar textos
font = pygame.font.SysFont("Arial", 24)

# --- Variables globales de juego ---
score = 0
high_score = 0
player = Player(pos=[0, 0, 0])
obstacles = []
PLAYER_SPEED = BASE_SPEED
# La cámara se controla mediante este offset relativo al jugador.
camera_offset = np.array(CAMERA_OFFSET, dtype=float)

# Estados del juego:
# "running": juego en curso.
# "exploding": animación de explosión (fragmentación) activa (duración 1.5 s).
# "game_over": estado final, pantalla congelada y mensaje.
state = "running"
explosion_start_time = None
fragments = []

def spawn_obstacles_in_range(start_x, end_x):
    """
    Genera obstáculos (pirámides) en el eje X desde start_x hasta end_x,
    separadas aleatoriamente entre 5 y 10 unidades.
    """
    x = start_x
    while x > end_x:
        obstacles.append(Obstacle(pos=[x, 0, 0]))
        x -= random.randint(5, 10)

# Generar bloque inicial de obstáculos desde -30 hasta -300.
spawn_obstacles_in_range(-30, -300)
current_end_x = -300

# Dirección de la luz (para las sombras)
light_dir = np.array([0.5, -1, 0.5], dtype=float)
light_dir /= np.linalg.norm(light_dir)

# --- Bucle principal del juego ---
while True:
    dt = clock.get_time() / 1000.0  # dt en segundos.
    for event in pygame.event.get():
        if event.type == QUIT:
            pygame.quit(); sys.exit()
        elif event.type == KEYDOWN:
            if event.key == K_ESCAPE:
                pygame.quit(); sys.exit()
            # En estado "running", la tecla SPACE permite saltar.
            if state == "running":
                if event.key == K_SPACE and player.on_ground:
                    player.vel_y = JUMP_SPEED
                    player.on_ground = False
            # En estado "exploding" o "game_over", la tecla R reinicia el juego.
            if state in ["exploding", "game_over"] and event.key == K_r:
                if score > high_score:
                    high_score = score
                score = 0
                PLAYER_SPEED = BASE_SPEED
                player = Player(pos=[0, 0, 0])
                obstacles = []
                spawn_obstacles_in_range(-30, -300)
                current_end_x = -300
                state = "running"
                fragments = []
                # Reinicia la música desde el inicio.
                pygame.mixer.music.play(-1)
    # Permitir cambiar la perspectiva con las flechas (modifica camera_offset)
    keys = pygame.key.get_pressed()
    if keys[K_LEFT]:
        camera_offset[0] -= 0.2
    if keys[K_RIGHT]:
        camera_offset[0] += 0.2
    if keys[K_UP]:
        camera_offset[1] += 0.2
    if keys[K_DOWN]:
        camera_offset[1] -= 0.2

    # --- Lógica del juego según el estado ---
    if state == "running":
        # La velocidad del jugador aumenta con el score:
        PLAYER_SPEED = BASE_SPEED + (score / 5000.0)
        player.pos[0] -= PLAYER_SPEED  # Movimiento hacia la izquierda.
        # Actualizar salto y gravedad:
        if not player.on_ground:
            player.vel_y -= GRAVITY
        player.pos[1] += player.vel_y
        if player.pos[1] < 0:
            player.pos[1] = 0
            player.vel_y = 0
            player.on_ground = True
            # Ajustar la rotación a un múltiplo de 90° (para que el cubo "asiente" su orientación)
            player.rotation_z = round(player.rotation_z / (math.pi/2)) * (math.pi/2)
        if not player.on_ground:
            player.rotation_z += 0.1
        # Sumar puntos: cada obstáculo que el jugador pasa sin colisionar (se suma 10 puntos).
        for obs in obstacles:
            if not obs.passed and player.pos[0] < obs.pos[0]:
                score += 10
                obs.passed = True
        # Generar más obstáculos dinámicamente si el jugador se acerca al final del rango.
        if player.pos[0] < (current_end_x + 20):
            new_end_x = current_end_x - 100
            spawn_obstacles_in_range(current_end_x, new_end_x)
            current_end_x = new_end_x
        # Comprobar colisiones: si el jugador colisiona con algún obstáculo...
        for obs in obstacles:
            if abs(player.pos[0] - obs.pos[0]) < 0.6 and abs(player.pos[1] - obs.pos[1]) < 0.6:
                # Detener la música al colisionar.
                pygame.mixer.music.stop()
                # Se inicia la animación de explosión (fragmentación del cubo).
                explosion_start_time = pygame.time.get_ticks()
                fragments = create_fragments_from_player(player)
                state = "exploding"
                break
    elif state == "exploding":
        current_time = pygame.time.get_ticks()
        elapsed = current_time - explosion_start_time
        if elapsed < 1500:
            # Actualizar cada fragmento: se aplican las fórmulas de movimiento y gravedad.
            for frag in fragments:
                frag.update(dt, GRAVITY)
        else:
            # Después de 1.5 segundos, se pasa a estado game_over y se congela la pantalla.
            state = "game_over"
    elif state == "game_over":
        # No se actualizan posiciones; se muestra el mensaje.
        pass

    # --- Renderizado ---
    glLoadIdentity()
    # La cámara se posiciona en player.pos + camera_offset.
    cam_pos = player.pos + camera_offset
    gluLookAt(cam_pos[0], cam_pos[1], cam_pos[2],
              player.pos[0], player.pos[1], player.pos[2],
              0, 1, 0)
    glClearColor(0.5, 0.8, 1.0, 1.0)
    glClear(GL_COLOR_BUFFER_BIT)
    draw_floor_lines(FLOOR_LIMIT)
    if state == "running":
        p_verts = player.get_transformed_vertices()
        vis_p = backface_cull(player.triangles, p_verts, cam_pos)
        sorted_p = painter_sort(vis_p, p_verts)
        draw_object(p_verts, sorted_p, (0, 0.5, 1, 1))
        shadow_p = [project_shadow(v, light_dir) for v in p_verts]
        draw_object(shadow_p, sorted_p, (0, 0, 0, 0.5))
    elif state in ["exploding", "game_over"]:
        for frag in fragments:
            frag_verts = frag.get_transformed_vertices()
            sorted_frag = painter_sort(cube_triangles, frag_verts)
            draw_object(frag_verts, sorted_frag, (0, 0.5, 1, 1))
    for obs in obstacles:
        o_verts = obs.get_transformed_vertices()
        sorted_o = painter_sort(obs.triangles, o_verts)
        draw_object(o_verts, sorted_o, (1, 0, 0, 1))
        shadow_o = [project_shadow(v, light_dir) for v in o_verts]
        draw_object(shadow_o, sorted_o, (0, 0, 0, 0.4))
    if state == "game_over":
        draw_text(10, display[1]-30, f"Game Over! P: {score}   R: {high_score}", font)
        draw_text(10, display[1]-60, "Reinica con [R]", font)
    if state == "running":
        draw_text(10, display[1]-30, f"Puntuación: {score}   Record: {high_score}", font)
    pygame.display.flip()
    clock.tick(60)

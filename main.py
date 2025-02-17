# main.py
import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import numpy as np
import math, random, sys
import time

from config import DISPLAY_WIDTH, DISPLAY_HEIGHT, FOV, NEAR_PLANE, FAR_PLANE, GRAVITY, JUMP_SPEED, BASE_SPEED, FLOOR_LIMIT, CAMERA_OFFSET
from render_utils import draw_text, rotation_z, backface_cull, painter_sort, draw_object, project_shadow, draw_floor_lines
from game_objects import Player, Obstacle, create_fragments_from_player, cube_triangles

pygame.init()

# --- Inicializa el mezclador de audio y carga la música de fondo ---
pygame.mixer.init()
pygame.mixer.music.load("Music.mp3")
pygame.mixer.music.play(-1)  # -1 para reproducir en bucle

display = (DISPLAY_WIDTH, DISPLAY_HEIGHT)
pygame.display.set_mode(display, DOUBLEBUF | OPENGL)
clock = pygame.time.Clock()

glMatrixMode(GL_PROJECTION)
glLoadIdentity()
gluPerspective(FOV, (DISPLAY_WIDTH / DISPLAY_HEIGHT), NEAR_PLANE, FAR_PLANE)
glMatrixMode(GL_MODELVIEW)
glDisable(GL_DEPTH_TEST)
glEnable(GL_BLEND)
glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

font = pygame.font.SysFont("Arial", 24)

# Variables globales de juego
score = 0
high_score = 0
player = Player(pos=[0, 0, 0])
obstacles = []
PLAYER_SPEED = BASE_SPEED
camera_offset = np.array(CAMERA_OFFSET, dtype=float)

# Estados: "running", "exploding", "game_over"
state = "running"
explosion_start_time = None
fragments = []

def spawn_obstacles_in_range(start_x, end_x):
    x = start_x
    while x > end_x:
        obstacles.append(Obstacle(pos=[x, 0, 0]))
        x -= random.randint(5, 10)

spawn_obstacles_in_range(-30, -300)
current_end_x = -300

light_dir = np.array([0.5, -1, 0.5], dtype=float)
light_dir /= np.linalg.norm(light_dir)

# --- Bucle principal del juego ---
while True:
    dt = clock.get_time() / 1000.0
    for event in pygame.event.get():
        if event.type == QUIT:
            pygame.quit(); sys.exit()
        elif event.type == KEYDOWN:
            if event.key == K_ESCAPE:
                pygame.quit(); sys.exit()
            if state == "running":
                if event.key == K_SPACE and player.on_ground:
                    player.vel_y = JUMP_SPEED
                    player.on_ground = False
            # Al reiniciar el juego (estado "exploding" o "game_over")
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
                # Reinicia la música desde el inicio
                pygame.mixer.music.play(-1)
    # Cambiar perspectiva con las flechas
    keys = pygame.key.get_pressed()
    if keys[K_LEFT]:
        camera_offset[0] -= 0.2
    if keys[K_RIGHT]:
        camera_offset[0] += 0.2
    if keys[K_UP]:
        camera_offset[1] += 0.2
    if keys[K_DOWN]:
        camera_offset[1] -= 0.2

    if state == "running":
        PLAYER_SPEED = BASE_SPEED + (score / 5000.0)
        player.pos[0] -= PLAYER_SPEED
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
        for obs in obstacles:
            if not obs.passed and player.pos[0] < obs.pos[0]:
                score += 10
                obs.passed = True
        if player.pos[0] < (current_end_x + 20):
            new_end_x = current_end_x - 100
            spawn_obstacles_in_range(current_end_x, new_end_x)
            current_end_x = new_end_x
        for obs in obstacles:
            # Detección de colisión (AABB simple)
            if abs(player.pos[0] - obs.pos[0]) < 0.6 and abs(player.pos[1] - obs.pos[1]) < 0.6:
                # Al colisionar, detenemos la música
                pygame.mixer.music.stop()
                explosion_start_time = pygame.time.get_ticks()
                fragments = create_fragments_from_player(player)
                state = "exploding"
                break
    elif state == "exploding":
        current_time = pygame.time.get_ticks()
        elapsed = current_time - explosion_start_time
        if elapsed < 1500:
            for frag in fragments:
                frag.update(dt, GRAVITY)
        else:
            state = "game_over"
    elif state == "game_over":
        pass

    glLoadIdentity()
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
        draw_text(10, display[1] - 30, f"Game Over! P: {score}   R: {high_score}", font)
        draw_text(10, display[1] - 60, "Presiona R para reiniciar", font)
    if state == "running":
        draw_text(10, display[1] - 30, f"Puntuación: {score}   Record: {high_score}", font)
    pygame.display.flip()
    clock.tick(60)

# render_utils.py
"""
Funciones de renderizado y utilidades matemáticas para el proyecto.
Aquí se incluyen funciones para la rotación (utilizando la matriz de rotación de Z),
backface culling (para eliminar triángulos que no se deben ver), painter’s algorithm (para ordenar los triángulos según la profundidad),
dibujar objetos y proyecciones (sombras), y para dibujar el piso y textos.
"""

import pygame
from OpenGL.GL import *
from OpenGL.GLU import *
import numpy as np
import math

def rotation_z(angle):
    """
    Calcula la matriz de rotación de 3x3 para el eje Z.
    Fórmula: 
      [ cos(angle)  -sin(angle)   0 ]
      [ sin(angle)   cos(angle)   0 ]
      [    0             0        1 ]
    Esto rota un vector en el plano XY.
    """
    c = math.cos(angle)
    s = math.sin(angle)
    return np.array([[ c, -s, 0],
                     [ s,  c, 0],
                     [ 0,  0, 1]], dtype=float)

def backface_cull(triangles, vertices, cam_pos):
    """
    Realiza el backface culling: elimina triángulos que no se ven desde la cámara.
    Calcula la normal de cada triángulo usando el producto vectorial y luego comprueba
    si el ángulo entre la normal y la dirección de la cámara es agudo (producto punto > 0).
    """
    visibles = []
    for tri in triangles:
        v0 = vertices[tri[0]]
        v1 = vertices[tri[1]]
        v2 = vertices[tri[2]]
        normal = np.cross(v1 - v0, v2 - v0)
        if np.dot(normal, cam_pos - v0) > 0:
            visibles.append(tri)
    return visibles

def painter_sort(triangles, vertices):
    """
    Ordena los triángulos de forma que se dibujen de atrás hacia adelante (painter’s algorithm).
    Calcula la profundidad promedio (valor Z) de cada triángulo y los ordena en orden descendente.
    """
    tri_depths = []
    for tri in triangles:
        z_avg = (vertices[tri[0]][2] + vertices[tri[1]][2] + vertices[tri[2]][2]) / 3.0
        tri_depths.append((tri, z_avg))
    tri_depths.sort(key=lambda t: t[1], reverse=True)
    return [t for (t, _) in tri_depths]

def draw_object(vertices, triangles, color):
    """
    Dibuja un objeto usando la lista de vértices y triángulos.
    Usa glBegin(GL_TRIANGLES) para dibujar cada triángulo.
    """
    glColor4f(*color)
    glBegin(GL_TRIANGLES)
    for tri in triangles:
        for idx in tri:
            glVertex3fv(vertices[idx])
    glEnd()

def project_shadow(vertex, light_dir):
    """
    Proyecta un vértice sobre el plano y = 0 siguiendo la dirección de la luz.
    La fórmula es: v_proyectado = v + t * light_dir, donde t = -v.y / light_dir.y.
    Esto se usa para crear la sombra del objeto en el piso.
    """
    if light_dir[1] == 0:
        return vertex.copy()
    t = -vertex[1] / light_dir[1]
    return vertex + light_dir * t

def draw_floor_lines(floor_limit):
    floor_limit_ancho = 2
    """
    Dibuja el piso como un cuadrado lleno.
    El piso se extiende desde -floor_limit hasta floor_limit en los ejes X y Z,
    y se renderiza con un color gris (70% opaco).
    """
    # Color gris con un 70% de opacidad (transparencia del 30%)
    glColor4f(0, 0, 0, 0.3)
    glBegin(GL_QUADS)
    glVertex3f(-floor_limit, 0, -floor_limit_ancho)
    glVertex3f(10, 0, -floor_limit_ancho)
    glVertex3f(10, 0, floor_limit_ancho)
    glVertex3f(-floor_limit, 0, floor_limit_ancho)
    glEnd()


def draw_text(x, y, text, font):
    """
    Dibuja un texto en pantalla en la posición (x,y).
    Se utiliza la función pygame.font para renderizar el texto y luego se usa glDrawPixels para dibujarlo.
    """
    text_surface = font.render(text, True, (255, 255, 255))
    text_data = pygame.image.tostring(text_surface, "RGBA", True)
    glWindowPos2d(x, y)
    glDrawPixels(text_surface.get_width(), text_surface.get_height(), GL_RGBA, GL_UNSIGNED_BYTE, text_data)

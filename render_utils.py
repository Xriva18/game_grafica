# render_utils.py
import pygame
from OpenGL.GL import *
from OpenGL.GLU import *
import numpy as np
import math

def rotation_z(angle):
    """Devuelve la matriz de rotación 3x3 alrededor del eje Z."""
    c = math.cos(angle)
    s = math.sin(angle)
    return np.array([[c, -s, 0],
                     [s,  c, 0],
                     [0,  0, 1]], dtype=float)

def backface_cull(triangles, vertices, cam_pos):
    """Devuelve los triángulos que miran hacia la cámara."""
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
    """Ordena los triángulos de más lejos a más cerca según la profundidad (z)."""
    tri_depths = []
    for tri in triangles:
        z_avg = (vertices[tri[0]][2] + vertices[tri[1]][2] + vertices[tri[2]][2]) / 3.0
        tri_depths.append((tri, z_avg))
    tri_depths.sort(key=lambda t: t[1], reverse=True)
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

def draw_floor_lines(floor_limit, spacing=5):
    """Dibuja líneas del piso en el rango [-floor_limit, floor_limit]."""
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

def draw_text(x, y, text, font):
    """Dibuja texto en la ventana en la posición (x,y) en píxeles."""
    text_surface = font.render(text, True, (255, 255, 255))
    text_data = pygame.image.tostring(text_surface, "RGBA", True)
    glWindowPos2d(x, y)
    glDrawPixels(text_surface.get_width(), text_surface.get_height(), GL_RGBA, GL_UNSIGNED_BYTE, text_data)

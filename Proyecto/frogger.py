import pygame
import time
import random
import math

# =======================
# Funciones para el cubo 3D
# =======================

def rotate_x(vertex, angle):
    """Rota el vértice (x,y,z) alrededor del eje X usando:
       y' = y*cos(angle) - z*sin(angle)
       z' = y*sin(angle) + z*cos(angle)
    """
    x, y, z = vertex
    y_new = y * math.cos(angle) - z * math.sin(angle)
    z_new = y * math.sin(angle) + z * math.cos(angle)
    return (x, y_new, z_new)

def rotate_y(vertex, angle):
    """Rota el vértice (x,y,z) alrededor del eje Y usando:
       x' = x*cos(angle) + z*sin(angle)
       z' = -x*sin(angle) + z*cos(angle)
    """
    x, y, z = vertex
    x_new = x * math.cos(angle) + z * math.sin(angle)
    z_new = -x * math.sin(angle) + z * math.cos(angle)
    return (x_new, y, z_new)

def project(vertex, fov, viewer_distance, screen_center):
    """Proyecta un punto 3D (x,y,z) a 2D usando la fórmula:
       factor = fov / (z + viewer_distance)
       x2d = x * factor + screen_center[0]
       y2d = -y * factor + screen_center[1]
    """
    x, y, z = vertex
    # Evitar división por cero:
    factor = fov / (z + viewer_distance) if (z + viewer_distance) != 0 else fov
    x_proj = x * factor + screen_center[0]
    y_proj = -y * factor + screen_center[1]
    return (int(x_proj), int(y_proj))

def cross(u, v):
    """Producto vectorial entre dos vectores 3D."""
    return (u[1]*v[2] - u[2]*v[1],
            u[2]*v[0] - u[0]*v[2],
            u[0]*v[1] - u[1]*v[0])

def dot(u, v):
    """Producto escalar entre dos vectores."""
    return u[0]*v[0] + u[1]*v[1] + u[2]*v[2]

def orientation(p, q, r):
    """Devuelve el valor del determinante 2D (orientación de tres puntos)."""
    return (q[0] - p[0])*(r[1]-p[1]) - (q[1]-p[1])*(r[0]-p[0])

def convex_hull(points):
    """Calcula la envolvente convexa (algoritmo de gift wrapping) para una lista de puntos 2D."""
    if len(points) <= 3:
        return points[:]
    # Encuentra el punto más a la izquierda
    start = min(points, key=lambda p: p[0])
    hull = [start]
    current = start
    while True:
        candidate = points[0]
        for p in points:
            if p == current:
                continue
            # Si p está más a la izquierda que candidate respecto a current
            if candidate == current or orientation(current, candidate, p) < 0:
                candidate = p
        if candidate == start:
            break
        hull.append(candidate)
        current = candidate
    return hull

def draw_cube(surface, angle_x, angle_y):
    """Dibuja un cubo 3D rotado con sombreado, ocultación de caras y sombra proyectada.
    
    Parámetros de transformación:
      - fov: campo de visión (escala de proyección).
      - viewer_distance: distancia de la cámara.
      - cube_center: traslación en 3D.
      - ground_y: altura del “suelo” donde se proyecta la sombra.
      - screen_center: centro en pantalla donde se dibuja el cubo.
    """
    # Parámetros del cubo
    cube_size = 100  # tamaño total
    half = cube_size / 2
    # Vértices del cubo centrado en (0,0,0)
    vertices = [
        (-half, -half, -half),
        ( half, -half, -half),
        ( half,  half, -half),
        (-half,  half, -half),
        (-half, -half,  half),
        ( half, -half,  half),
        ( half,  half,  half),
        (-half,  half,  half)
    ]
    
    # Definir las caras (índices de vértices)
    faces = [
        (0, 1, 2, 3),  # cara trasera
        (4, 5, 6, 7),  # cara delantera
        (0, 1, 5, 4),  # inferior
        (2, 3, 7, 6),  # superior
        (1, 2, 6, 5),  # derecha
        (0, 3, 7, 4)   # izquierda
    ]
    
    # Parámetros de proyección y posición en pantalla para el cubo demo
    fov = 256
    viewer_distance = 4
    # Trasladamos el cubo en 3D (lo centramos en (0,0,50))
    cube_translation = (0, 0, 50)
    # Centro de dibujo en pantalla (por ejemplo, esquina superior derecha)
    screen_center = (700, 150)
    # Definir el plano "suelo" en y = ground_y (para la sombra)
    ground_y = -60
    
    # Dirección de la luz (no normalizada)
    light = (1, -2, 1)
    # Normalizamos la luz:
    mag = math.sqrt(light[0]**2 + light[1]**2 + light[2]**2)
    light = (light[0]/mag, light[1]/mag, light[2]/mag)
    
    # Transformar cada vértice: rotar en X y Y y luego trasladar
    transformed_vertices = []
    for v in vertices:
        # Aplicar rotación en X y luego en Y
        rx = rotate_x(v, angle_x)
        rxy = rotate_y(rx, angle_y)
        # Trasladar
        transformed = (rxy[0] + cube_translation[0],
                       rxy[1] + cube_translation[1],
                       rxy[2] + cube_translation[2])
        transformed_vertices.append(transformed)
    
    # Proyectar los vértices 3D a 2D
    projected = [ project(v, fov, viewer_distance, screen_center) for v in transformed_vertices ]
    
    # Calcular la sombra: para cada vértice se proyecta sobre el plano y = ground_y usando la dirección de la luz.
    shadow_vertices = []
    for v in transformed_vertices:
        # Evitar división por cero si light[1] es 0
        if light[1] == 0:
            t = 0
        else:
            t = (ground_y - v[1]) / light[1]
        # Proyecta el punto: V_shadow = V + t * light
        shadow_v = (v[0] + t * light[0],
                    ground_y,  # forzamos que esté en el suelo
                    v[2] + t * light[2])
        shadow_vertices.append(shadow_v)
    projected_shadow = [ project(v, fov, viewer_distance, screen_center) for v in shadow_vertices ]
    
    # Calcular la envolvente convexa de los puntos de sombra para dibujar la sombra completa
    shadow_hull = convex_hull(projected_shadow)
    shadow_color = (30, 30, 30)
    pygame.draw.polygon(surface, shadow_color, shadow_hull)
    
    # Para cada cara, determinar visibilidad (back-face culling) y calcular sombreado
    face_list = []
    for face in faces:
        # Obtener los 3 vértices de la cara para calcular la normal
        v0 = transformed_vertices[face[0]]
        v1 = transformed_vertices[face[1]]
        v2 = transformed_vertices[face[2]]
        # Vector de dos aristas:
        edge1 = (v1[0]-v0[0], v1[1]-v0[1], v1[2]-v0[2])
        edge2 = (v2[0]-v0[0], v2[1]-v0[1], v2[2]-v0[2])
        normal = cross(edge1, edge2)
        # Para back-face culling usamos la dirección de visión. Supondremos que la cámara mira hacia (0,0,-1)
        view_vector = (0, 0, -1)
        if dot(normal, view_vector) >= 0:
            continue  # cara oculta
        # Calcular el promedio de z para la cara (para el algoritmo del pintor)
        avg_z = sum([ transformed_vertices[i][2] for i in face ]) / len(face)
        # Calcular la iluminación: la intensidad depende del ángulo entre la normal y la luz.
        intensity = -dot(normal, light)
        intensity = max(0.1, min(1, intensity))
        # Color base (puedes ajustar)
        base_color = (200, 200, 200)
        face_color = (int(base_color[0]*intensity),
                      int(base_color[1]*intensity),
                      int(base_color[2]*intensity))
        # Obtener la proyección 2D de los vértices de la cara
        face_proj = [ projected[i] for i in face ]
        face_list.append((avg_z, face_proj, face_color))
    
    # Ordenar las caras de acuerdo al promedio de z (painter algorithm: de atrás a adelante)
    face_list.sort(key=lambda f: f[0])
    for _, poly, color in face_list:
        pygame.draw.polygon(surface, color, poly)
        # Dibujar borde para evidenciar la línea (ocultamiento de líneas)
        pygame.draw.polygon(surface, (0,0,0), poly, 1)

# =======================
# Código original del juego de la ranita (Crocki Crocki)
# =======================

# Inicialización
pygame.init()

# Dimensiones de la pantalla
pantallaw = 800
pantallah = 600

# Colores
fondo = (50, 50, 50)
white = (255, 255, 255)
marco = (100, 100, 200)
vereda = (40, 39, 39)
selva = (10, 150, 10)
agua_c = (100, 100, 230)

# Carga de imágenes
crocki_img = pygame.image.load('crockicrocki.png')
carr = pygame.image.load('carr.png')
carl = pygame.image.load('carl.png')
tortuga = pygame.image.load('tortugas.png')
arbol = pygame.image.load('arbol.png')

# Lista para los “crockis” que logren llegar arriba
crockis = []

# Creación de la ventana
areajuego = pygame.display.set_mode((pantallaw, pantallah))
pygame.display.set_caption('Crocki Crocki - 800x600')

gametimer = pygame.time.Clock()

def text_objects(text, font):
    textSurface = font.render(text, True, white)
    return textSurface, textSurface.get_rect()

def message_display(text, x, y):
    largetext = pygame.font.Font('freesansbold.ttf', 25)
    TextSurf, TextRect = text_objects(text, largetext)
    TextRect.center = (x, y)
    areajuego.blit(TextSurf, TextRect)

# Función de colisión para autos
def obj_colisiones(a, jposx, w):
    """
    Checa si la rana (jposx..jposx+50) colisiona con un auto que va de 'a'..a+w.
    """
    if jposx >= a and jposx <= a + w:
        return True
    elif (jposx + 50) >= a and (jposx + 50) <= a + w:
        return True
    return False

def game_loop():
    # Variables para la demo del cubo 3D
    cube_angle_x = 0
    cube_angle_y = 0

    # Posición inicial de la rana
    jposx = 750
    jposy = 550

    # Filas de carretera
    auto01y = 350
    auto02y = 400
    auto03y = 450

    # Filas de agua
    agua01y = 100
    agua02y = 150
    agua03y = 200
    agua04y = 250

    # Listas de posiciones X para autos y “troncos”
    auto01 = [100, 300, 500]
    auto02 = [200, 400, 600]
    auto03 = [150, 350, 550]

    agua01 = [100, 400]   # 2 “troncos” en y=100
    agua02 = [200, 500]   # 2 “troncos” en y=150
    agua03 = [100, 300]   # 2 “troncos” en y=200
    agua04 = [250, 550]   # 2 “troncos” en y=250

    # Velocidades de movimiento (x)
    g1mx = 5
    g2mx = 3
    g3mx = -4

    ciclos = 3000
    puntaje = 0

    termino = False

    while not termino:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                termino = True
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_0:
                    termino = True
                if event.key == pygame.K_LEFT:
                    jposx = max(0, jposx - 50)
                elif event.key == pygame.K_RIGHT:
                    jposx = min(750, jposx + 50)
                elif event.key == pygame.K_UP:
                    jposy = max(50, jposy - 50)
                elif event.key == pygame.K_DOWN:
                    jposy = min(550, jposy + 50)

        # COLISIONES CON AUTOS
        if jposy == auto03y:
            for a in auto03:
                if obj_colisiones(a, jposx, 50):
                    termino = True
                    break
        if jposy == auto02y:
            for a in auto02:
                if obj_colisiones(a, jposx, 50):
                    termino = True
                    break
        if jposy == auto01y:
            for a in auto01:
                if obj_colisiones(a, jposx, 50):
                    termino = True
                    break

        # COLISIONES EN EL AGUA
        frog_rect = pygame.Rect(jposx, jposy, 50, 50)
        if jposy == agua04y:
            notenelagua = False
            for a in agua04:
                log_rect = pygame.Rect(a, agua04y, 100, 50)
                if frog_rect.colliderect(log_rect):
                    notenelagua = True
                    jposx += g3mx
                    break
            if not notenelagua:
                termino = True

        if jposy == agua03y:
            notenelagua = False
            for a in agua03:
                log_rect = pygame.Rect(a, agua03y, 100, 50)
                if frog_rect.colliderect(log_rect):
                    notenelagua = True
                    jposx += g2mx
                    break
            if not notenelagua:
                termino = True

        if jposy == agua02y:
            notenelagua = False
            for a in agua02:
                log_rect = pygame.Rect(a, agua02y, 100, 50)
                if frog_rect.colliderect(log_rect):
                    notenelagua = True
                    jposx += g1mx
                    break
            if not notenelagua:
                termino = True

        if jposy == agua01y:
            notenelagua = False
            for a in agua01:
                log_rect = pygame.Rect(a, agua01y, 100, 50)
                if frog_rect.colliderect(log_rect):
                    notenelagua = True
                    jposx += g2mx
                    break
            if not notenelagua:
                termino = True

        # LLEGADA A LA META (selva)
        if jposy == 50:
            puntaje += 20000
            jposy = 550
            jposx = 750
            crockis.append(jposx)

        # MOVIMIENTO de autos
        for i in range(len(auto01)):
            auto01[i] += g1mx
            if auto01[i] > 800:
                auto01[i] = -50
        for i in range(len(auto02)):
            auto02[i] += g2mx
            if auto02[i] > 800:
                auto02[i] = -50
        for i in range(len(auto03)):
            auto03[i] += g3mx
            if auto03[i] < -50:
                auto03[i] = 800

        # MOVIMIENTO de troncos en el agua
        for i in range(len(agua01)):
            agua01[i] += g2mx
            if agua01[i] < -100:
                agua01[i] = 800
            elif agua01[i] > 800:
                agua01[i] = -100

        for i in range(len(agua02)):
            agua02[i] += g1mx
            if agua02[i] > 800:
                agua02[i] = -100

        for i in range(len(agua03)):
            agua03[i] += g2mx
            if agua03[i] < -100:
                agua03[i] = 800
            elif agua03[i] > 800:
                agua03[i] = -100

        for i in range(len(agua04)):
            agua04[i] += g3mx
            if agua04[i] < -100:
                agua04[i] = 800
            elif agua04[i] > 800:
                agua04[i] = -100

        # DIBUJAR FONDO Y MARCOS
        areajuego.fill(fondo)
        pygame.draw.rect(areajuego, marco, [0, 0, pantallaw, 50])
        pygame.draw.rect(areajuego, marco, [0, 550, pantallaw, 50])
        pygame.draw.rect(areajuego, selva, [0, 50, pantallaw, 50])
        pygame.draw.rect(areajuego, agua_c, [0, 100, pantallaw, 200])
        pygame.draw.rect(areajuego, vereda, [0, 300, pantallaw, 50])
        pygame.draw.rect(areajuego, (70, 70, 70), [0, 350, pantallaw, 150])
        pygame.draw.rect(areajuego, vereda, [0, 500, pantallaw, 50])

        message_display(f"Ciclos restantes: {ciclos}", 250, 580)
        message_display(f"Puntaje de Crockis salvados: {puntaje}", 250, 20)

        # DIBUJAR OBJETOS DEL AGUA
        for a in agua01:
            areajuego.blit(tortuga, (a, agua01y))
        for a in agua02:
            areajuego.blit(arbol, (a, agua02y))
        for a in agua03:
            areajuego.blit(tortuga, (a, agua03y))
        for a in agua04:
            areajuego.blit(arbol, (a, agua04y))

        # DIBUJAR RANA
        areajuego.blit(crocki_img, (jposx, jposy))

        # DIBUJAR AUTOS
        for a in auto01:
            areajuego.blit(carr, (a, auto01y))
        for a in auto02:
            areajuego.blit(carr, (a, auto02y))
        for a in auto03:
            areajuego.blit(carl, (a, auto03y))

        # DIBUJAR CROCKIS SALVADOS ARRIBA
        for a in crockis:
            areajuego.blit(crocki_img, (a, 50))
        
        # --- DIBUJO DEL CUBO 3D (DEMO DE SOMBRAS, ROTACIÓN, OCULTAMIENTO y PAINTER ALGORITHM) ---
        draw_cube(areajuego, cube_angle_x, cube_angle_y)
        # Actualizar ángulos de rotación
        cube_angle_x += 0.01
        cube_angle_y += 0.02

        pygame.display.update()
        gametimer.tick(60)
        ciclos -= 1
        if ciclos <= 0:
            termino = True

    if puntaje == 0:
        ciclos = 0
    return ciclos + puntaje

def main():
    areajuego.fill(fondo)
    score = game_loop()
    time.sleep(2)
    areajuego.fill(fondo)
    for a in crockis:
        areajuego.blit(crocki_img, (a, 50))
    message_display("Puntaje total: " + str(score), 400, 300)
    pygame.display.update()
    print("Tu score fue:", score)
    time.sleep(4)
    pygame.quit()
    quit()

if __name__ == "__main__":
    main()

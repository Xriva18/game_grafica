from ursina import *
import random

app = Ursina()


# Agregar música de fondo
musica_fondo = Audio('Music.mp3', autoplay=True, loop=True)
musica_fondo.volume = 0.5  # Ajusta volumen


# Función para crear un modelo de pirámide personalizado.
def create_pyramid():
    vertices = [
        Vec3(0, 1, 0),      # vértice superior
        Vec3(-1, -1, 1),    # base frontal izquierda
        Vec3(1, -1, 1),     # base frontal derecha
        Vec3(1, -1, -1),    # base trasera derecha
        Vec3(-1, -1, -1)    # base trasera izquierda
    ]
    triangles = [
        (0, 1, 2),   # cara frontal
        (0, 2, 3),   # cara derecha
        (0, 3, 4),   # cara trasera
        (0, 4, 1),   # cara izquierda
        (1, 2, 3),   # base (triángulo 1)
        (1, 3, 4)    # base (triángulo 2)
    ]
    return Mesh(vertices=vertices, triangles=triangles)

# -- Variables de estado --
game_over_flag = False
game_over_text = None

# -- Configuración del jugador --
jugador = Entity(
    model='cube',
    color=color.azure,
    scale=1,
    position=(0,0,0),  # El pivot se ubicará aquí
    origin_y=-0.5,     # Ajuste para que la base quede en y=0
    collider='box'
)
jugador.velocidad_y = 0
jugador.altura_salto = 0.3
jugador.gravedad = 0.01
jugador.en_suelo = True

# -- Suelo (camino) --
suelo = Entity(
    model='plane',
    scale=(1000,1,10),
    texture='white_cube',
    texture_scale=(1000,10),
    collider='box',
    position=(0,0,0),
    color=color.cyan  # Aquí se define el color negro
)


# -- Obstáculos: pirámides --
obstaculos = []
next_obstacle_spawn = 5

# Generar un primer obstáculo.
initial_obstacle = Entity(
    model=create_pyramid(),
    color=color.red,
    scale=0.5,
    position=(10, 0.5, 0),
    collider='box'
)
obstaculos.append(initial_obstacle)

# -- Rastro del jugador --
puntos_rastro = []
rastro = Entity(model=Mesh(), color=color.yellow, mode='line')

# -- Configuración de la cámara --
camera.position = Vec3(jugador.x - 10, jugador.y + 5, -20)
camera.look_at(jugador)

def game_over():
    """Muestra texto de Game Over y activa la bandera."""
    global game_over_flag, game_over_text
    musica_fondo.stop()
    game_over_flag = True
    game_over_text = Text(
        text='Game Over\nPulsa C para reiniciar',
        origin=(0, 0),
        scale=2,
        background=True,
        color=color.white
    )

def reset_game():
    global game_over_flag, next_obstacle_spawn, game_over_text
    
    # Volver a reproducir la música desde el inicio
    musica_fondo.play()

    # 1. Ocultar/Destruir el texto de Game Over
    if game_over_text:
        destroy(game_over_text)
    
    game_over_flag = False
    
    # 2. Resetear al jugador
    jugador.x = 0
    jugador.y = 0
    jugador.velocidad_y = 0
    jugador.en_suelo = True
    
    # 3. Limpiar obstáculos en pantalla
    for obs in obstaculos:
        destroy(obs)
    obstaculos.clear()
    
    # 4. Reiniciar la posición de "spawn"
    next_obstacle_spawn = 5

    # 5. Volver a crear el obstáculo inicial
    initial_obstacle = Entity(
        model=create_pyramid(),
        color=color.red,
        scale=0.5,
        position=(10, 0.5, 0),
        collider='box'
    )
    obstaculos.append(initial_obstacle)

    # 6. Vaciar el rastro y reiniciarlo
    puntos_rastro.clear()
    rastro.model = Mesh(vertices=[], mode='line')


def update():
    global next_obstacle_spawn

    if game_over_flag:
        return  # No actualizar si estamos en Game Over

    # Movimiento continuo hacia adelante
    jugador.x += 0.07

    # Aplicar gravedad si no está en el suelo
    if not jugador.en_suelo:
        jugador.velocidad_y -= jugador.gravedad
    jugador.y += jugador.velocidad_y

    # Comprobar si aterriza en el suelo
    if jugador.y < 0:
        jugador.y = 0
        jugador.velocidad_y = 0
        jugador.en_suelo = True

    # Actualizar rastro del jugador
    puntos_rastro.append(Vec3(jugador.x, jugador.y, jugador.z))
    if len(puntos_rastro) > 1:
        rastro.model = Mesh(vertices=puntos_rastro, mode='line')

    # Actualizar la posición de la cámara
    camera.position = Vec3(jugador.x - 10, jugador.y + 5, -20)
    camera.look_at(jugador)

    # Verificar colisión con cada obstáculo
    for obstaculo in obstaculos:
        if jugador.intersects(obstaculo).hit:
            game_over()
            return

    # Generar nuevos obstáculos dinámicamente
    if jugador.x > next_obstacle_spawn:
        spawn_x = jugador.x + 15
        obstaculo = Entity(
            model=create_pyramid(),
            color=color.red,
            scale=0.5,
            position=(spawn_x, 0.5, 0),
            collider='box'
        )
        obstaculos.append(obstaculo)
        next_obstacle_spawn += random.uniform(10, 20)

    # Eliminar obstáculos que ya quedaron muy atrás
    for obstaculo in obstaculos.copy():
        if obstaculo.x < jugador.x - 20:
            destroy(obstaculo)
            obstaculos.remove(obstaculo)

def input(key):
    # Si está en Game Over y se pulsa 'c', reiniciamos la partida
    if game_over_flag and key == 'c':
        reset_game()
        return
    
    # De lo contrario, si no está en Game Over, el 'space' es para saltar
    if key == 'space' and jugador.en_suelo and not game_over_flag:
        jugador.velocidad_y = jugador.altura_salto
        jugador.en_suelo = False

app.run()

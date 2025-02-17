# 3D Runner: Juego de Cubo y Obstáculos

Este proyecto es un juego en 3D donde controlas un cubo que avanza por un mundo lleno de obstáculos. El jugador puede saltar para evitar colisiones y, al impactar con un obstáculo, el cubo se fragmenta en pequeños cubos, simulando una explosión. El juego implementa físicas simples (gravedad y salto), renderizado en 3D con técnicas como *backface culling* y el algoritmo del pintor (*painter's algorithm*), además de efectos de sombra y control dinámico de la cámara.

## Características

- **Juego en 3D:** Vista en perspectiva con cámara dinámica.
- **Jugador y Obstáculos:** 
  - El jugador se representa como un cubo.
  - Los obstáculos se representan como pirámides.
- **Física Básica:** Gravedad, salto y detección de colisiones.
- **Animación de Explosión:** Al chocar, el cubo se fragmenta en mini cubos que se dispersan con efectos de rotación y velocidad.
- **Renderizado Avanzado:** Uso de técnicas de *backface culling* y *painter's algorithm* para el dibujo correcto de las superficies.
- **Controles y Puntuación:** 
  - Sistema de puntuación que aumenta conforme se evitan obstáculos.
  - Registro del récord (high score).
- **Sonido y Música:** Integración de música de fondo (archivo `Music.mp3`) y efectos de audio.
- **Interacción:** Control del salto con la barra espaciadora, ajuste de la perspectiva con las flechas y reinicio del juego con la tecla **R**.

## Requisitos

Asegúrate de tener instalado Python 3.x. Además, este proyecto depende de las siguientes librerías:

- **Ursina**  
  Instalación:  
  ```bash
  pip install ursina
  ```

- **Pygame**  
  Instalación:  
  ```bash
  pip install pygame
  ```

- **PyOpenGL**  
  Instalación:  
  ```bash
  pip install PyOpenGL
  ```

- **NumPy**  
  Instalación:  
  ```bash
  pip install numpy
  ```

> **Nota:** Aunque se incluye la instalación de Ursina en el README, la mayor parte del renderizado y la lógica del juego se basan en Pygame y PyOpenGL.

## Instalación

1. **Clona el repositorio:**

   ```bash
   git clone https://github.com/tu_usuario/tu_repositorio.git
   cd tu_repositorio
   ```

2. **Instala las dependencias:**

   Puedes instalar todas las librerías requeridas ejecutando:

   ```bash
   pip install ursina pygame PyOpenGL numpy
   ```

   O, si prefieres, crear un archivo `requirements.txt` con lo siguiente:

   ```txt
   ursina
   pygame
   PyOpenGL
   numpy
   ```

   Y luego ejecutar:

   ```bash
   pip install -r requirements.txt
   ```

## Ejecución

Para iniciar el juego, ejecuta:

```bash
python main.py
```

Asegúrate de que el archivo de música `Music.mp3` se encuentre en el directorio raíz del proyecto.

## Estructura del Proyecto

- **README.md**  
  Este archivo, que describe el proyecto, su instalación y uso.

- **config.py**  
  Contiene constantes y configuraciones globales (dimensiones de pantalla, parámetros de física, escalas, etc.).

- **game_objects.py**  
  Define los objetos del juego:
  - **Player:** El cubo controlado por el jugador.
  - **Obstacle:** Obstáculos representados como pirámides.
  - **Fragment:** Mini cubos que se generan durante la animación de explosión.
  - Función `create_fragments_from_player` para generar los fragmentos tras una colisión.

- **geometry.py**  
  Configura Pygame y OpenGL, gestiona el bucle principal del juego, actualiza la lógica de movimiento, controla estados (running, exploding, game_over) y renderiza la escena.

- **main.py**  
  Archivo principal que inicializa la música de fondo, configura la ventana de juego y ejecuta el ciclo principal. Es similar en estructura a `geometry.py`, pero incluye la integración del audio.

- **render_utils.py**  
  Incluye funciones de ayuda para el renderizado:
  - Matrices de rotación.
  - Backface culling.
  - Ordenación de triángulos (painter's algorithm).
  - Dibujo de objetos, sombras y líneas del piso.
  - Funciones para renderizar texto en pantalla.

## Controles

- **Espacio:** Saltar (disponible cuando el jugador está en el suelo).
- **Flechas (←, →, ↑, ↓):** Cambiar la perspectiva de la cámara.
- **R:** Reiniciar el juego tras una colisión o al finalizar la animación de explosión.
- **ESC:** Salir del juego.

## Desarrolladores

- **Guanoluisa Fernando** [@Xriva18]
- **Aragon Mikel**
- **Pallango Brayan**

---

¡Disfruta del juego y diviértete mientras mejoras tu puntuación!

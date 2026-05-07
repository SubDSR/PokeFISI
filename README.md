# PokeFISI

Simulador académico de combates por turnos inspirado en Pokémon. El proyecto combina un motor de batalla en Python con dos formas de uso:

- interfaz por consola para partidas y experimentos,
- interfaz web estática servida por un servidor HTTP ligero incluido en el backend.

## Qué hace el proyecto

PokeFISI genera equipos aleatorios de Pokémon, ejecuta combates por turnos y muestra el resultado en consola o en navegador. El sistema está pensado como una base académica para experimentar con:

- agentes de decisión,
- resolución de turnos,
- simulación por lotes,
- visualización del estado de batalla.

## Características principales

- Motor de batalla por turnos en Python.
- Equipos de tamaño `3 vs 3` o `4 vs 4`.
- Catálogo estático de Pokémon y movimientos.
- Selección aleatoria de equipo y de 4 movimientos por Pokémon.
- Agente humano, aleatorio y heurístico.
- Modo consola.
- Modo experimento por lotes.
- Servidor web con API para jugar `humano vs IA` o ver `IA vs IA`.
- Exportación de frames para replay.

## Requisitos

- Python 3.10 o superior.

No hay dependencias externas declaradas en el repositorio. El proyecto usa solo librerías estándar de Python y archivos estáticos HTML/CSS/JS.

## Estructura del proyecto

```text
backend/
  agents/        Agentes de decisión (humano, random, heurístico)
  battle/        Motor, estado, modelos y cálculo de daño
  data/          Catálogos estáticos de Pokémon y movimientos
  experiments/   Simulaciones por lotes
  ui/            Salidas de consola, replay y serialización de vista
  main.py        Punto de entrada CLI
  server.py      Servidor HTTP y API web
  session.py     Sesiones interactivas para el frontend

frontend/
  assets/        Recursos visuales
  web/
    index.html   Interfaz principal
    app.js       Cliente web y control de combate
    styles.css   Estilos de la interfaz
```

## Cómo iniciar el proyecto

### 1. Ejecutar una batalla en consola

```bash
python -m backend.main --mode battle
```

Ejemplo con jugador humano en consola:

```bash
python -m backend.main --mode battle --agent1 human --agent2 heuristic
```

Ejemplo silencioso:

```bash
python -m backend.main --mode battle --agent1 heuristic --agent2 random --quiet --message-delay 0 --decision-delay 0
```

### 2. Ejecutar experimentos por lotes

```bash
python -m backend.main --mode experiment --battles 50 --team-size 3 --agent1 random --agent2 heuristic
```

Esto imprime un resumen con:

- número de batallas,
- victorias por jugador,
- tasa de victorias,
- promedio de turnos.

### 3. Iniciar la interfaz web

```bash
python -m backend.main --mode serve --host 127.0.0.1 --port 8000
```

Luego abre en el navegador:

```text
http://127.0.0.1:8000
```

Desde la pantalla inicial puedes:

- elegir tamaño de equipo,
- jugar `Human vs IA`,
- mirar `IA vs IA` con avance manual o automático.

### 4. Exportar replay

```bash
python -m backend.main --mode battle --ui replay
```

Por defecto, el replay se exporta en:

```text
frontend/web/replay_data.js
```

También puedes cambiar la ruta:

```bash
python -m backend.main --mode battle --ui replay --replay-output frontend/web/mi_replay.js
```

Nota: el exportador genera los frames del combate, pero la interfaz web actual no carga automáticamente `replay_data.js`. El modo web principal consume sesiones en vivo por API.

## Parámetros disponibles

El punto de entrada `backend.main` acepta estos argumentos:

- `--mode`: `battle`, `experiment`, `serve`
- `--ui`: `console`, `replay`
- `--team-size`: `3` o `4`
- `--agent1`: `random`, `heuristic`, `human`
- `--agent2`: `random`, `heuristic`, `human`
- `--battles`: número de simulaciones en modo experimento
- `--seed`: semilla para reproducibilidad
- `--quiet`: salida resumida para batalla por consola
- `--message-delay`: pausa entre mensajes de UI de consola
- `--decision-delay`: pausa al mostrar decisiones en consola
- `--replay-output`: archivo de salida del replay
- `--host`: host del servidor web
- `--port`: puerto del servidor web

## Cómo funciona internamente

### 1. Datos estáticos

`backend/data/` define el catálogo base:

- `pokemon.py`: especies, stats base, tipos, sprites y pool de movimientos.
- `moves.py`: poder, precisión, tipo, descripción y PP.

Cada Pokémon de batalla se construye a partir de una especie y recibe 4 movimientos elegidos aleatoriamente desde su pool.

### 2. Estado de batalla

`backend/battle/state.py` mantiene:

- los dos equipos,
- el turno actual,
- el log del combate,
- las acciones legales para cada jugador.

Las acciones posibles son:

- `move`
- `switch`
- `struggle`

Si el Pokémon activo se debilita, solo se permiten cambios. Si no quedan movimientos con PP, se habilita `Struggle`.

### 3. Resolución de turnos

`backend/battle/engine.py` resuelve cada turno con estas reglas:

1. Atiende cambios forzados si un Pokémon activo está debilitado.
2. Pide una acción a cada agente.
3. Ordena acciones.
4. Ejecuta cambios antes que ataques.
5. Para ataques, usa la velocidad como criterio principal.
6. Si hay empate práctico en el orden, agrega desempate aleatorio.

### 4. Fórmula de daño

El daño simplificado está en `backend/battle/damage.py`:

```text
Damage = (Attack / Defense_op) * BasePower - Speed_op * K
K = 0.5
```

El daño final nunca baja de `1`.

### 5. Agentes

`backend/agents/` incluye:

- `RandomAgent`: elige una acción legal al azar.
- `HeuristicAgent`: evalúa el daño esperado de cada acción y elige la que maximiza `HP_total_propio - HP_total_rival`.
- `HumanAgent`: pide la acción por teclado en consola.

### 6. Capa web

`backend/server.py` levanta un servidor HTTP con dos responsabilidades:

- servir `frontend/web/index.html`, `app.js`, `styles.css` y assets,
- exponer la API de combate.

`backend/session.py` mantiene sesiones activas en memoria. Cada sesión tiene:

- `session_id`,
- estado de batalla,
- generador aleatorio,
- recolector de frames para animar la UI.

El frontend (`frontend/web/app.js`) hace peticiones `fetch` a la API y renderiza:

- sprites,
- HP,
- party,
- mensaje de batalla,
- panel de acciones,
- animaciones de ataque, cambio y debilitamiento.

## API disponible

### `GET /api/health`

Devuelve:

```json
{"status": "ok"}
```

### `POST /api/battle/start`

Body:

```json
{
  "mode": "human-vs-ai",
  "teamSize": 3,
  "seed": 7
}
```

`mode` acepta:

- `human-vs-ai`
- `ai-vs-ai`

Respuesta: estado actual de la sesión, frames iniciales y `sessionId`.

### `POST /api/battle/{sessionId}/step`

Avanza un turno en modo `ai-vs-ai`.

### `POST /api/battle/{sessionId}/action`

Recibe la acción humana en modo `human-vs-ai`.

Body:

```json
{
  "actionType": "move",
  "index": 0
}
```

## Modos de uso reales del proyecto

### Consola

- Puede usar agentes `random`, `heuristic` o `human`.
- Sirve para depurar el flujo del motor.

### Experimento

- Ejecuta muchas batallas seguidas.
- Actualmente solo crea agentes `random` y `heuristic`.
- Está pensado para comparar rendimiento básico.

### Web

- `human-vs-ai`: el jugador humano decide por botones y la IA rival es aleatoria.
- `ai-vs-ai`: ambos lados son agentes aleatorios y la UI actúa como visor.

## Limitaciones actuales

El simulador implementa una versión simplificada del combate. No incluye:

- ventajas o resistencias por tipo,
- estados alterados,
- habilidades,
- objetos,
- críticos,
- efectos secundarios de movimientos,
- cambio de stats,
- persistencia de sesiones,
- integración visible del archivo exportado por `--ui replay` dentro del frontend actual.

Además, las sesiones web viven solo en memoria del proceso del servidor.

## Flujo recomendado para probarlo

1. Ejecuta el servidor web.
2. Abre `http://127.0.0.1:8000`.
3. Prueba `Human vs IA` para validar interacción.
4. Prueba `IA vs IA` con `AUTO` y `NEXT` para observar la secuencia de frames.
5. Ejecuta un experimento por consola para comparar agentes.

## Archivos clave para entender el código

- `backend/main.py`: orquestación principal y argumentos CLI.
- `backend/server.py`: servidor HTTP y rutas API.
- `backend/session.py`: ciclo de vida de sesión web.
- `backend/battle/engine.py`: resolución del combate.
- `backend/battle/state.py`: acciones legales y estado del turno.
- `backend/battle/damage.py`: fórmula de daño.
- `backend/ui/view_state.py`: contrato serializable entre backend y frontend.
- `frontend/web/app.js`: controlador del cliente web.

## Verificación rápida

Comandos comprobados sobre este repositorio:

```bash
python -m backend.main --mode experiment --battles 3 --team-size 3 --agent1 random --agent2 heuristic --seed 7
python -m backend.main --mode battle --agent1 heuristic --agent2 random --quiet --message-delay 0 --decision-delay 0 --seed 7
python -m backend.main --mode serve --host 127.0.0.1 --port 8000
```

También responde correctamente el health check:

```text
GET /api/health -> {"status": "ok"}
```

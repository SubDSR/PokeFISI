# Conexion tecnica backend-frontend - PokeFISI

## Objetivo

Conectar directamente el backend actual ubicado en `backend/` con el frontend nuevo ubicado en `frontend/retro-poke-battle-main/`, usando el backend como fuente canonica de datos y reglas de combate, sin reutilizar referencias de frontends eliminados.

La integracion debe conservar la estructura visual, componentes y animaciones actuales del frontend nuevo:

- `frontend/retro-poke-battle-main/src/lib/pokefisi/PokefisiApp.tsx`
- `frontend/retro-poke-battle-main/src/lib/pokefisi/components.tsx`
- `frontend/retro-poke-battle-main/src/styles.css`

No se debe reconstruir la interfaz ni cambiar el lenguaje visual retro/pixel art. La conexion debe reemplazar la simulacion local del frontend por datos y resultados provenientes del backend.

---

## Estado Actual

### Backend

El backend contiene la logica principal de batalla y una API HTTP local operativa.

| Archivo | Responsabilidad | Estado |
|---|---|---|
| `backend/server.py` | Servidor HTTP con rutas `/api/health`, `/api/battle/start`, `/api/battle/{sessionId}/step`, `/api/battle/{sessionId}/action` | Funcional. Faltan rutas `/api/pokemon` y `/api/config`. Referencia obsoleta a `frontend/web` sin CORS configurado. |
| `backend/session.py` | Manejo de sesiones, frames de batalla, acciones humanas e IA | Funcional. `BattleSession.__init__` no acepta `player_pokemon_ids`; siempre usa `build_balanced_teams` sin distincion de modo. |
| `backend/config.py` | Mapeo de dificultad a agente IA | Correcto. `VALID_DIFFICULTIES = {"easy", "medium", "hard", "sobrevilla"}`. |
| `backend/battle/factory.py` | Construccion de equipos y Pokemon de batalla desde `POKEDEX` | Correcto. `build_team_from_species()` existe (linea 117) pero nunca es llamada para equipos del jugador. |
| `backend/ui/view_state.py` | Serializacion del estado de batalla para UI | Correcto. Serializa `currentHp`, `maxHp`, `spriteUrl`, `moves`, `actionGroups`. |
| `backend/data/pokemon.py` | Fuente canonica de Pokemon disponibles | Correcto. `POKEDEX` con 30 Pokemon (solo formas base). |

### Frontend

El frontend nuevo esta centralizado en:

| Archivo | Responsabilidad | Estado |
|---|---|---|
| `src/lib/pokefisi/PokefisiApp.tsx` | Flujo de pantallas, seleccion, batalla y resultado | Funcional visualmente. Contiene motor de combate local completo (`calcDamage`, `chooseAIMove`, `runTurn`, `doAttack`). No realiza ninguna llamada HTTP al backend. |
| `src/lib/pokefisi/data.ts` | Tipos, pool local de Pokemon y dificultad local | Contiene `POKEMON_POOL` hardcodeada con **60 Pokemon** (incluye evoluciones no presentes en `POKEDEX`). El tipo `Difficulty` usa `"maestro"` en lugar de `"maestro-sobrevilla"`. No tiene mapeo `DIFFICULTY_TO_API`. |
| `src/lib/pokefisi/components.tsx` | Componentes visuales reutilizables | Correcto. Sin cambios necesarios. |
| `src/styles.css` | Animaciones y estilo pixel art | Correcto. Todas las clases de animacion definidas y funcionales. |
| `src/lib/pokefisi/api.ts` | Cliente HTTP centralizado | **No existe.** Debe crearse. |

---

## Brechas Identificadas

La integracion **no esta implementada**. El frontend opera como simulador independiente y no consulta el backend en ningun flujo. Las siguientes brechas bloquean la integracion:

### Backend

| ID | Brecha | Archivo | Detalle |
|---|---|---|---|
| B1 | Falta ruta `GET /api/pokemon` | `server.py` | El frontend no puede obtener el Pokédex desde el backend. |
| B2 | Falta ruta `GET /api/config` | `server.py` | El frontend duplica la configuracion de dificultades. Recomendado, no obligatorio. |
| B3 | `BattleSession` no acepta equipo del jugador | `session.py:103` | `__init__` no tiene parametro `player_pokemon_ids`. Para `human-vs-ai` siempre genera equipo aleatorio ignorando la seleccion del usuario. |
| B4 | Sin CORS ni proxy configurado | `server.py` | El servidor no envia cabeceras `Access-Control-Allow-Origin`, lo que bloquea llamadas desde el servidor de Vite en desarrollo. |
| B5 | Referencia obsoleta a `frontend/web` | `server.py:18` | Las constantes `FRONTEND_WEB_DIR` y `FRONTEND_ASSET_DIR` apuntan a un directorio eliminado. |

### Frontend

| ID | Brecha | Archivo | Detalle |
|---|---|---|---|
| F1 | `api.ts` no existe | `src/lib/pokefisi/` | No hay cliente HTTP. El frontend nunca llama al backend. |
| F2 | `POKEMON_POOL` desalineada con `POKEDEX` | `data.ts:214` | El frontend tiene 60 Pokemon (incluye ivysaur, charizard, blastoise y otras evoluciones ausentes en `POKEDEX`). El backend solo reconoce 30 Pokemon base. |
| F3 | Nombre de dificultad inconsistente | `data.ts:236`, `PokefisiApp.tsx:249` | El frontend usa `"maestro"` y `"Maestro Pokemon"`. El documento y el backend esperan `"maestro-sobrevilla"` con conversion a `"sobrevilla"`. |
| F4 | Sin mapeo `DIFFICULTY_TO_API` | `data.ts` | No existe conversion de valores visuales (`facil`, `medio`, `dificil`, `maestro-sobrevilla`) a valores de API (`easy`, `medium`, `hard`, `sobrevilla`). |
| F5 | Motor de combate local activo | `PokefisiApp.tsx:46-674` | `calcDamage`, `chooseAIMove`, `runTurn` y `doAttack` ejecutan toda la batalla en el cliente. El backend no participa en ningun turno. |
| F6 | Sin reproduccion de frames | `PokefisiApp.tsx` | No existe mecanismo para recibir, iterar ni animar la lista de `frames` devuelta por el backend. |
| F7 | Sin seguimiento de `sessionId` | `PokefisiApp.tsx` | No se almacena ni usa el `sessionId` de sesion porque no se inicia ninguna sesion contra el backend. |

---

## Principios De Integracion

1. El backend es la fuente de verdad para Pokemon, movimientos, stats, equipos, acciones legales, turnos y resultado.
2. El frontend conserva la estructura visual actual y solo cambia su fuente de datos.
3. El frontend no debe tener un pool hardcodeado distinto al de `backend/data/pokemon.py`.
4. Las dificultades visibles del dropdown deben mapearse a los agentes reales del backend.
5. En modo `Human vs IA`, los Pokemon seleccionables deben ser exactamente los definidos en `POKEDEX`.
6. Las animaciones actuales se conservan usando los `frames` y `animation.type` que ya devuelve `BattleSession`.
7. Toda ruta nueva de API debe mantenerse bajo `/api` para separar frontend de backend.

---

## Fuente Canonica De Pokemon

La lista oficial de Pokemon seleccionables es `backend/data/pokemon.py`, especificamente el diccionario `POKEDEX`.

> **Atencion:** El frontend actual (`data.ts`) contiene 60 Pokemon generados localmente incluyendo evoluciones (ivysaur, venusaur, charmeleon, charizard, wartortle, blastoise, etc.) que **no existen en `POKEDEX`**. Al conectar el frontend al backend, `SelectScreen` debe mostrar unicamente los 30 Pokemon del `POKEDEX` cargados desde `GET /api/pokemon`. La `POKEMON_POOL` local debe eliminarse.

Pokemon registrados actualmente en `POKEDEX`:

| ID | Nombre |
|---|---|
| `bulbasaur` | Bulbasaur |
| `charmander` | Charmander |
| `squirtle` | Squirtle |
| `pikachu` | Pikachu |
| `pidgeotto` | Pidgeotto |
| `geodude` | Geodude |
| `psyduck` | Psyduck |
| `growlithe` | Growlithe |
| `oddish` | Oddish |
| `vulpix` | Vulpix |
| `poliwag` | Poliwag |
| `machop` | Machop |
| `abra` | Abra |
| `magnemite` | Magnemite |
| `sandshrew` | Sandshrew |
| `bellsprout` | Bellsprout |
| `rattata` | Rattata |
| `spearow` | Spearow |
| `ekans` | Ekans |
| `nidoranf` | Nidoran F |
| `nidoranm` | Nidoran M |
| `paras` | Paras |
| `venonat` | Venonat |
| `meowth` | Meowth |
| `mankey` | Mankey |
| `tentacool` | Tentacool |
| `ponyta` | Ponyta |
| `slowpoke` | Slowpoke |
| `doduo` | Doduo |
| `seel` | Seel |

---

## Mapeo De Dificultades E IA

El dropdown actual del frontend debe mantenerse visualmente, pero sus valores deben enviarse al backend normalizados.

| Dropdown frontend | Valor frontend | Difficulty API | Agente backend | Implementacion |
|---|---|---|---|---|
| Facil | `facil` | `easy` | `RandomAgent` | IA random |
| Medio | `medio` | `medium` | `HeuristicAgent` | Agente heuristico |
| Dificil | `dificil` | `hard` | `MinimaxAgent` | Minimax con pesos manuales |
| Maestro-Sobrevilla | `maestro-sobrevilla` | `sobrevilla` | `MinimaxAgent` optimizado | Minimax con pesos optimizados |

> **Atencion:** El frontend actual usa `"maestro"` como valor de dificultad (ver `data.ts:236` y `PokefisiApp.tsx:249`). Debe renombrarse a `"maestro-sobrevilla"` para alinearse con el documento y agregar la conversion a `"sobrevilla"` antes de llamar al backend.

En `backend/config.py`, los valores validos actuales son:

```python
VALID_DIFFICULTIES = {"easy", "medium", "hard", "sobrevilla"}
```

Por tanto, el frontend no debe enviar `facil`, `medio`, `dificil` ni `maestro-sobrevilla` directamente a `/api/battle/start`. Debe convertirlos antes.

Mapeo requerido en frontend (`data.ts`):

```ts
export type Difficulty = "facil" | "medio" | "dificil" | "maestro-sobrevilla";

export const DIFFICULTY_TO_API: Record<Difficulty, string> = {
  facil: "easy",
  medio: "medium",
  dificil: "hard",
  "maestro-sobrevilla": "sobrevilla",
};
```

---

## Contratos API

### `GET /api/health`

Ruta existente. Operativa.

```json
{ "status": "ok" }
```

### `GET /api/pokemon`

Ruta nueva. **No implementada en backend.** Debe exponer los Pokemon de `backend/data/pokemon.py` para el selector del frontend.

Respuesta esperada:

```json
{
  "pokemon": [
    {
      "id": "bulbasaur",
      "name": "Bulbasaur",
      "level": 50,
      "hp": 45,
      "attack": 49,
      "defense": 49,
      "speed": 45,
      "types": ["grass", "poison"],
      "moveIds": ["tackle", "headbutt", "vinewhip", "razorleaf"],
      "spriteFrontUrl": "https://play.pokemonshowdown.com/sprites/ani/bulbasaur.gif",
      "spriteBackUrl": "https://play.pokemonshowdown.com/sprites/ani-back/bulbasaur.gif"
    }
  ]
}
```

Reglas de serializacion:

- Construir DTOs JSON desde `POKEDEX`; nunca duplicar datos en el frontend.
- Convertir `pokemon_type="grass/poison"` (cadena separada por `/`) a `types=["grass", "poison"]` (lista).
- Mantener `id` como identificador estable para seleccion y payloads.

### `GET /api/config`

Ruta nueva recomendada. **No implementada.** Opcional: evita que el frontend duplique la configuracion de dificultad.

```json
{
  "difficulties": [
    { "label": "Facil", "uiValue": "facil", "apiValue": "easy", "agent": "random" },
    { "label": "Medio", "uiValue": "medio", "apiValue": "medium", "agent": "heuristic" },
    { "label": "Dificil", "uiValue": "dificil", "apiValue": "hard", "agent": "minimax" },
    { "label": "Maestro-Sobrevilla", "uiValue": "maestro-sobrevilla", "apiValue": "sobrevilla", "agent": "minimax_optimized" }
  ],
  "teamSizes": [3, 4]
}
```

### `POST /api/battle/start`

Ruta existente. Requiere ampliarse para aceptar `playerPokemonIds` en modo `human-vs-ai`.

Payload para `Human vs IA`:

```json
{
  "mode": "human-vs-ai",
  "teamSize": 3,
  "difficulty": "hard",
  "playerPokemonIds": ["pikachu", "squirtle", "growlithe"]
}
```

Payload para `IA vs IA`:

```json
{
  "mode": "ai-vs-ai",
  "teamSize": 3,
  "difficulty": "sobrevilla"
}
```

Validaciones obligatorias:

- `mode` debe ser `human-vs-ai` o `ai-vs-ai`.
- `teamSize` debe ser `3` o `4`.
- `difficulty` debe pertenecer a `VALID_DIFFICULTIES`.
- En `human-vs-ai`, `playerPokemonIds` debe existir, tener longitud igual a `teamSize`, sin IDs repetidos y todos los IDs deben existir en `POKEDEX`.
- El equipo rival debe generarse desde `POKEDEX` excluyendo los IDs del jugador.

Respuesta esperada:

```json
{
  "sessionId": "...",
  "mode": "human-vs-ai",
  "over": false,
  "winner": null,
  "requiresHumanAction": true,
  "currentState": {},
  "frames": []
}
```

### `POST /api/battle/{sessionId}/action`

Ruta existente. Operativa.

```json
{ "actionType": "move", "index": 0 }
```

```json
{ "actionType": "switch", "index": 2 }
```

### `POST /api/battle/{sessionId}/step`

Ruta existente para avanzar batallas `IA vs IA`. Operativa.

```json
{}
```

---

## Cambios Requeridos En Backend

### B1 — Agregar CORS a todas las respuestas

El servidor no envia cabeceras CORS, lo que bloquea llamadas desde `http://localhost:5173` (Vite). Agregar en `_write_json` y `_serve_file`:

```python
self.send_header("Access-Control-Allow-Origin", "*")
self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
self.send_header("Access-Control-Allow-Headers", "Content-Type")
```

Ademas, agregar un handler para `OPTIONS` que devuelva `204 No Content` con las mismas cabeceras, para preflight requests del navegador.

### B2 — Agregar `GET /api/pokemon`

Implementar en `server.py` dentro de `do_GET`:

```python
if parsed.path == "/api/pokemon":
    self._write_json({"pokemon": serialize_pokedex()})
    return
```

La funcion `serialize_pokedex()` debe vivir en un modulo separado (por ejemplo `backend/ui/serializers.py`) y construir DTOs desde `POKEDEX`:

```python
def serialize_pokedex() -> list[dict]:
    from backend.data.pokemon import POKEDEX
    result = []
    for entry in POKEDEX.values():
        result.append({
            "id": entry.id,
            "name": entry.name,
            "level": entry.level,
            "hp": entry.hp,
            "attack": entry.attack,
            "defense": entry.defense,
            "speed": entry.speed,
            "types": entry.pokemon_type.split("/"),
            "moveIds": list(entry.move_ids),
            "spriteFrontUrl": entry.sprite_front_url,
            "spriteBackUrl": entry.sprite_back_url,
        })
    return result
```

### B3 — Ampliar `BattleSession` para equipo del jugador

Modificar `BattleSession.__init__` en `session.py` para aceptar `player_pokemon_ids`:

```python
def __init__(
    self,
    mode: str,
    team_size: int = 3,
    seed: int | None = None,
    difficulty: str = "medium",
    player_pokemon_ids: list[str] | None = None,
):
```

Logica de construccion de equipos segun modo:

```python
if mode == "human-vs-ai" and player_pokemon_ids:
    from backend.battle.factory import build_team_from_species, build_random_team
    from backend.data.pokemon import POKEDEX
    team1 = build_team_from_species("Jugador", player_pokemon_ids, self.rng)
    remaining_ids = [pid for pid in POKEDEX if pid not in player_pokemon_ids]
    team2 = build_random_team("IA 2", team_size, self.rng, species_pool=remaining_ids)
else:
    team1, team2 = build_balanced_teams(
        "Jugador" if mode == "human-vs-ai" else "IA 1", "IA 2", team_size, self.rng
    )
```

Tambien propagar `player_pokemon_ids` desde `SessionStore.create` y desde el handler de `POST /api/battle/start` en `server.py`.

### B4 — Eliminar referencia a `frontend/web`

Las constantes `FRONTEND_WEB_DIR` y `FRONTEND_ASSET_DIR` en `server.py:18-19` apuntan a un directorio eliminado. En modo API puro (desarrollo separado con Vite), el servidor no debe servir archivos estaticos. Opciones:

- Eliminar `do_GET` para rutas no-API o devolver `404` para cualquier ruta que no empiece por `/api/`.
- En produccion local, apuntar al build de `frontend/retro-poke-battle-main/dist/`.

---

## Cambios Requeridos En Frontend

### F1 — Crear `api.ts`

Crear `frontend/retro-poke-battle-main/src/lib/pokefisi/api.ts`:

```ts
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json", ...init?.headers },
    ...init,
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({ error: response.statusText }));
    throw new Error(error.error ?? "Error de comunicacion con el backend");
  }
  return response.json() as Promise<T>;
}

export const fetchPokemon = () =>
  requestJson<{ pokemon: ApiPokemon[] }>("/api/pokemon").then((r) => r.pokemon);

export const startBattle = (payload: StartBattlePayload) =>
  requestJson<BattleResponse>("/api/battle/start", {
    method: "POST",
    body: JSON.stringify(payload),
  });

export const sendHumanAction = (sessionId: string, action: HumanAction) =>
  requestJson<BattleResponse>(`/api/battle/${sessionId}/action`, {
    method: "POST",
    body: JSON.stringify(action),
  });

export const stepAiBattle = (sessionId: string) =>
  requestJson<BattleResponse>(`/api/battle/${sessionId}/step`, {
    method: "POST",
    body: "{}",
  });
```

Los tipos `ApiPokemon`, `StartBattlePayload`, `BattleResponse` y `HumanAction` deben definirse en `data.ts` o en un archivo `types.ts` separado.

### F2 — Reemplazar `POKEMON_POOL` por datos del API

En `data.ts`, eliminar `POKEMON_POOL`, `SEEDS` y las URLs hardcodeadas de PokeAPI. Conservar:

- Tipos TypeScript (`Pokemon`, `Move`, `Difficulty`, `PokeType`).
- `DIFFICULTY_TO_API` (nuevo).
- `DIFFICULTY_LABEL` y `DIFFICULTY_DESC` si no se usa `/api/config`.
- Funcion `mapApiPokemon(dto: ApiPokemon): Pokemon` que convierta el DTO del backend al modelo visual del frontend.

```ts
export function mapApiPokemon(dto: ApiPokemon): Pokemon {
  return {
    id: dto.id,
    name: dto.name,
    level: dto.level,
    types: dto.types as PokeType[],
    sprite: dto.spriteFrontUrl,
    spriteBack: dto.spriteBackUrl,
    icon: dto.spriteFrontUrl,
    hp: dto.hp,
    hpMax: dto.hp,
    moves: [],   // los movimientos reales los devuelve currentState en cada frame
    fainted: false,
  };
}
```

`SelectScreen` recibe la lista cargada desde `fetchPokemon()` en lugar de importar `POKEMON_POOL`.

### F3 — Corregir nombre de dificultad `"maestro"`

En `data.ts:236` cambiar:

```ts
// antes
export type Difficulty = "facil" | "medio" | "dificil" | "maestro";

// despues
export type Difficulty = "facil" | "medio" | "dificil" | "maestro-sobrevilla";
```

En `PokefisiApp.tsx:249` cambiar la opcion del dropdown:

```ts
// antes
{ value: "maestro", label: "Maestro Pokemon" }

// despues
{ value: "maestro-sobrevilla", label: "Maestro-Sobrevilla" }
```

Agregar `DIFFICULTY_TO_API` en `data.ts` (ver seccion Mapeo De Dificultades).

### F4 — Conectar seleccion Human vs IA al backend

Al confirmar equipo, reemplazar la logica local de `handleConfirmTeam` por una llamada a `startBattle`:

```ts
const response = await startBattle({
  mode: "human-vs-ai",
  teamSize,
  difficulty: DIFFICULTY_TO_API[difficulty],
  playerPokemonIds: selectedIds,
});
setSessionId(response.sessionId);
setFrameQueue(response.frames);
setCurrentState(response.currentState);
```

### F5 — Reemplazar motor local por reproduccion de frames

Eliminar de `PokefisiApp.tsx`:

- `calcDamage` (linea 46)
- `chooseAIMove` (linea 63)
- `effectivenessTag` (linea 74)
- `runTurn` (linea 607)
- `doAttack` (linea 535)

`BattleScreen` pasa a ser un reproductor de estado: recibe `currentState` del backend y reproduce animaciones segun `frame.animation.type`.

Mapeo de animaciones (el CSS ya existe y no cambia):

| `frame.animation.type` backend | Clase CSS frontend |
|---|---|
| `attack` (side: player) | `anim-attack-player` sobre sprite del jugador, luego `anim-shake` + `anim-flash` sobre enemigo |
| `attack` (side: enemy) | `anim-attack-enemy` sobre sprite del enemigo, luego `anim-shake` + `anim-flash` sobre jugador |
| `switch` | `anim-enter` sobre el entrante |
| `faint` | `anim-faint` sobre el que cae |
| `idle` | Sin animacion |

Cada accion humana llama `sendHumanAction` y encola los frames de respuesta. Para IA vs IA, un loop llama `stepAiBattle` y agrega los frames a la cola.

---

## Modelo Visual Del Estado Backend

`backend/ui/view_state.py` ya serializa datos compatibles con la UI:

```json
{
  "turn": 1,
  "message": "Elige una accion: atacar o cambiar de Pokemon.",
  "player": {
    "trainer": "Jugador",
    "active": {
      "name": "Pikachu",
      "level": 50,
      "currentHp": 110,
      "maxHp": 110,
      "spriteUrl": "...",
      "moves": [
        { "name": "Impactrueno", "type": "electric", "pp": 15, "maxPp": 15, "power": 40 }
      ]
    },
    "party": []
  },
  "enemy": {
    "trainer": "IA 2",
    "active": {},
    "party": []
  },
  "actionGroups": {
    "moves": [],
    "switches": [],
    "forcedSwitch": false
  },
  "panel": {
    "menu": "root",
    "locked": false
  }
}
```

Mapeo al modelo visual del frontend:

| Campo backend | Campo frontend |
|---|---|
| `currentHp` | `hp` |
| `maxHp` | `hpMax` |
| `spriteUrl` (jugador) | `spriteBack` |
| `spriteUrl` (enemigo) | `sprite` |
| `moves[].name` | Botones de `MoveButton` |
| `moves[].pp` / `moves[].maxPp` | PP mostrado |
| `actionGroups.moves` | Acciones de LUCHAR |
| `actionGroups.switches` | Acciones de POKEMON |

---

## Estructura De Archivos

Frontend:

```text
frontend/retro-poke-battle-main/src/lib/pokefisi/
  api.ts              # cliente HTTP (crear)
  data.ts             # tipos, DIFFICULTY_TO_API, mapApiPokemon; sin POKEMON_POOL
  PokefisiApp.tsx     # flujo visual conectado a API; sin motor local
  components.tsx      # componentes visuales (sin cambios)
```

Backend:

```text
backend/
  server.py           # rutas API + CORS + GET /api/pokemon
  session.py          # BattleSession con player_pokemon_ids
  ui/serializers.py   # serialize_pokedex() (crear)
  data/pokemon.py     # fuente canonica POKEDEX (sin cambios)
  battle/factory.py   # build_team_from_species (sin cambios)
```

---

## Flujo Completo Human Vs IA

1. El frontend carga `GET /api/pokemon` al abrir `SelectScreen`.
2. El usuario elige dificultad desde el dropdown existente.
3. El usuario presiona `Human vs IA`.
4. `SelectScreen` muestra solo los 30 Pokemon de `POKEDEX`.
5. El usuario elige 3 o 4 Pokemon.
6. El frontend llama `POST /api/battle/start` con `playerPokemonIds` y la dificultad convertida por `DIFFICULTY_TO_API`.
7. El backend valida IDs, crea equipo humano con `build_team_from_species` y equipo IA con el resto de `POKEDEX`.
8. El backend devuelve `sessionId`, `currentState` y `frames`.
9. El frontend almacena `sessionId`, muestra `currentState` y reproduce `frames` con las clases CSS existentes.
10. Cada accion humana llama `POST /api/battle/{sessionId}/action`.
11. El backend responde nuevos `frames` y el frontend actualiza la UI.
12. Cuando `over=true`, el frontend muestra `ResultScreen`.

## Flujo Completo IA Vs IA

1. El usuario elige dificultad y tamano de equipo.
2. El usuario presiona `IA vs IA`.
3. El frontend llama `POST /api/battle/start` sin `playerPokemonIds`.
4. El backend construye ambos equipos con `build_balanced_teams` desde `POKEDEX`.
5. El frontend almacena `sessionId` y muestra el estado inicial.
6. Cada avance automatico llama `POST /api/battle/{sessionId}/step` respetando pausa y velocidad del frontend.
7. El frontend reproduce frames usando `frame.animation.type` con las clases CSS existentes.

---

## Variables De Entorno

Crear `frontend/retro-poke-battle-main/.env.local`:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

Esto desacopla el puerto del backend del codigo fuente. Si se usa proxy de Vite en lugar de CORS, se puede dejar vacio:

```env
VITE_API_BASE_URL=
```

## CORS Y Proxy

Dos alternativas para que frontend (puerto 5173) y backend (puerto 8000) se comuniquen:

**Opcion A — CORS en backend (recomendado para simplicidad):**

Agregar en `_write_json` y en un handler `do_OPTIONS`:

```python
self.send_header("Access-Control-Allow-Origin", "*")
self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
self.send_header("Access-Control-Allow-Headers", "Content-Type")
```

**Opcion B — Proxy en Vite:**

En `vite.config.ts` o `app.config.ts` de TanStack Start:

```ts
server: {
  proxy: {
    "/api": "http://127.0.0.1:8000"
  }
}
```

Con proxy, `API_BASE_URL` debe ser `""` (cadena vacia) y todas las llamadas van a rutas relativas.

---

## Criterios De Aceptacion

La integracion se considera correcta si cumple todo lo siguiente:

- El frontend no importa ni usa `POKEMON_POOL` ni datos locales de Pokemon.
- `SelectScreen` muestra solo los 30 Pokemon definidos en `backend/data/pokemon.py`.
- Al elegir `Human vs IA`, los IDs seleccionados se envian en `playerPokemonIds`.
- El backend valida esos IDs contra `POKEDEX` y rechaza IDs inexistentes.
- La dificultad `Facil` activa `RandomAgent`.
- La dificultad `Medio` activa `HeuristicAgent`.
- La dificultad `Dificil` activa `MinimaxAgent` con pesos manuales.
- La dificultad `Maestro-Sobrevilla` activa `MinimaxAgent` con pesos optimizados o fallback manual.
- El dropdown visual se mantiene identico al actual.
- Las clases CSS de animacion (`anim-shake`, `anim-flash`, `anim-attack-player`, `anim-attack-enemy`, `anim-faint`, `anim-enter`, `anim-float`) siguen usandose.
- El calculo de dano y la decision de IA no ocurren en el frontend.
- El resultado de batalla proviene del backend.

---

## Pruebas Recomendadas

### Backend

Iniciar servidor:

```bash
python -m backend.main --mode serve
```

Verificar salud:

```bash
curl http://127.0.0.1:8000/api/health
```

Verificar Pokemon (requiere implementar B2):

```bash
curl http://127.0.0.1:8000/api/pokemon
```

Iniciar batalla Human vs IA (requiere implementar B3):

```bash
curl -X POST http://127.0.0.1:8000/api/battle/start \
  -H "Content-Type: application/json" \
  -d '{"mode":"human-vs-ai","teamSize":3,"difficulty":"hard","playerPokemonIds":["pikachu","squirtle","growlithe"]}'
```

### Frontend

```bash
cd frontend/retro-poke-battle-main
npm run dev
```

Validaciones manuales:

- Abrir el menu y confirmar que el dropdown contiene `Facil`, `Medio`, `Dificil`, `Maestro-Sobrevilla`.
- Entrar a `Human vs IA` y confirmar que aparecen exactamente los 30 Pokemon de `POKEDEX`.
- Seleccionar equipo, iniciar combate y confirmar que los mismos Pokemon aparecen en batalla.
- Ejecutar una accion de ataque y verificar que el backend devuelve nuevos frames.
- Confirmar que las animaciones de ataque, golpe, cambio y debilitamiento funcionan.

---

## Riesgos Y Mitigaciones

| Riesgo | Mitigacion |
|---|---|
| Duplicar datos entre `data.ts` y `pokemon.py` | Eliminar `POKEMON_POOL`; usar `GET /api/pokemon` como unica fuente |
| Romper animaciones al conectar API | Mantener CSS actual; mapear `frame.animation.type` a clases existentes |
| Enviar dificultad en formato incorrecto al backend | Usar `DIFFICULTY_TO_API` centralizado en `data.ts` |
| Seleccionar Pokemon inexistentes (evoluciones locales) | Al eliminar `POKEMON_POOL`, el selector solo mostrara los 30 de `POKEDEX` |
| Llamadas CORS bloqueadas en desarrollo | Configurar CORS en backend o proxy en Vite |
| Usar rutas de frontend eliminado | No usar `frontend/web`; apuntar a Vite en dev o `dist/` en produccion |
| Acoplar frontend al puerto 8000 | Usar `VITE_API_BASE_URL` o proxy |

---

## Resumen De Implementacion

La integracion no esta implementada. El frontend opera como simulador independiente. La conexion consiste en:

**Backend (4 cambios):**

1. Agregar CORS a todas las respuestas (`server.py`) — desbloquea llamadas desde Vite.
2. Agregar `GET /api/pokemon` (`server.py` + `ui/serializers.py`) — expone `POKEDEX` al frontend.
3. Ampliar `BattleSession.__init__` con `player_pokemon_ids` (`session.py`) — permite equipos seleccionados por el jugador.
4. Propagar `player_pokemon_ids` en `SessionStore.create` y en el handler de `/api/battle/start` (`server.py`).

**Frontend (5 cambios, solo logica de conexion, sin tocar visual):**

1. Crear `api.ts` con `fetchPokemon`, `startBattle`, `sendHumanAction`, `stepAiBattle`.
2. Reemplazar `POKEMON_POOL` por datos de `GET /api/pokemon`; agregar `mapApiPokemon` en `data.ts`.
3. Renombrar `"maestro"` a `"maestro-sobrevilla"` y agregar `DIFFICULTY_TO_API` en `data.ts`.
4. Reemplazar logica local (`calcDamage`, `chooseAIMove`, `runTurn`, `doAttack`) por consumo de `frames` del backend.
5. Almacenar `sessionId` y llamar al backend en cada accion del jugador y en cada paso de IA vs IA.

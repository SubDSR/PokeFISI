# PokeFISI: Simulador Académico de Combates y Optimización Evolutiva de IA

PokeFISI es un simulador académico de combates por turnos basado en las mecánicas fundamentales de Pokémon (tipos elementales, estadísticas, daño y selección de equipos). Este proyecto ha sido desarrollado en el marco de la **Universidad Nacional Mayor de San Marcos (UNMSM) - Facultad de Ingeniería de Sistemas e Informática (FISI)**, con el objetivo de investigar la aplicación de algoritmos de teoría de juegos (Minimax con Poda Alfa-Beta) y algoritmos evolutivos (Algoritmo Genético) para la optimización de agentes de inteligencia artificial en entornos de decisión estocásticos y adversariales.

---

## 📌 Índice

1. [Descripción General](#-descripción-general)
2. [Arquitectura del Proyecto](#-arquitectura-del-proyecto)
3. [Mecánicas del Simulador](#-mecánicas-del-simulador)
   - [Balance de Equipos (Reglas 1 a 5)](#balance-de-equipos-reglas-1-a-5)
   - [Fórmula de Daño Calibrada](#fórmula-de-daño-calibrada)
   - [Alcance y Simplificaciones](#alcance-y-simplificaciones)
4. [Niveles de Dificultad e IA](#-niveles-de-dificultad-e-ia)
5. [Agente Minimax y Optimizaciones](#-agente-minimax-y-optimizaciones)
   - [Poda Alfa-Beta](#poda-alfa-beta)
   - [Ordenamiento Heurístico (Move Ordering)](#ordenamiento-heurístico-move-ordering)
   - [Tabla de Transposición](#tabla-de-transposición)
   - [Control de Ramificación (Top-K)](#control-de-ramificación-top-k)
6. [Optimización con Algoritmo Genético](#-optimización-con-algoritmo-genético)
   - [Función Heurística Compuesta](#función-heurística-compuesta)
   - [Función de Fitness](#función-de-fitness)
   - [Operadores Evolutivos](#operadores-evolutivos)
7. [Guía de Instalación y Ejecución](#-guía-de-instalación-y-ejecución)
   - [Requisitos](#requisitos)
   - [Backend (Python 3.10+)](#backend-python-310)
   - [Frontend (React + TypeScript + Vite)](#frontend-react--typescript--vite)
8. [Scripts de Automatización y Experimentos](#-scripts-de-automatización-y-experimentos)
9. [Referencia de la API HTTP](#-referencia-de-la-api-http)
10. [Justificación Académica](#-justificación-académica)

---

## 📖 Descripción General

PokeFISI proporciona un entorno interactivo y experimental completo:
- **Backend (Python 3.10+)**: Implementa el motor de simulación de batallas (libre de efectos secundarios para permitir búsquedas prospectivas en el árbol de juego), los agentes de toma de decisión (Heurísticos, Minimax) y el marco de entrenamiento evolutivo (Algoritmo Genético). Todo desarrollado utilizando exclusivamente la **biblioteca estándar de Python** (sin dependencias de terceros), garantizando portabilidad y ligereza.
- **Frontend (React 19 + TypeScript + Vite + Tailwind CSS)**: Ofrece una interfaz gráfica moderna, con animaciones dinámicas de transición de batallas, selector de dificultad multinivel, consola de registros de acciones en tiempo real e indicador visual del estado de los equipos.

---

## 🏗️ Arquitectura del Proyecto

El proyecto está organizado de la siguiente manera:

```text
PokeFISI/
├── backend/                       # Código fuente del servidor y agentes de IA
│   ├── agents/                    # Definición de agentes (Base, Random, Heuristic, Minimax, Human)
│   │   ├── heuristics.py          # Las 5 funciones heurísticas normalizadas
│   │   ├── minimax_agent.py       # Agente adversarial con Poda Alfa-Beta y optimizaciones
│   │   └── heuristic_agent.py     # Agente con evaluación codiciosa (greedy) de profundidad 1
│   ├── battle/                    # Lógica del juego y motor de batalla
│   │   ├── damage.py              # Fórmula de daño con efectividad elemental y calibración de velocidad
│   │   ├── engine.py              # Ejecutor de turnos de la batalla
│   │   ├── factory.py             # Generador de equipos balanceados (Reglas 1-5)
│   │   ├── simulator.py           # Simulador sin efectos secundarios para el lookahead de Minimax
│   │   └── state.py               # Representación inmutable del estado del combate
│   ├── data/                      # Datos estáticos (Pokédex, Movedex, Tabla de Efectividad)
│   ├── experiments/               # Algoritmo Genético y experimentación por lotes
│   │   ├── evolution.py           # Loop evolutivo offline de optimización de pesos
│   │   └── fitness.py             # Evaluador de fitness (win rate + margen de supervivencia)
│   ├── ui/                        # Visualizadores para terminal (Consola y exportador de Replay)
│   ├── config.py                  # Gestión centralizada de dificultades, pesos y profundidades
│   ├── main.py                    # CLI / Punto de entrada multipropósito
│   └── server.py                  # Servidor HTTP API (BaseHTTPRequestHandler de Python)
├── frontend/                      # Cliente web interactivo (React 19 + TS)
│   ├── src/
│   │   ├── lib/pokefisi/          # Componentes y lógica del cliente (PokefisiApp, api.ts, etc.)
│   │   ├── main.tsx               # Entrada de React
│   │   └── styles.css             # Estilos y animaciones (Tailwind v4)
│   ├── package.json               # Configuración del frontend y scripts npm
│   └── vite.config.ts             # Configuración del bundler Vite
├── docs/                          # Documentación científica del proyecto
│   ├── algorithms_justification.md  # Justificación teórica de Minimax y Algoritmo Genético
│   ├── complexity_analysis.md       # Análisis de complejidad temporal del árbol de búsqueda
│   ├── difficulty_system.md         # Diseño del sistema de dificultad progresiva
│   └── conexion_backend_frontend.md # Protocolo de comunicación HTTP entre capas
├── scripts/                       # Scripts auxiliares para experimentos y automatización
├── results/                       # Directorio de salida para métricas, gráficos y best_weights.json
├── requirements.txt               # Dependencias del backend (solo pytest para desarrollo)
└── setup.py                       # Configuración de distribución del paquete de python
```

---

## ⚔️ Mecánicas del Simulador

### Balance de Equipos (Reglas 1 a 5)
Para asegurar batallas justas y estratégicas, el generador de equipos (`backend/battle/factory.py`) impone restricciones estrictas de diseño:
1. **Regla 1 (Tier de Potencia)**: Clasificación de Pokémon en Tiers basados en su BST (*Base Stat Total*). Un equipo de 3 debe incluir 1 Pokémon de Tier A (Fuerte), 1 de Tier B (Medio) y 1 de Tier C (Débil).
2. **Regla 2 (Tipos Primarios Únicos)**: No pueden existir dos Pokémon en el mismo equipo con el mismo tipo primario.
3. **Regla 3 (Sin Debilidad Compartida)**: El equipo no puede tener más de un Pokémon que reciba daño súper efectivo ($\ge 2\times$) por el mismo tipo de ataque elemental.
4. **Regla 4 (STAB Garantizado)**: Cada Pokémon generado tiene garantizado al menos un movimiento ofensivo que coincide con su tipo (*Same Type Attack Bonus*).
5. **Regla 5 (Exclusión Mutua)**: Al generar los equipos para una batalla, un Pokémon no puede aparecer simultáneamente en ambos equipos.
6. **Balance Cruzado**: Si la diferencia de ventajas de tipo entre los equipos calculados supera un umbral de 2, el generador automáticamente reconstruye el equipo menos favorecido.

### Alcance y Simplificaciones

El simulador implementa un subconjunto deliberadamente acotado de la mecánica oficial de Pokémon Gen 3:

**Contenido incluido:**
- **30 Pokémon** de la primera generación, distribuidos en 3 tiers de potencia.
- **50 movimientos** con valores de `base_power` y `accuracy` verificados contra el dataset oficial de Pokémon Showdown Gen 3.
- **13 tipos elementales**: Normal, Fuego, Agua, Eléctrico, Planta, Lucha, Veneno, Tierra, Volador, Psíquico, Bicho, Roca y Acero.

**Simplificaciones respecto a Gen 3 oficial** (fuera del alcance del proyecto):
- No hay **efectos de estado** (quemado, paralizado, dormido, congelado, envenenado).
- No hay **habilidades** (*abilities*) pasivas de Pokémon.
- No hay **objetos equipados** (*held items*) ni **clima** (lluvia, sol, granizo, tormenta de arena).
- Los movimientos de **múltiples turnos** se resuelven en un único turno por simplicidad (e.g., Solar Beam).
- No hay **golpes críticos** ni variación aleatoria de daño — el daño es completamente determinista.

Estas simplificaciones garantizan un entorno de información perfecta y determinismo total, lo que justifica directamente el uso de Minimax clásico.

---

### Fórmula de Daño Calibrada
El motor utiliza una versión ajustada de la fórmula tradicional para evitar batallas con debilitamientos instantáneos (OHKOs) y dar mayor peso a la táctica:

$$\text{Damage} = \max\left(1, \text{Int}\left(\text{Round}\left(\frac{\frac{\text{Attack}}{\max(1, \text{Defense\_op})} \times \text{BasePower} \times \text{TypeModifier} - \text{Speed\_op} \times K}{\text{DAMAGE\_SCALE}}\right)\right)\right)$$

*Donde:*
- **$K = 0.1$**: Factor de evasión por velocidad del defensor. Evita que la velocidad domine por completo la mitigación de daño.
- **$\text{DAMAGE\_SCALE} = 2$**: Divisor de calibración que duplica la duración promedio del combate, permitiendo la ejecución de estrategias de cambio (*switches*).
- **$\text{TypeModifier}$**: Multiplicador resultante del producto de efectividades frente a la tabla de tipos elementales.

---

## 🎮 Niveles de Dificultad e IA

El simulador ofrece 4 niveles de dificultad bien definidos en `backend/config.py`:

| Nivel | Nombre | Clave API | Agente Subyacente | Profundidad ($d$) | Win Rate Esperado (Humano) | Propósito |
| :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **1** | Entrenamiento | `easy` | `RandomAgent` | - | 85% - 95% | Aprendizaje inicial y pruebas de flujo. |
| **2** | Competitivo | `medium` | `HeuristicAgent` | 1 | 60% - 70% | Oponente codicioso (*greedy*) de corto plazo. |
| **3** | Experto | `hard` | `MinimaxAgent` | 4 | 35% - 45% | Búsqueda táctica profunda con pesos calibrados manualmente. |
| **4** | Maestro | `sobrevilla` | `MinimaxAgent + GA` | 4 | 10% - 25% | Máximo desafío. Usa los pesos optimizados por el Algoritmo Genético. |

---

## 🧠 Agente Minimax y Optimizaciones

El `MinimaxAgent` modela el combate como un juego de **dos jugadores simultáneos por turno** de información perfecta. A diferencia del Minimax alternante clásico donde cada nivel del árbol representa un solo jugador, en PokeFISI **cada unidad de profundidad $d$ engloba ya un turno completo**: el agente itera sobre sus propias acciones y, para cada una, minimiza sobre todas las respuestas posibles del oponente antes de descender al siguiente turno. Esto produce una complejidad sin poda de $O((b \cdot b)^d) = O(b^{2d})$ donde $b \approx 6$ es el factor de ramificación por jugador y $d$ la profundidad en **turnos completos**.

```
          [ Estado de Batalla Actual ]
                       │
   (Fase 1: acciones críticas + top-K ranking propio)
                       │
       ┌───────────────┼───────────────┐
   [Acción 1]      [Acción 2]      [Acción 3]    ← acciones propias (MAX)
       │                │                │
  ┌────┴────┐      ┌────┴────┐      ┌────┴────┐
[Riv1][Riv2]    [Riv1][Riv2]    [Riv1][Riv2]    ← respuestas del rival (MIN)
       │
[Simular turno completo → nuevo estado]
       │
[Repetir recursivamente hasta profundidad d]
       │
[Evaluar h(s, i) en hojas]  ──►  Poda Alfa-Beta corta ramas
```

### Poda Alfa-Beta
Elimina subárboles cuyo resultado garantizado es inferior (para MAX) o superior (para MIN) a soluciones ya encontradas. Con buen ordenamiento de acciones, el costo se reduce al caso óptimo de $O(b^d)$, equivalente a $O((b^2)^{d/2})$ dado que cada unidad de profundidad cubre un par de movimientos (el nodo MAX y su MIN interno ya están agrupados).

### Ordenamiento Heurístico (Move Ordering)
La selección de acciones a explorar se realiza en **dos fases secuenciales**:

**Fase 1 — Acciones críticas (siempre incluidas, nunca eliminadas por top-K)**:
- Movimientos que producen un KO inmediato del Pokémon rival activo.
- El ataque de mayor daño esperado cuando el Pokémon propio puede ser KOado en el siguiente turno (*tempo attack*).
- Switches defensivos que reducen el daño esperado recibido o que garantizan que el entrante sobreviva el siguiente golpe.

**Fase 2 — Ranking del resto de acciones**:
Las acciones no críticas se puntúan con `_quick_score()` sin simular el turno completo. Para movimientos: daño esperado normalizado por HP del defensor. Para switches: combinación de ventaja de tipo del entrante (×0.25), reducción de vulnerabilidad del activo actual (×0.30), supervivencia esperada del entrante (×0.25) y HP ratio (×0.20), con penalizaciones por tempo perdido y "mal switch". Las acciones se ordenan de mayor a menor score para MAX y de menor a mayor para MIN, maximizando los cortes alfa-beta tempranos.

### Tabla de Transposición
Memoiza evaluaciones de estados visitados durante la búsqueda. Lo que evita no son ciclos — los cuales son imposibles en este modelo porque HP y PP solo decrementan — sino la **convergencia de trayectorias**: distintas secuencias de acciones en el árbol de búsqueda pueden alcanzar el mismo estado de batalla, y la tabla evita recomputarlo. El hash del estado incluye: número de turno, índice activo por equipo, HP y PP de cada Pokémon, y las últimas acciones ejecutadas (tipo + índice).

### Control de Ramificación (Top-K)
Tras extraer las acciones críticas de la Fase 1, la exploración se completa con las $K = 6$ acciones mejor valoradas por `_quick_score()` de la Fase 2. El número efectivo de acciones exploradas puede **superar $K$** cuando existen acciones críticas (KOs, switches urgentes) que se fuerzan al frente independientemente del ranking. Esta distinción evita que el recorte elimine movimientos letales que podrían quedar al final del ranking heurístico. Con $K=6$ y $d=4$, el tiempo de respuesta se sitúa consistentemente por debajo de los 0.5 segundos por turno.

---

## 🧬 Optimización con Algoritmo Genético

### Función Heurística Compuesta
La evaluación de las hojas del árbol se basa en una combinación lineal ponderada de 5 factores normalizados en el rango $[-1, 1]$ o $[-1, 0]$:

$$h(s, i) = W_1 \cdot f_{\text{pokemon vivos}}(s, i) + W_2 \cdot f_{\text{ventaja tipo}}(s, i) + W_3 \cdot f_{\text{velocidad}}(s, i) + W_4 \cdot f_{\text{hp restante}}(s, i) + W_5 \cdot f_{\text{riesgo morir}}(s, i)$$

*Donde:*
- $f_{\text{pokemon vivos}}$: Ventaja numérica de Pokémon saludables.
- $f_{\text{ventaja tipo}}$: Matchup elemental del Pokémon activo frente al rival.
- $f_{\text{velocidad}}$: Diferencia relativa de velocidad entre los Pokémon activos, calculada como $\tanh\!\left(\frac{\text{speed}_{\text{propio}} - \text{speed}_{\text{rival}}}{100}\right)$. No es una señal binaria de "quien ataca primero" (eso sería discontinuo), sino un proxy continuo de dominancia de velocidad comparativa. La velocidad ya actúa como factor de mitigación defensiva en la fórmula de daño; este factor captura su dimensión táctica residual.
- $f_{\text{hp restante}}$: Proporción de vida acumulada del equipo.
- $f_{\text{riesgo morir}}$: Penalización prospectiva si el Pokémon activo morirá en el siguiente turno.

### Función de Fitness
El algoritmo evalúa a cada individuo (un vector de pesos $W \in \mathbb{R}^5$) haciéndolo combatir $N$ veces contra el `HeuristicAgent` como oponente de referencia. El `HeuristicAgent` no simula turnos futuros: evalúa cada movimiento por su daño esperado y cada switch por una combinación de ventaja de tipo del entrante, reducción de vulnerabilidad del activo actual y HP ratio del entrante — lo que le permite cambiar voluntariamente ante desventajas de tipo reales sin ningún lookahead.

$$\text{Fitness}(W) = (\text{WinRate} \times 0.7) + (\text{MarginScore} \times 0.3)$$

- **$\text{WinRate}$**: Porcentaje de victorias obtenidas ($[0, 100]$).
- **$\text{MarginScore}$**: Promedio normalizado de la diferencia de Pokémon supervivientes al finalizar el encuentro ($[-100, 100]$).

### Operadores Evolutivos
- **Inicialización**: La población combina diversidad y calidad inicial. El primer individuo es el vector `MANUAL_WEIGHTS` (semilla experta); los 3 siguientes son variaciones gaussianas cercanas ($\sigma=0.05$) del mismo vector; el resto son vectores uniformes aleatorios en $[0,1]^5$. Esta estrategia de *seeding* reduce la exploración ciega inicial y acelera la convergencia sin sacrificar diversidad.
- **Selección**: Torneo determinista de tamaño $k=4$.
- **Crossover**: Cruce de un punto y uniforme (tasa del 80%) para mantener la diversidad genética.
- **Mutación**: Mutación Gaussiana ($\sigma=0.1$, tasa del 20%) con clamp a $[0,1]$ para realizar búsquedas refinadas locales.
- **Elitismo**: Preservación directa del $15\%$ de los mejores candidatos de la generación anterior.

---

## 🚀 Guía de Instalación y Ejecución

### Requisitos
- **Python**: Versión 3.10 o superior.
- **Node.js**: Versión 18 o superior y administrador de paquetes `npm`.
- **Conexión a internet**: Los sprites de los Pokémon se sirven desde `play.pokemonshowdown.com`. Sin conexión los sprites no cargarán, pero el simulador funciona con normalidad.

### Backend (Python 3.10+)

1. **Crear y activar entorno virtual (opcional pero recomendado)**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # En Linux/macOS
   # o
   .venv\Scripts\activate     # En Windows
   ```

2. **Instalar dependencias de desarrollo**:
   ```bash
   pip install -r requirements.txt
   # Opcional: instalar en modo editable
   pip install -e .
   ```

3. **Ejecutar el servidor API**:
   ```bash
   python -m backend.main --mode serve --port 8000
   ```
   Para exponer el servidor en la red local (accesible desde otros dispositivos):
   ```bash
   python -m backend.main --mode serve --host 0.0.0.0 --port 8000
   ```

4. **Ejecutar una batalla simulada en consola (IA vs IA)**:
   ```bash
   python -m backend.main --mode battle --agent1 minimax --agent2 heuristic
   ```
   *Agentes disponibles*: `random`, `heuristic`, `human`, `minimax`, `minimax-optimized` (usa pesos del AG si existen).

   Usar `--seed INT` para obtener batallas reproducibles:
   ```bash
   python -m backend.main --mode battle --agent1 minimax --agent2 heuristic --seed 42
   ```

5. **Exportar replay visual de una batalla**:
   ```bash
   python -m backend.main --mode battle --ui replay --agent1 minimax --agent2 heuristic
   ```
   Genera un archivo `frontend/web/replay_data.js` que puede ser abierto en el navegador para revisar la batalla turno a turno.

6. **Ejecutar un lote de batallas comparativo (experimento)**:
   ```bash
   python -m backend.main --mode experiment --agent1 minimax --agent2 heuristic --battles 20
   ```
   Imprime un resumen con win rate, promedio de turnos y resultado de cada agente.

### Frontend (React + TypeScript + Vite)

1. **Navegar a la carpeta frontend e instalar dependencias**:
   ```bash
   cd frontend
   npm install
   ```

2. **Iniciar el servidor de desarrollo**:
   ```bash
   npm run dev
   ```
   *Nota: Por defecto estará disponible en [http://localhost:5173](http://localhost:5173).*

---

## 📊 Scripts de Automatización y Experimentos

En la carpeta `scripts/` se ubican utilidades clave para probar, entrenar y comparar la IA:

- **Entrenamiento Offline del Algoritmo Genético**:
  ```bash
  python scripts/run_evolution.py --generations 50 --battles 30 --depth 4
  ```
  Genera tres archivos en `results/`:
  - `best_weights.json` — pesos óptimos, leídos automáticamente por el servidor en la dificultad **Maestro (`sobrevilla`)**.
  - `evolution_history.csv` — progresión de fitness y diversidad por generación.
  - `evolution_summary.txt` — resumen legible del entrenamiento completo.

- **Evaluación Comparativa de Dificultad**:
  ```bash
  python scripts/test_difficulty_levels.py --battles 20
  ```
  Valida que la tasa de victorias de los agentes sea progresiva de acuerdo con su nivel estratégico.

- **Exportación de Métricas de Rendimiento**:
  ```bash
  python scripts/export_metrics.py --depths 1 2 3 --battles 20
  ```
  Genera archivos `.csv` en `results/` comparando tiempos de respuesta, cantidad de nodos visitados y tasa de acierto de cortes.

- **Experimento en Consola Minimax vs Heuristic**:
  ```bash
  python scripts/run_minimax_experiment.py --battles 30 --depth 2
  ```

- **Ejecución de Tests Unitarios**:
  ```bash
  pytest
  ```

---

## 🔌 Referencia de la API HTTP

El servidor expone una API REST JSON en `http://127.0.0.1:8000` (por defecto). Todos los endpoints responden con `Content-Type: application/json`.

### Endpoints

#### `GET /api/health`
Comprueba que el servidor está activo.
```json
{ "status": "ok" }
```

#### `GET /api/pokemon`
Devuelve el Pokédex completo: estadísticas base, tipos, movimientos disponibles y URLs de sprites.

#### `GET /api/config`
Devuelve las dificultades disponibles y los tamaños de equipo soportados.
```json
{ "difficulties": [...], "teamSizes": [3, 4] }
```

#### `POST /api/battle/start`
Inicia una nueva sesión de batalla. Devuelve el estado inicial del combate y un `sessionId`.

```json
{
  "mode": "human-vs-ai",
  "difficulty": "hard",
  "teamSize": 3,
  "seed": 42,
  "playerPokemonIds": ["bulbasaur", "charmander", "squirtle"]
}
```

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `mode` | `string` | `"human-vs-ai"` o `"ai-vs-ai"`. En `ai-vs-ai` ambos equipos son generados automáticamente. |
| `difficulty` | `string` | `"easy"` \| `"medium"` \| `"hard"` \| `"sobrevilla"` |
| `teamSize` | `int` | `3` o `4` |
| `seed` | `int` | Opcional. Fija la semilla para resultados reproducibles. |
| `playerPokemonIds` | `string[]` | Solo en `human-vs-ai`. Lista de IDs del Pokédex para el equipo del jugador. |

#### `POST /api/battle/{sessionId}/step`
Avanza el turno de la IA. Se usa en `ai-vs-ai` o para ejecutar la respuesta del oponente después de una acción humana. No requiere body.

#### `POST /api/battle/{sessionId}/action`
Envía la acción del jugador humano (solo en `human-vs-ai`).

```json
{
  "actionType": "move",
  "index": 0
}
```

| Campo | Valores |
|-------|---------|
| `actionType` | `"move"` para usar un movimiento, `"switch"` para cambiar de Pokémon |
| `index` | Índice del movimiento (0–3) o del Pokémon al que cambiar (0–2) |

---

## 🎓 Justificación Académica

- **Idoneidad de Minimax**: Los combates en PokeFISI se comportan como juegos matriciales por turnos, deterministas en su núcleo de cálculo físico e información perfecta. El resultado es de **suma constante** en victorias/derrotas (lo que uno gana el otro lo pierde), pero no estrictamente de suma cero: los empates — cuando ambos equipos se eliminan simultáneamente — devuelven valor 0 para ambos jugadores. Esta estructura encaja de manera natural en la formulación teórica de Minimax con poda Alfa-Beta (Von Neumann, 1928).
- **Ordenamiento Heurístico e Inspiración de A\***: El ordenamiento previo de movimientos toma el concepto de pre-evaluación del coste de transición de A\* para reordenar las ramas. Esto maximiza los cortes alfa-beta en etapas tempranas. En el modelo de este proyecto, donde cada unidad de profundidad $d$ representa un turno completo (equivalente a 2 plies alternantes), la complejidad promedio con ordenamiento pasa de $O(b^{2d})$ a un valor aproximado de $O(b^{3d/2})$ — a diferencia del resultado clásico $O(b^{3d/4})$ que se aplica a Minimax de un solo ply por nivel.
- **Búsqueda de Gradiente Inexistente mediante GA**: La optimización del vector de pesos heurísticos carece de una función continua diferenciable debido a factores estocásticos y saltos discretos (como debilitamiento de Pokémon). Esto inhabilita el uso de algoritmos basados en gradiente (Gradient Descent), justificando el uso de Algoritmos Genéticos como aproximadores globales estocásticos robustos de caja negra.

# PokeFISI: Simulador Académico de Combates y Optimización Evolutiva de IA

PokeFISI es un simulador académico de combates por turnos basado en las mecánicas fundamentales de Pokémon (tipos elementales, estadísticas, daño y selección de equipos). Este proyecto ha sido desarrollado en el marco de la **Universidad Nacional Mayor de San Marcos (UNMSM) - Facultad de Ingeniería de Sistemas e Informática (FISI)**, con el objetivo de investigar la aplicación de algoritmos de teoría de juegos (Minimax con Poda Alfa-Beta) y algoritmos evolutivos (Algoritmo Genético) para la optimización de agentes de inteligencia artificial en entornos de decisión estocásticos y adversariales.

---

## 📌 Índice

1. [Descripción General](#-descripción-general)
2. [Arquitectura del Proyecto](#-arquitectura-del-proyecto)
3. [Mecánicas del Simulador](#-mecánicas-del-simulador)
   - [Balance de Equipos (Reglas 1 a 5)](#balance-de-equipos-reglas-1-a-5)
   - [Escalado de HP (Fórmula Gen 3)](#escalado-de-hp-fórmula-gen-3)
   - [Fórmula de Daño Calibrada](#fórmula-de-daño-calibrada)
   - [Tabla de Efectividad de Tipos](#tabla-de-efectividad-de-tipos)
   - [Flujo de Resolución de un Turno](#flujo-de-resolución-de-un-turno)
   - [Sistema de PP y Struggle](#sistema-de-pp-y-struggle)
   - [Alcance y Simplificaciones](#alcance-y-simplificaciones)
4. [Niveles de Dificultad e IA](#-niveles-de-dificultad-e-ia)
5. [Agente Minimax y Optimizaciones](#-agente-minimax-y-optimizaciones)
   - [Poda Alfa-Beta](#poda-alfa-beta)
   - [Ordenamiento Heurístico (Move Ordering)](#ordenamiento-heurístico-move-ordering)
   - [Tabla de Transposición](#tabla-de-transposición)
   - [Control de Ramificación (Top-K)](#control-de-ramificación-top-k)
   - [Modo Determinista del Simulador](#modo-determinista-del-simulador)
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
1. **Regla 1 (Tier de Potencia)**: Los 30 Pokémon se clasifican por BST (*Base Stat Total* = HP + Atk + Def + Speed) en 3 tiers:
   - **Tier A** (BST ≥ 225): Mankey, Growlithe, Machop, Slowpoke, Doduo, Geodude, Pidgeotto, Sandshrew, Ponyta.
   - **Tier B** (195 ≤ BST < 225): Charmander, Squirtle, Bellsprout, Spearow, Psyduck, Meowth, Seel, Venonat, Pikachu, Poliwag.
   - **Tier C** (BST < 195): Abra, Magnemite, Oddish, Vulpix, Paras, Tentacool, Bulbasaur, Nidoran M/F, Rattata, Ekans.
   - Equipo de **3**: 1A + 1B + 1C. Equipo de **4**: 1A + 2B + 1C.
   - La diferencia máxima de BST entre cualquier par de equipos generados es ≈ 60 puntos.
   - Si los constraints de Reglas 2 y 3 son imposibles de satisfacer, el generador degrada progresivamente: primero intenta solo con Reglas 1+2, y como último recurso solo Regla 1.
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
- Solo existen **4 estadísticas** por Pokémon: HP, Ataque, Defensa y Velocidad. Gen 3 oficial tiene 6 (añade Ataque Especial y Defensa Especial). En PokeFISI todos los movimientos, sean físicos o especiales, usan las mismas stats de Ataque y Defensa.

Estas simplificaciones garantizan un entorno de información perfecta y determinismo total, lo que justifica directamente el uso de Minimax clásico.

---

### Escalado de HP (Fórmula Gen 3)

Todos los Pokémon calculan su HP de combate aplicando la fórmula oficial de Gen 3 con parámetros fijos:

$$\text{HP\_final} = \left\lfloor \frac{(2 \times \text{BaseHP} + \text{IV} + \lfloor \text{EV}/4 \rfloor) \times \text{Level}}{100} \right\rfloor + \text{Level} + 10$$

*Parámetros fijos en PokeFISI*: $\text{IV} = 31$ (máximo), $\text{EV} = 0$, $\text{Level} = 50$.

Con estos valores la fórmula se simplifica a:

$$\text{HP\_final} = \left\lfloor \frac{(2 \times \text{BaseHP} + 31) \times 50}{100} \right\rfloor + 60$$

Esto produce HP de combate entre **~2 y 3× mayores** que las stats base del Pokédex. Ejemplos representativos:

| Pokémon | BaseHP | HP\_final |
|---------|--------|-----------|
| Rattata | 30 | 100 |
| Bulbasaur | 45 | 120 |
| Machop | 70 | 155 |
| Slowpoke | 90 | 185 |

Este escalado es la razón por la que `DAMAGE_SCALE = 2` en la fórmula de daño produce batallas de duración táctica: sin él, los ataques eliminarían a un Pokémon en 1-2 golpes.

---

### Fórmula de Daño Calibrada
El motor utiliza una versión ajustada de la fórmula tradicional para evitar batallas con debilitamientos instantáneos (OHKOs) y dar mayor peso a la táctica:

$$\text{Damage} = \max\left(1, \text{Int}\left(\text{Round}\left(\frac{\frac{\text{Attack}}{\max(1, \text{Defense\_op})} \times \text{BasePower} \times \text{TypeModifier} - \text{Speed\_op} \times K}{\text{DAMAGE\_SCALE}}\right)\right)\right)$$

*Donde:*
- **$K = 0.1$**: Factor de evasión por velocidad del defensor. Evita que la velocidad domine por completo la mitigación de daño.
- **$\text{DAMAGE\_SCALE} = 2$**: Divisor de calibración que duplica la duración promedio del combate, permitiendo la ejecución de estrategias de cambio (*switches*).
- **$\text{TypeModifier}$**: Multiplicador resultante del producto de efectividades frente a la tabla de tipos elementales.

---

### Tabla de Efectividad de Tipos

El multiplicador de tipo se obtiene de un chart oficial Gen 3 (fuente: Pokémon Showdown). Solo se almacenan las entradas no-unitarias — cualquier par no registrado vale 1.0 por defecto.

| Multiplicador | Significado |
|:---:|---|
| `0.0` | Inmune — el movimiento no hace daño |
| `0.5` | No muy efectivo |
| `1.0` | Neutro (por defecto) |
| `2.0` | Súper efectivo |

**Tipos duales**: cuando un Pokémon defiende con dos tipos, los multiplicadores son **multiplicativos**. Ejemplos:

| Atacante → Defensor | Tipo defensor | Multiplicador final |
|---|---|:---:|
| Fuego → Bulbasaur (Planta/Veneno) | Planta×2.0, Veneno×1.0 | **2.0×** |
| Tierra → Geodude (Roca/Tierra) | Roca×1.0, Tierra×1.0 | **1.0×** |
| Agua → Geodude (Roca/Tierra) | Roca×2.0, Tierra×2.0 | **4.0×** |
| Normal → Gengar (fantasma — no implementado) | Ghost×0.0 | **0.0×** |

Este multiplicador compuesto es el `TypeModifier` de la fórmula de daño y la base de los factores $f_{\text{ventaja tipo}}$ de la heurística.

---

### Flujo de Resolución de un Turno

Cada turno sigue este orden de resolución, respetado tanto por el motor real (`engine.py`) como por el simulador Minimax (`simulator.py`):

1. **Cambios forzados**: si algún Pokémon quedó debilitado el turno anterior, su entrenador elige un reemplazo antes de que comiencen las acciones normales.
2. **Selección de acciones**: cada agente elige su acción del conjunto de acciones legales.
3. **Ordenación de acciones**:
   - Los *switches* tienen **prioridad sobre los movimientos** — se ejecutan primero.
   - Dentro de la misma prioridad, el Pokémon de mayor velocidad actúa antes.
   - Empate de velocidad → desempate aleatorio.
4. **Ejecución en orden**: las acciones se aplican secuencialmente según el orden anterior.
5. **Cancelación de movimiento**: si el Pokémon que eligió un movimiento cae durante la ejecución de la acción del rival (que actuó primero por velocidad), su movimiento pendiente **se cancela** — el sustituto no hereda la acción del caído.
6. **Auto-switch**: tras cada acción que produce un KO, se resuelve inmediatamente el cambio forzado del equipo afectado.

---

### Sistema de PP y Struggle

Cada movimiento tiene un número limitado de **PP** (*Power Points*) que se consume al usarlo, incluso si el movimiento falla por precisión. Cuando el PP de un movimiento llega a 0, ese movimiento deja de estar disponible como acción legal.

Cuando un Pokémon no tiene ningún movimiento con PP restantes, la única acción disponible es **Struggle**:

$$\text{Daño} = \left\lfloor \text{Attack} \times 0.5 \right\rfloor \quad \text{(mínimo 1)}$$
$$\text{Retroceso} = \left\lfloor \text{Daño} / 4 \right\rfloor \quad \text{(mínimo 1)}$$

Struggle es el único mecanismo en PokeFISI donde un Pokémon puede eliminarse a sí mismo. La tabla de transposición registra los PP de cada movimiento en su hash de estado, garantizando que el agotamiento de PP produzca entradas distintas en la caché.

---

## 🎮 Niveles de Dificultad e IA

El simulador ofrece 4 niveles de dificultad bien definidos en `backend/config.py`:

| Nivel | Nombre | Clave API | Agente Subyacente | Profundidad ($d$) | Win Rate Esperado (Humano) | Propósito |
| :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **1** | Entrenamiento | `easy` | `RandomAgent` | - | 85% - 95% | Aprendizaje inicial y pruebas de flujo. |
| **2** | Competitivo | `medium` | `HeuristicAgent` | 1 | 60% - 70% | Oponente codicioso (*greedy*) de corto plazo. |
| **3** | Experto | `hard` | `MinimaxAgent` | 4 | 35% - 45% | Búsqueda táctica profunda con pesos calibrados manualmente. |
| **4** | Maestro | `sobrevilla` | `MinimaxAgent + GA` | 4 | 10% - 25% | Máximo desafío. Usa los pesos optimizados por el Algoritmo Genético. |

### HeuristicAgent — lógica interna

El `HeuristicAgent` (dificultad Media) evalúa **sin simular turnos futuros**: calcula un score para cada acción legal y elige la máxima.

**Movimientos**: el score es el balance de HP esperado tras el golpe.
$$\text{score\_move} = \text{HP\_total\_propio} - (\text{HP\_total\_rival} - \text{daño} \times \text{accuracy})$$

**Switches**: el score añade tres componentes al balance de HP base.

| Componente | Fórmula | Propósito |
|---|---|---|
| Ganancia de tipo | $(\text{best\_mult\_entrante} - 1.0) \times 30$ | Favorece al Pokémon con ventaja ofensiva sobre el rival activo |
| Reducción de vulnerabilidad | $(\text{mult\_rival\_vs\_actual} - \text{mult\_rival\_vs\_entrante}) \times 20$ | Penaliza quedarse si el rival ya tiene ventaja de tipo sobre el activo |
| Bonus de HP | $(\text{HP\_entrante} / \text{HP\_max}) \times 10$ | Prefiere traer Pokémon con más vida restante |

Este diseño hace que el agente cambie voluntariamente cuando está en desventaja de tipo real, a diferencia de un greedy puro que siempre prefiere atacar.

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

### Modo Determinista del Simulador

Durante la búsqueda Minimax, `simulate_turn()` se invoca con `deterministic=True`. En este modo, en lugar de muestrear la precisión del movimiento con una variable aleatoria (lo que haría el árbol no determinista y dependiente de la semilla), se usa directamente el **daño esperado**:

$$\text{Daño\_sim} = \text{round}(\text{Daño} \times \text{accuracy})$$

Esto garantiza que el mismo par (estado, acción) siempre produzca el mismo estado sucesor en el árbol, haciendo válida la búsqueda de Minimax de información perfecta. Sin este modo, dos ramas con el mismo movimiento podrían divergir por distinta suerte de precisión, invalidando la comparación de valores heurísticos. El motor de combate real sí muestrea la precisión de forma aleatoria — solo el simulador de lookahead opera en modo determinista.

### Telemetría del Agente

Tras cada llamada a `choose_action()`, el `MinimaxAgent` expone métricas de búsqueda en `last_choice_details`:

| Campo | Descripción |
|---|---|
| `nodes_evaluated` | Nodos del árbol evaluados en esa decisión (heurística o terminal) |
| `nodes_pruned` | Cortes alfa-beta realizados (ramas descartadas sin evaluar) |
| `transposition_hits` | Veces que un estado fue encontrado en la caché y no se recomputó |
| `time_taken` | Tiempo total de la búsqueda en segundos |

Estos valores son los que leen los scripts `scripts/export_metrics.py` y `scripts/run_minimax_experiment.py` para comparar eficiencia entre profundidades, factor Top-K y presencia de tabla de transposición.

---

## 🧬 Optimización con Algoritmo Genético

### Función Heurística Compuesta
La evaluación de las hojas del árbol se basa en una combinación lineal ponderada de 5 factores:

$$h(s, i) = W_1 \cdot f_{\text{pokemon vivos}}(s, i) + W_2 \cdot f_{\text{ventaja tipo}}(s, i) + W_3 \cdot f_{\text{velocidad}}(s, i) + W_4 \cdot f_{\text{hp restante}}(s, i) + W_5 \cdot f_{\text{riesgo morir}}(s, i)$$

**Detalle de cada factor, su fórmula de normalización y rango:**

**$f_{\text{pokemon vivos}}$** — Ventaja numérica de Pokémon saludables.
$$f_1 = \frac{\text{vivos\_propio} - \text{vivos\_rival}}{\text{team\_size}} \quad \in [-1,\ 1]$$

**$f_{\text{ventaja tipo}}$** — Matchup elemental del activo propio vs el rival activo. Toma el mejor multiplicador de tipo entre los movimientos de cada Pokémon, luego normaliza la diferencia. El clip es necesario porque con Pokémon de tipos duales los multiplicadores pueden llegar a 4×, haciendo que el valor crudo supere 1.0.
$$f_2 = \text{clip}\!\left(\frac{\text{best\_mult\_own} - \text{best\_mult\_opp}}{2},\ -1,\ 1\right) \quad \in [-1,\ 1]$$

**$f_{\text{velocidad}}$** — Diferencia relativa de velocidad entre los activos. Proxy continuo de dominancia táctica de velocidad (no binario). La velocidad ya reduce el daño recibido en la fórmula de daño; este factor captura su dimensión estratégica residual.
$$f_3 = \tanh\!\left(\frac{\text{speed\_propio} - \text{speed\_rival}}{100}\right) \quad \in (-1,\ 1)$$

**$f_{\text{hp restante}}$** — Ventaja de HP acumulado del equipo propio vs el rival. Cada ratio es HP\_actual / HP\_max sumado por todos los Pokémon del equipo.
$$f_4 = \text{ratio\_hp\_propio} - \text{ratio\_hp\_rival} \quad \in [-1,\ 1]$$

**$f_{\text{riesgo morir}}$** — Función de riesgo continua, no binaria. Calcula si el Pokémon activo puede ser KOado por el mejor movimiento del rival (daño esperado = daño × accuracy). La penalización escala linealmente entre los extremos y se agrava si el rival es más rápido (ataca primero).
$$\text{riesgo} = \begin{cases} 1.0 & \text{si } \text{hp} \leq \text{dmg\_max} \\ 0.0 & \text{si } \text{hp} \geq 2 \times \text{dmg\_max} \\ 1 - \dfrac{\text{hp} - \text{dmg\_max}}{\text{dmg\_max}} & \text{en otro caso} \end{cases}$$
$$\text{si rival es más rápido:}\quad \text{riesgo} \leftarrow \min(1.0,\ \text{riesgo} \times 1.5)$$
$$f_5 = -\text{riesgo} \quad \in [-1,\ 0]$$

**Escala de pesos y valores terminales:**

Los pesos manuales `MANUAL_WEIGHTS = [0.25, 0.35, 0.05, 0.20, 0.15]` suman 1.0, acotando $h \in [-1, 1]$. La elección de cada valor responde a una justificación táctica:

| Peso | Factor | Valor | Razonamiento |
|:---:|---|:---:|---|
| $W_1$ | Pokémon vivos | 0.25 | Ventaja numérica importante pero su señal cambia de golpe (±1/team\_size), no gradualmente |
| $W_2$ | Ventaja de tipo | 0.35 | El matchup elemental es la decisión táctica más determinante en PokeFISI — justifica el peso más alto |
| $W_3$ | Velocidad | 0.05 | La velocidad ya penaliza el daño recibido en la fórmula de daño; su información táctica residual es mínima |
| $W_4$ | HP restante | 0.20 | Mide la resistencia global del equipo; señal continua y gradual, segundo factor más informativo |
| $W_5$ | Riesgo de morir | 0.15 | Urgencia táctica — captura peligro inmediato no completamente reflejado en el HP ratio |

Los pesos del AG se optimizan en $[0, 1]$ por componente **sin restricción de suma**, por lo que la escala del resultado puede variar entre individuos. Esto no afecta la correctitud del Minimax porque los estados terminales devuelven $\pm 1000$, valor que domina cualquier evaluación heurística independientemente de la escala de pesos, garantizando que ganar siempre supere cualquier ventaja parcial de tablero.

### Función de Fitness
El algoritmo evalúa a cada individuo (un vector de pesos $W \in \mathbb{R}^5$) haciéndolo combatir $N$ veces contra el `HeuristicAgent` como oponente de referencia. El `HeuristicAgent` no simula turnos futuros: evalúa cada movimiento por su daño esperado y cada switch por una combinación de ventaja de tipo del entrante, reducción de vulnerabilidad del activo actual y HP ratio del entrante — lo que le permite cambiar voluntariamente ante desventajas de tipo reales sin ningún lookahead.

$$\text{Fitness}(W) = (\text{WinRate} \times 0.7) + (\text{MarginScore} \times 0.3)$$

- **$\text{WinRate}$**: Porcentaje de victorias obtenidas ($[0, 100]$).
- **$\text{MarginScore}$**: Promedio normalizado de la diferencia de Pokémon supervivientes al finalizar el encuentro ($[-100, 100]$).

El ratio 70/30 refleja que **ganar es el objetivo primario** — un individuo que pierde casi siempre no mejora aunque lo haga con margen ajustado. Sin embargo, un fitness puramente binario (solo win rate) otorgaría la misma puntuación a una victoria aplastante y a una victoria con 1 Pokémon restante, eliminando la señal de gradiente que el AG necesita para distinguir pesos buenos de pesos mediocres dentro de los ganadores. El `MarginScore` resuelve este empate y acelera la convergencia.

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

- **Ejecución de Tests**:
  ```bash
  pytest
  ```
  El suite cubre tres módulos con garantías tanto de correctitud como de comportamiento táctico:

  | Módulo | Qué verifica |
  |--------|-------------|
  | `tests/test_battle/test_damage.py` | Fórmula de daño, TypeModifier, mínimo garantizado de 1 |
  | `tests/test_battle/test_stats.py` | Fórmula de HP Gen 3 con IV/EV/Level fijos |
  | `tests/test_heuristics/test_heuristics.py` | Rango y monotonía de cada $f_i$ |
  | `tests/test_agents/test_minimax.py` | Correctitud y comportamiento táctico del agente |

  Los tests de Minimax incluyen **escenarios tácticos concretos** con nombres de Pokémon reales:
  - `test_does_not_modify_state` — el árbol de búsqueda nunca corrompe el estado de la partida real.
  - `test_deterministic_simulation_ignores_rng_sampling` — dos semillas distintas producen el mismo resultado en modo determinista.
  - `test_critical_knockout_action_is_kept_when_top_k_is_zero` — los KOs inmediatos nunca son eliminados por el recorte top-K.
  - `test_forced_switch_prefers_best_evaluated_replacement` — los cambios forzados usan la heurística para elegir el mejor sustituto.
  - `test_does_not_switch_sandshrew_into_meowth_against_brick_break` — escenario con Pokémon y movimientos reales que verifica que el agente evita un switch suicida.

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

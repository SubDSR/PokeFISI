# PokeFISI: Simulador Académico de Combates y Optimización Evolutiva de IA

PokeFISI es un simulador académico de combates por turnos basado en las mecánicas fundamentales de Pokémon (tipos elementales, estadísticas, daño y selección de equipos). Este proyecto ha sido desarrollado en el marco de la **Universidad Nacional Mayor de San Marcos (UNMSM) - Facultad de Ingeniería de Sistemas e Informática (FISI)**, con el objetivo de investigar la aplicación de algoritmos de teoría de juegos (Minimax con Poda Alfa-Beta) y algoritmos evolutivos (Algoritmo Genético) para la optimización de agentes de inteligencia artificial en entornos de decisión estocásticos y adversariales.

---

## 📌 Índice

1. [Descripción General](#-descripción-general)
2. [Arquitectura del Proyecto](#-arquitectura-del-proyecto)
3. [Mecánicas del Simulador](#-mecánicas-del-simulador)
   - [Balance de Equipos (Reglas 1 a 5)](#balance-de-equipos-reglas-1-a-5)
   - [Fórmula de Daño Calibrada](#fórmula-de-daño-calibrada)
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
9. [Justificación Académica](#-justificación-académica)

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
├── docs/                          # Justificaciones científicas e informes de complejidad
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
5. **Regla 5 (Exclusión Mutua)**: En la modalidad competitiva, un Pokémon no puede aparecer simultáneamente en ambos equipos.
6. **Balance Cruzado**: Si la diferencia de ventajas de tipo entre los equipos calculados supera un umbral de 2, el generador automáticamente reconstruye el equipo menos favorecido.

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

| Nivel | Nombre | Agente Subyacente | Profundidad ($d$) | Win Rate Esperado (Humano) | Propósito |
| :---: | :---: | :---: | :---: | :---: | :--- |
| **1** | Entrenamiento | `RandomAgent` | - | 85% - 95% | Aprendizaje inicial y pruebas de flujo. |
| **2** | Competitivo | `HeuristicAgent` | 1 | 60% - 70% | Oponente codicioso (*greedy*) de corto plazo. |
| **3** | Experto | `MinimaxAgent` | 4 | 35% - 45% | Búsqueda táctica profunda con pesos calibrados manualmente. |
| **4** | Maestro | `MinimaxAgent + GA` | 4 | 10% - 25% | Máximo desafío. Usa los pesos optimizados por el Algoritmo Genético. |

---

## 🧠 Agente Minimax y Optimizaciones

El `MinimaxAgent` modela el combate como un juego secuencial de información completa de dos jugadores. Para mitigar la explosión combinatoria ($O(b^{2d})$ donde $b \approx 6$ es el número de acciones y $d$ la profundidad de turnos), el agente incorpora las siguientes técnicas avanzadas:

```
                  [ Estado de Batalla Actual ]
                               │
               (Top-K Acciones Heurísticas Propias)
                               │
            ┌──────────────────┼──────────────────┐
        [Acción 1]          [Acción 2]         [Acción 3]
            │                  │                  │
   (Minimizar Turno Oponente) (Minimizar)    (Minimizar)
    ┌───────┼───────┐          ┌───┴───┐          ┌───┴───┐
[Resp1]  [Resp2]  [Resp3]     ...     ...        ...     ...
    │       │       │
 [Turno 2: Repetir Minimax Recursivo hasta d]
    │
[Evaluación Heurística Compuesta en Hojas] ──► Poda Alfa-Beta para cortar ramas
```

### Poda Alfa-Beta
Elimina la evaluación de subárboles cuyas ramas garanticen peores resultados que los ya descubiertos. Esto reduce el costo computacional a un caso óptimo de $O(b^d)$.

### Ordenamiento Heurístico (Move Ordering)
Antes de descender recursivamente en el árbol, las acciones disponibles son pre-evaluadas y ordenadas de manera óptima (de mayor a menor para el nodo MAX y de menor a mayor para el nodo MIN). Esto maximiza la probabilidad de encontrar cortes alfa-beta en etapas tempranas de la búsqueda recursiva.

### Tabla de Transposición
Utiliza una estructura de memoización en memoria para almacenar las evaluaciones de estados previamente visitados. Evita recomputar ramas duplicadas causadas por ciclos redundantes en la batalla (como cambios consecutivos de Pokémon entre turnos).

### Control de Ramificación (Top-K)
Limita la exploración a las $K = 6$ mejores acciones del turno. De esta manera, el factor de ramificación efectivo se mantiene controlado y el tiempo de respuesta del agente en una profundidad $d=4$ se sitúa consistentemente por debajo de los 0.5 segundos por turno.

---

## 🧬 Optimización con Algoritmo Genético

### Función Heurística Compuesta
La evaluación de las hojas del árbol se basa en una combinación lineal ponderada de 5 factores normalizados en el rango $[-1, 1]$ o $[-1, 0]$:

$$h(s, i) = W_1 \cdot f_{\text{pokemon vivos}}(s, i) + W_2 \cdot f_{\text{ventaja tipo}}(s, i) + W_3 \cdot f_{\text{velocidad}}(s, i) + W_4 \cdot f_{\text{hp restante}}(s, i) + W_5 \cdot f_{\text{riesgo morir}}(s, i)$$

*Donde:*
- $f_{\text{pokemon vivos}}$: Ventaja numérica de Pokémon saludables.
- $f_{\text{ventaja tipo}}$: Matchup elemental del Pokémon activo frente al rival.
- $f_{\text{velocidad}}$: Ventaja táctica de atacar primero.
- $f_{\text{hp restante}}$: Proporción de vida acumulada del equipo.
- $f_{\text{riesgo morir}}$: Penalización prospectiva si el Pokémon activo morirá en el siguiente turno.

### Función de Fitness
El algoritmo evalúa a cada individuo (un vector de pesos $W \in \mathbb{R}^5$) haciéndolo combatir $N$ veces contra el `HeuristicAgent` de referencia.

$$\text{Fitness}(W) = (\text{WinRate} \times 0.7) + (\text{MarginScore} \times 0.3)$$

- **$\text{WinRate}$**: Porcentaje de victorias obtenidas ($[0, 100]$).
- **$\text{MarginScore}$**: Promedio normalizado de la diferencia de Pokémon supervivientes al finalizar el encuentro ($[-100, 100]$).

### Operadores Evolutivos
- **Selección**: Torneo determinista de tamaño $k=4$.
- **Crossover**: Cruce de un punto y uniforme (tasa del 80%) para mantener la diversidad genética.
- **Mutación**: Mutación Gaussiana ($\sigma=0.1$, tasa del 20%) para realizar búsquedas refinadas locales.
- **Elitismo**: Preservación directa del $15\%$ de los mejores candidatos de la generación anterior.

---

## 🚀 Guía de Instalación y Ejecución

### Requisitos
- **Python**: Versión 3.10 o superior.
- **Node.js**: Versión 18 o superior y administrador de paquetes `npm`.

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

4. **Ejecutar una batalla simulada en consola (IA vs IA)**:
   ```bash
   python -m backend.main --mode battle --agent1 minimax --agent2 heuristic
   ```

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
  Genera los pesos óptimos y los guarda en `results/best_weights.json`, los cuales son leídos de manera automática por el servidor en la dificultad **Maestro (Sobrevilla)**.

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

## 🎓 Justificación Académica

- **Idoneidad de Minimax**: Los combates en PokeFISI se comportan como juegos matriciales por turnos, deterministas en su núcleo de cálculo físico, de suma cero e información perfecta. Esto encaja de manera natural en la formulación teórica de Minimax con poda Alfa-Beta (Von Neumann, 1928).
- **Ordenamiento Heurístico e Inspiración de A\***: El ordenamiento previo de movimientos toma el concepto de pre-evaluación del coste de transición de A\* para reordenar las ramas. Esto maximiza la cota inferior/superior de búsqueda recursiva de Alfa-Beta, transformando la complejidad del peor caso de la poda de $O(b^{2d})$ a un valor medio aproximado de $O(b^{3d/4})$.
- **Búsqueda de Gradiente Inexistente mediante GA**: La optimización del vector de pesos heurísticos carece de una función continua diferenciable debido a factores estocásticos y saltos discretos (como debilitamiento de Pokémon). Esto inhabilita el uso de algoritmos basados en gradiente (Gradient Descent), justificando el uso de Algoritmos Genéticos como aproximadores globales estocásticos robustos de caja negra.

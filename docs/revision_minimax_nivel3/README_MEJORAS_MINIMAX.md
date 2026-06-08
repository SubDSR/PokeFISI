# README Tecnico - Mejoras Para Que Minimax Maximice Victorias

## Punto De Partida

El objetivo ideal es que Minimax gane siempre. Con reglas simetricas, equipos aleatorios y movimientos con probabilidad de fallo, una garantia absoluta del 100% no es tecnicamente realista sin controlar o modificar condiciones del juego. Si se mantiene un juego justo y estocastico, el objetivo correcto es maximizar el win rate esperado y reducir derrotas evitables.

Para acercarse al ideal, las mejoras deben atacar tres frentes: calidad del modelo de decision, calidad de entrenamiento/evaluacion y control de condiciones de batalla.

## Prioridades Recomendadas

| Prioridad | Mejora | Impacto esperado |
|---:|---|---|
| 1 | Hacer determinista o expectimax la simulacion usada por Minimax. | Reduce decisiones ruidosas y mejora consistencia. |
| 2 | Explorar correctamente switches forzados y no elegir siempre el primer Pokemon vivo. | Evita derrotas por reemplazos tacticamente malos. |
| 3 | Corregir ordenamiento de acciones y revisar `top_k_actions`. | Evita excluir jugadas ganadoras. |
| 4 | Evaluar con equipos balanceados y semillas cruzadas. | Mide fuerza real del agente, no suerte de equipo. |
| 5 | Entrenar `best_weights.json` con validacion robusta. | Convierte Sobrevilla en un nivel realmente superior. |
| 6 | Agregar pruebas de regresion para casos donde Minimax pierde. | Evita que errores tacticos vuelvan a aparecer. |

## Mejoras De Algoritmo

### 1. Reemplazar azar en el arbol por valor esperado

Problema actual: `simulate_turn()` usa `rng.random()` para decidir si un movimiento falla dentro de la busqueda. Eso hace que una rama pueda verse buena o mala por una muestra aleatoria puntual.

Mejora recomendada:

| Opcion | Descripcion |
|---|---|
| Simulacion determinista por dano esperado | Aplicar `damage * accuracy` durante busqueda y reservar azar solo para batalla real. |
| Expectiminimax | Crear nodos de azar para hit/miss y calcular valor esperado. |
| Muestreo Monte Carlo por accion | Simular varias veces cada accion y promediar, con presupuesto de tiempo. |

Recomendacion practica: empezar con dano esperado determinista porque es simple, rapido y estable.

### 2. Resolver el juego simultaneo como matriz de pagos

El combate selecciona acciones simultaneamente y luego resuelve por switch/velocidad. El enfoque actual hace maximizacion de accion propia y minimizacion de respuestas rivales, lo cual aproxima una politica pesimista.

Mejora recomendada:

1. Construir matriz `valor[accion_propia][accion_rival]`.
2. Evaluar todas las respuestas legales relevantes del rival.
3. Elegir la accion con mejor valor minimo o resolver una estrategia mixta si se quiere robustez tipo Nash.

Beneficio: Minimax deja de depender tanto del orden de ramas y modela mejor la simultaneidad del turno.

### 3. Explorar switches forzados

Problema actual: tras un KO, el simulador selecciona el primer Pokemon vivo con `_auto_switch_fainted()`.

Mejora recomendada:

| Caso | Decision correcta |
|---|---|
| Minimax sufre KO | Evaluar todos los switches legales y escoger el mejor. |
| Rival sufre KO | Asumir que el rival escoge el switch mas perjudicial para Minimax. |
| Ambos sufren KO | Resolver ambos switches como subproblema simultaneo. |

Impacto: mejora mucho el juego de medio combate, especialmente cuando quedan 2 o 3 Pokemon.

### 4. Corregir `_quick_score()`

Problema actual: `calculate_damage()` ya incluye multiplicador de tipo, pero `_quick_score()` vuelve a multiplicar por `type_mod`.

Cambio recomendado:

```python
expected_dmg = calculate_damage(attacker, defender, move) * move.accuracy
```

Beneficio: el ordenamiento de acciones sera mas fiel al dano real. Esto importa porque `top_k_actions` puede dejar fuera acciones legales.

### 5. Ajustar `top_k_actions`

Problema actual: con 4 movimientos y 2 switches hay 6 acciones legales, pero `top_k_actions=5` puede excluir una.

Mejora recomendada:

| Regla | Motivo |
|---|---|
| Incluir siempre acciones letales. | Nunca excluir un KO posible. |
| Incluir siempre switches que eviten KO. | Evita suicidios tacticos. |
| Usar top-K dinamico. | `K = min(len(actions), base_k + acciones_criticas)`. |
| No podar switches cuando el activo esta en riesgo alto. | Los cambios suelen ser decisivos. |

### 6. Busqueda adaptativa

Propuesta:

| Tecnica | Uso |
|---|---|
| Iterative deepening | Profundizar mientras haya presupuesto de tiempo. |
| Quiescence search | Extender busqueda en estados con KO inminente. |
| Move ordering con TT | Reusar mejor accion previa para ordenar ramas. |
| Aspiration windows | Reducir ventana alfa-beta cuando hay valor esperado estable. |

Objetivo: mejorar calidad sin disparar tiempos de respuesta.

## Mejoras De Heuristica

### 1. Agregar dano esperado recibido

La heuristica actual incluye riesgo de morir, pero conviene sumar una estimacion mas continua:

```text
expected_exchange = expected_damage_done - expected_damage_received
```

Esto ayuda a elegir entre atacar, cambiar o conservar HP.

### 2. Valorar KOs inmediatos y supervivencia

Agregar bonificaciones fuertes:

| Situacion | Ajuste sugerido |
|---|---:|
| Movimiento propio hace KO este turno | `+alto` |
| Movimiento rival hace KO al activo | `-alto` |
| Switch evita KO y mantiene ventaja de tipo | `+medio/alto` |
| Ataque falla posible con baja accuracy y alternativa segura | Penalizacion por riesgo |

### 3. Evaluar cobertura del equipo completo

La ventaja de tipo del activo no basta. Minimax debe saber si el equipo restante tiene respuesta contra amenazas futuras.

Factores sugeridos:

| Factor | Descripcion |
|---|---|
| Cobertura ofensiva | Numero de rivales contra los que existe algun movimiento >= 2x. |
| Vulnerabilidad compartida | Penalizar si varios Pokemon son debiles al mismo tipo rival. |
| Valor del lead | Preferir activo que no obliga a switch inmediato. |
| Conservacion de win condition | Penalizar sacrificar el unico counter del rival. |

### 4. Incorporar PP y accuracy de forma tactica

Actualmente PP existe, pero la heuristica puede valorar mejor:

| Caso | Mejora |
|---|---|
| Movimiento fuerte con PP bajo | Usarlo si asegura KO; conservarlo si no cambia resultado. |
| Movimiento impreciso | Penalizar si una falla permite KO rival. |
| Struggle cercano | Penalizar quedarse sin PP util. |

## Mejoras De Entrenamiento Genetico

### 1. Generar realmente `best_weights.json`

Comando base:

```powershell
$env:PYTHONIOENCODING='utf-8'; python scripts/run_evolution.py --generations 50 --battles 30 --depth 1
```

Luego validar:

```powershell
python -m backend.main --mode experiment --agent1 minimax-optimized --agent2 heuristic --battles 100 --seed 7
python scripts/test_difficulty_levels.py --battles 100
```

### 2. Cambiar fitness para robustez

Fitness actual:

```text
fitness = win_rate * 0.7 + margin_score * 0.3
```

Mejora sugerida:

```text
fitness = 0.55 * win_rate
        + 0.20 * margin_score
        + 0.15 * cross_seed_stability
        + 0.10 * side_balance_score
```

Motivo: el agente no solo debe ganar en una semilla o lado; debe ganar consistentemente.

### 3. Entrenar contra varios rivales

No entrenar solo contra `HeuristicAgent`. Usar mezcla:

| Rival | Motivo |
|---|---|
| Random | Garantizar piso minimo. |
| Heuristic | Superar greedy fuerte. |
| Minimax manual | Mejorar contra si mismo. |
| Minimax optimizado anterior | Evitar regresion. |
| Politicas humanas simples | Cubrir patrones explotables como primera accion legal. |

### 4. Evaluacion con equipos balanceados y espejados

Para medir fuerza real:

1. Generar equipos con `build_balanced_teams()`.
2. Jugar batalla A: Minimax como jugador 1.
3. Jugar batalla B: mismos equipos invertidos.
4. Promediar resultados.

Esto reduce sesgo por ventaja inicial de equipo o lado.

## Mejoras De Validacion

### 1. Convertir `test_difficulty_levels.py` en prueba con fallo real

Actualmente imprime el resultado esperado, pero no falla si no se cumple.

Agregar condicion:

```text
Random < Heuristic < Minimax <= Sobrevilla
```

Si no se cumple, el script debe retornar codigo distinto de cero.

### 2. Agregar regresiones de batalla

Caso minimo a capturar:

| Caso | Resultado actual | Resultado esperado tras mejoras |
|---|---|---|
| `human` vs `minimax`, seed 7, entradas siempre `1` | Gana Jugador en 9 turnos | Gana Minimax o evita derrota tactica evidente. |
| `run_minimax_experiment`, depth=2, seed 7 | Minimax 40% | Minimax > 60% como minimo. |
| `export_metrics`, depth 2 | 35% | Depth 2 >= depth 1. |

### 3. Instalar y documentar tests

Opciones:

| Opcion | Comando |
|---|---|
| Instalar dependencia de test | `python -m pip install pytest` |
| Agregar extra de desarrollo | `pip install -e .[dev]` |
| CI recomendado | Ejecutar `python -m pytest` y scripts de dificultad. |

## Mejoras De Producto Para Garantizar Victoria

Si el requerimiento real es que Minimax gane siempre, no basta con mejorar algoritmo; hay que cambiar condiciones del juego.

Opciones de diseno:

| Opcion | Descripcion | Consecuencia |
|---|---|---|
| Dar ventaja de equipo a Minimax | Generar equipo de Minimax con mejor cobertura y BST. | Gana mas, pero deja de ser batalla justa. |
| Eliminar accuracy aleatoria | Todos los movimientos usan dano esperado o aciertan. | Reduce derrotas por azar. |
| Permitir preseleccion de lead | Minimax elige mejor Pokemon inicial tras ver rival. | Mejora mucho matchups iniciales. |
| Handicap al jugador | Reducir equipo, PP o dano del jugador. | Garantia artificial. |
| Reroll de equipos desfavorables | Reintentar generacion hasta que Minimax tenga ventaja. | Aumenta win rate pero sesga experimento. |

Recomendacion academica: no forzar victoria con handicap. Es mejor demostrar mejora medible con win rate alto, validacion cruzada y comparativas reproducibles.

## Roadmap Propuesto

| Fase | Accion | Criterio de aceptacion |
|---:|---|---|
| 1 | Corregir `_quick_score()` y top-K critico. | Minimax no excluye KOs ni switches defensivos. |
| 2 | Simulador determinista de valor esperado para busqueda. | Resultados reproducibles y menos varianza. |
| 3 | Switches forzados optimizados dentro del arbol. | Menos derrotas tras primer KO. |
| 4 | Experimentos con equipos balanceados/espejados. | Metricas reflejan fuerza del agente. |
| 5 | Entrenamiento genetico robusto y `best_weights.json`. | Sobrevilla supera a Minimax manual. |
| 6 | Validacion automatica y regresiones. | `test_difficulty_levels.py` falla si la jerarquia no se cumple. |

## Meta Recomendada

Antes de declarar que Minimax es el agente ideal, usar estos umbrales:

| Metrica | Umbral minimo recomendado |
|---|---:|
| Minimax vs Random | >= 90% |
| Minimax vs Heuristic | >= 70% |
| Sobrevilla vs Minimax manual | >= 55% |
| Depth 2 vs Depth 1 | Depth 2 no debe tener menor win rate en muestras grandes. |
| Pruebas de regresion | 100% pasando. |

Con esos cambios, Minimax no necesariamente ganara absolutamente todas las partidas justas, pero estara mucho mas cerca del comportamiento ideal y las derrotas seran explicables por azar, desventaja extrema de equipo o limites de profundidad.

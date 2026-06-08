# README Tecnico - Revision Total y Resultados Nivel 3

## Objetivo

Revisar el proyecto PokeFISI Nivel 3, ejecutar simulaciones de batalla contra Minimax usando los comandos indicados en `README_NIVEL3.md`, registrar una batalla reproducible `human` vs `minimax` y consolidar hallazgos tecnicos.

## Alcance Revisado

Se revisaron los modulos principales del backend, frontend, experimentos y documentacion:

| Area | Archivos principales | Observacion |
|---|---|---|
| CLI | `backend/main.py` | Expone modos `battle`, `experiment`, `serve` y agentes `random`, `heuristic`, `human`, `minimax`, `minimax-optimized`. |
| Motor de batalla | `backend/battle/engine.py`, `state.py`, `models.py`, `damage.py` | Turnos simultaneos por seleccion previa, switches con prioridad, ataques por velocidad y calculo de dano con tipos. |
| Simulador Minimax | `backend/battle/simulator.py` | Simula turnos sobre clones para evitar efectos secundarios en el estado real. |
| Agentes | `backend/agents/*.py` | Hay agentes Random, Human, Heuristic y Minimax con poda alfa-beta, top-K y tabla de transposicion. |
| Heuristicas | `backend/agents/heuristics.py` | Evaluacion compuesta por vivos, ventaja de tipo, velocidad, HP restante y riesgo de morir. |
| Configuracion | `backend/config.py` | `MINIMAX_DEPTH=4` para agente principal y pesos manuales `[0.25, 0.35, 0.05, 0.2, 0.15]`. |
| Experimentos | `backend/experiments/*`, `scripts/*.py` | Incluye batch, exportacion de metricas y algoritmo genetico para pesos. |
| API web | `backend/server.py`, `backend/session.py` | Servidor HTTP local con sesiones en memoria y selector de dificultad. |
| Frontend | `frontend/web/*` | Interfaz web estilo batalla Pokemon, dificultad seleccionable y modo IA vs IA. |
| Tests | `tests/*` | Existen tests unitarios, pero `pytest` no esta instalado en el entorno actual. |

## Comandos Ejecutados

### Verificacion de tests

```powershell
pytest
python -m pytest
```

Resultado:

| Comando | Resultado |
|---|---|
| `pytest` | No reconocido como comando global. |
| `python -m pytest` | `No module named pytest`. |

Conclusion: la suite existe, pero no pudo ejecutarse porque `pytest` es dependencia opcional y no esta instalada en este entorno.

### Experimentos batch con `backend.main`

```powershell
python -m backend.main --mode experiment --agent1 minimax --agent2 random --battles 20 --seed 7
python -m backend.main --mode experiment --agent1 random --agent2 minimax --battles 20 --seed 7
python -m backend.main --mode experiment --agent1 minimax --agent2 heuristic --battles 20 --seed 7
python -m backend.main --mode experiment --agent1 heuristic --agent2 minimax --battles 20 --seed 7
python -m backend.main --mode experiment --agent1 minimax-optimized --agent2 heuristic --battles 20 --seed 7
```

Resultados:

| Experimento | Victorias agente 1 | Victorias agente 2 | Empates | Win rate Minimax/Sobrevilla | Turnos promedio |
|---|---:|---:|---:|---:|---:|
| `minimax` vs `random` | 15 | 5 | 0 | 75.0% | 5.65 |
| `random` vs `minimax` | 5 | 15 | 0 | 75.0% | 5.70 |
| `minimax` vs `heuristic` | 13 | 7 | 0 | 65.0% | 5.25 |
| `heuristic` vs `minimax` | 10 | 10 | 0 | 50.0% | 5.45 |
| `minimax-optimized` vs `heuristic` | 13 | 7 | 0 | 65.0% | 5.25 |

Lectura tecnica:

| Hallazgo | Interpretacion |
|---|---|
| Minimax domina a Random con 75% desde ambos lados. | El agente supera decisiones aleatorias de forma clara. |
| Minimax no domina siempre a Heuristic. | Contra un agente greedy con switches, el resultado baja a 65% o 50% segun lado/semilla. |
| `minimax-optimized` replica el rendimiento manual. | No existe `results/best_weights.json`, por lo que `load_agent_weights()` cae a pesos manuales. |

### Batalla reproducible: yo contra Minimax

Comando usado:

```powershell
1..80 | ForEach-Object { '1' } | python -m backend.main --mode battle --agent1 human --agent2 minimax --seed 7 --message-delay 0 --decision-delay 0
```

Condicion de juego: el agente `human` recibio una secuencia fija de entradas `1`, por lo que siempre eligio la primera accion legal disponible. Esto vuelve la batalla reproducible y evita decisiones manuales no trazables.

Resultado:

| Campo | Valor |
|---|---|
| Ganador | `Jugador` |
| Turnos | 9 |
| Equipo jugador | Abra, Squirtle, Ponyta |
| Equipo Minimax | Magnemite, Psyduck, Machop |
| Politica humana usada | Elegir siempre la primera accion legal |

Resumen de eventos importantes:

| Turno | Evento |
|---:|---|
| 1 | Minimax cambia de Magnemite a Psyduck; Abra usa Confusion. |
| 2 | Psyduck derrota a Abra con Headbutt. |
| 3 | Squirtle deja a Psyduck en 9 HP usando Hydro Pump. |
| 5 | Magnemite derrota a Squirtle con Spark. |
| 6 | Ponyta golpea a Machop con Fire Fang tras cambio de Minimax. |
| 7 | Ponyta derrota a Machop. |
| 8 | Minimax cambia a Psyduck y Ponyta lo derrota. |
| 9 | Ponyta derrota a Magnemite con Fire Fang. |

Conclusion de esta batalla: Minimax perdio ante una politica humana simple y predecible. Esto evidencia que, en el estado actual, Minimax no garantiza victoria incluso cuando el rival no juega de forma sofisticada.

### Script Nivel 3: Minimax vs Heuristic

Comando indicado por `README_NIVEL3.md`:

```powershell
$env:PYTHONIOENCODING='utf-8'; python scripts/run_minimax_experiment.py --battles 30 --depth 2 --seed 7
```

Resultado:

| Agente | Victorias | Win rate |
|---|---:|---:|
| Minimax depth=2 | 12 | 40.0% |
| Heuristic | 18 | 60.0% |
| Empates | 0 | 0.0% |

Conclusion: en esta configuracion, el Minimax depth=2 pierde contra Heuristic. Esto contradice el objetivo ideal de que Minimax sea superior y refuerza la necesidad de mejorar evaluacion, simulacion y entrenamiento.

### Exportacion de metricas por profundidad

Comando indicado por `README_NIVEL3.md`:

```powershell
$env:PYTHONIOENCODING='utf-8'; python scripts/export_metrics.py --depths 1 2 --battles 20 --seed 7
```

Resultado de `results/depth_comparison.csv`:

| Depth | Batallas | Win rate | Nodos promedio | Podas promedio | Poda promedio | Tiempo promedio |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 20 | 45.0% | 8 | 3 | 28.8% | 0.50 ms |
| 2 | 20 | 35.0% | 15 | 7 | 32.0% | 0.78 ms |

Lectura tecnica: subir de depth 1 a depth 2 aumento nodos y poda, pero redujo win rate en esta muestra. Esto sugiere que el problema no es solo profundidad, sino calidad del modelo de simulacion/evaluacion.

### Validacion de niveles de dificultad

Comando:

```powershell
$env:PYTHONIOENCODING='utf-8'; python scripts/test_difficulty_levels.py --battles 20
```

Resultado:

| Comparacion | Win% nivel inferior | Win% nivel superior | Resultado esperado cumplido |
|---|---:|---:|---|
| Nivel1 Random vs Nivel2 Heuristic | 25.0% | 75.0% | Si |
| Nivel2 Heuristic vs Nivel3 Minimax | 50.0% | 50.0% | No, queda empatado |
| Nivel3 Minimax vs Nivel4 Sobrevilla | 70.0% | 30.0% | No |

Conclusion: la jerarquia esperada `Nivel 1 < Nivel 2 < Nivel 3 <= Nivel 4` no se cumple con la muestra ejecutada.

## Hallazgos Tecnicos Principales

| Severidad | Hallazgo | Evidencia | Impacto |
|---|---|---|---|
| Alta | Minimax no garantiza superioridad contra Heuristic. | 40% en `run_minimax_experiment.py`, 35% en depth=2 exportado, 50% cuando Heuristic inicia. | El Nivel 3 no cumple todavia el objetivo competitivo ideal. |
| Alta | La busqueda usa simulaciones estocasticas por precision de movimientos. | `simulate_turn()` usa `rng.random()` para accuracy durante el arbol. | La evaluacion de ramas puede ser ruidosa y dependiente del orden de exploracion. |
| Alta | El simulador de Minimax resuelve cambios forzados con el primer Pokemon vivo. | `_auto_switch_fainted()` no consulta al agente ni explora switches. | Pierde ramas tacticas importantes tras KO. |
| Media | `_quick_score()` duplica la ventaja de tipo en movimientos. | `calculate_damage()` ya aplica tipo y luego `_quick_score()` multiplica por `type_mod` otra vez. | Puede ordenar mal acciones y excluir jugadas por `top_k_actions`. |
| Media | `top_k_actions=5` puede excluir acciones legales. | En batallas 3v3 puede haber 6 acciones: 4 ataques + 2 switches. | Una accion ganadora puede quedar fuera del arbol. |
| Media | Los experimentos batch no siempre usan equipos balanceados entre ambos lados. | `run_experiment()` y scripts usan `build_random_team()` para cada lado. | El win rate mezcla calidad del agente con ventaja inicial de equipo. |
| Media | `minimax-optimized` no esta realmente optimizado si no existe `best_weights.json`. | No hay `results/best_weights.json`; `load_agent_weights()` usa fallback manual. | El nivel Sobrevilla puede ser solo Minimax manual con otro nombre. |
| Media | Scripts fallan en Windows cp1252 al imprimir `✓`. | `UnicodeEncodeError` sin `PYTHONIOENCODING=utf-8`. | Mala experiencia de ejecucion en Windows. |
| Media | Los tests existen pero no son ejecutables sin instalar dependencia opcional. | `python -m pytest` falla por modulo ausente. | No hay verificacion automatica inmediata del proyecto. |
| Baja | El servidor local no limpia sesiones antiguas. | `SessionStore` mantiene dict indefinidamente. | Riesgo de crecimiento de memoria en uso prolongado. |
| Baja | Servidor estatico sin validacion explicita de path resuelto. | `_serve_file(FRONTEND_WEB_DIR / relative)`. | Riesgo bajo en entorno local; conviene endurecer. |

## Conclusion General

El proyecto tiene una arquitectura clara y extensible: separa motor, estado, agentes, heuristicas, simulador, experimentos, servidor y frontend. El Nivel 3 ya implementa Minimax con alfa-beta, transposicion, top-K y pesos configurables.

Sin embargo, las simulaciones muestran que Minimax todavia no cumple el objetivo ideal de ganar consistentemente. El problema principal parece estar en la fidelidad/calidad de la busqueda, no solo en la profundidad: usa azar dentro del arbol, no optimiza switches forzados, puede excluir acciones por top-K, y la evaluacion de experimentos no siempre controla ventajas iniciales de equipo.

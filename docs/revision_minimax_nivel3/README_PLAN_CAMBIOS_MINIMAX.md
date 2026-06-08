# README Tecnico - Plan De Cambios Recomendados Para Minimax

## Objetivo

Definir un plan tecnico de implementacion para mejorar Minimax a partir de `README_MEJORAS_MINIMAX.md`, seleccionando las recomendaciones con mejor relacion impacto/riesgo/esfuerzo y evitando cambios que aumenten complejidad sin evidencia suficiente.

El objetivo practico no es prometer 100% de victorias en un juego justo con azar, sino aumentar el win rate esperado, reducir derrotas evitables y hacer que los resultados sean reproducibles, medibles y defendibles tecnicamente.

## Criterios De Seleccion

Las recomendaciones se priorizan con estos criterios:

| Criterio | Peso | Razon |
|---|---:|---|
| Impacto en win rate | Alto | El cambio debe mejorar decisiones reales de batalla. |
| Bajo riesgo de regresion | Alto | El motor de batalla ya funciona; conviene tocar lo minimo necesario. |
| Facilidad de verificacion | Alto | Cada cambio debe poder validarse con scripts o tests. |
| Complejidad controlada | Medio | Evitar expectimax completo o Nash si antes hay errores mas simples. |
| Compatibilidad con arquitectura actual | Medio | Aprovechar `BattleState.clone()`, `simulate_turn()`, heuristicas y scripts existentes. |

## Cambios Seleccionados

| Prioridad | Cambio | Decision | Motivo |
|---:|---|---|---|
| 1 | Corregir `_quick_score()` | Implementar primero | Es un bug tactico simple: el tipo se aplica dos veces al dano esperado. |
| 2 | Top-K seguro para acciones criticas | Implementar primero | Evita excluir KOs o switches defensivos. Bajo costo, alto impacto. |
| 3 | Simulacion determinista para busqueda | Implementar en fase 2 | Reduce ruido por accuracy dentro del arbol sin redisenar todo Minimax. |
| 4 | Switches forzados optimizados | Implementar en fase 2 | Corrige decisiones malas despues de KO. |
| 5 | Evaluacion con equipos balanceados/espejados | Implementar en fase 3 | Mejora la calidad de medicion antes de entrenar pesos. |
| 6 | Regresiones automaticas | Implementar en paralelo | Evita volver a perder casos ya identificados. |
| 7 | Entrenamiento genetico robusto | Implementar despues | Solo debe ejecutarse cuando la simulacion y metricas sean confiables. |

## Cambios Diferidos

| Recomendacion | Estado | Justificacion |
|---|---|---|
| Expectiminimax completo | Diferido | Correcto teoricamente, pero aumenta mucho la complejidad. Primero usar valor esperado determinista. |
| Resolver Nash/estrategia mixta | Diferido | Requiere mas modelado y no es necesario para corregir fallos actuales. |
| Iterative deepening | Diferido | Util si hay presupuesto de tiempo variable; primero estabilizar evaluacion. |
| Aspiration windows | Diferido | Optimizacion avanzada; aporta menos que corregir top-K y simulacion. |
| Handicaps para garantizar victoria | No recomendado | Sesga el juego y debilita la validez academica. |

## Fase 1 - Correcciones De Bajo Riesgo

### 1. Corregir `_quick_score()`

Archivo objetivo: `backend/agents/minimax_agent.py`.

Problema:

```python
expected_dmg = calculate_damage(attacker, defender, move) * move.accuracy * type_mod
```

`calculate_damage()` ya aplica `get_type_multiplier()`, por lo que multiplicar otra vez por `type_mod` sobrevalora ataques super efectivos y penaliza dos veces ataques resistidos.

Cambio recomendado:

```python
expected_dmg = calculate_damage(attacker, defender, move) * move.accuracy
```

Criterio de aceptacion:

| Validacion | Resultado esperado |
|---|---|
| Test unitario de ordenamiento | El score de movimiento coincide con dano real esperado normalizado. |
| Experimento `minimax` vs `heuristic` | No debe reducir win rate respecto a linea base. |

### 2. Hacer top-K seguro para acciones criticas

Archivo objetivo: `backend/agents/minimax_agent.py`.

Problema: `top_k_actions=5` puede excluir una accion legal cuando hay 6 opciones. Si la accion excluida es un KO o un switch defensivo, Minimax pierde capacidad tactica.

Diseno recomendado:

1. Mantener ranking heuristico actual como base.
2. Identificar acciones criticas antes de recortar.
3. Incluir siempre acciones criticas aunque excedan `top_k_actions`.
4. Deduplicar manteniendo orden.

Acciones criticas propuestas:

| Tipo | Regla |
|---|---|
| KO inmediato | Movimiento cuyo dano esperado o maximo derrota al activo rival. |
| Evitar KO | Switch a Pokemon que reduce dano esperado del rival cuando el activo propio esta en riesgo de morir. |
| Ultimo recurso | Cualquier switch legal si el activo propio puede morir este turno. |

Funcion sugerida:

```python
def _select_search_actions(self, state, actions, player_index, maximize=True):
    ordered = self._rank_actions(state, actions, player_index, maximize=maximize)
    critical = self._critical_actions(state, actions, player_index)
    selected = []
    for action in critical + ordered[: self.top_k_actions]:
        if action not in selected:
            selected.append(action)
    return selected
```

Criterio de aceptacion:

| Validacion | Resultado esperado |
|---|---|
| Estado con 6 acciones y KO en ultima posicion | Minimax evalua el KO. |
| Estado con activo en rango de morir | Al menos un switch defensivo entra al arbol. |

## Fase 2 - Mejorar Fidelidad De Busqueda

### 3. Simulacion determinista para Minimax

Archivo objetivo: `backend/battle/simulator.py` o nuevo helper local en `backend/agents/minimax_agent.py`.

Problema: la busqueda usa `rng.random()` para accuracy. Una rama puede parecer buena o mala por azar, no por valor esperado.

Decision recomendada: implementar un modo determinista de simulacion para Minimax que use dano esperado.

Opcion minima:

```python
expected_damage = int(round(calculate_damage(attacker, defender, move) * move.accuracy))
defender.hp = max(0, defender.hp - max(1, expected_damage))
```

Mejor practica: no cambiar el motor real `BattleEngine`; solo cambiar la simulacion usada por el arbol. La batalla real debe conservar accuracy probabilistica si el juego lo requiere.

Criterio de aceptacion:

| Validacion | Resultado esperado |
|---|---|
| Mismo estado, misma accion, multiples evaluaciones | Mismo valor de hoja. |
| `export_metrics.py` repetido con misma semilla | Mismos resultados. |
| Tiempo promedio | No debe crecer significativamente. |

### 4. Optimizar switches forzados dentro del arbol

Archivo objetivo: `backend/battle/simulator.py` y/o `backend/agents/minimax_agent.py`.

Problema: `_auto_switch_fainted()` elige el primer Pokemon vivo. Esa regla es rapida, pero tacticamente debil.

Diseno recomendado por fases:

| Fase | Implementacion | Riesgo |
|---|---|---|
| 2A | Elegir switch forzado con mejor `evaluate_state()` para el jugador afectado. | Bajo |
| 2B | Si el switch es del rival, elegir el peor estado para Minimax. | Medio |
| 2C | Explorar todos los switches forzados como subramas. | Alto |

Implementar primero 2A y 2B. Evitar 2C hasta medir costo.

Criterio de aceptacion:

| Validacion | Resultado esperado |
|---|---|
| Tras KO de Minimax | El reemplazo no es simplemente el primer Pokemon vivo si hay mejor opcion. |
| Tras KO rival | El rival simulado no elige una opcion claramente mala. |
| Batalla seed 7 contra politica `1` | Minimax evita la derrota tactica observada o mejora margen. |

## Fase 3 - Medicion Confiable

### 5. Experimentos balanceados y espejados

Archivos objetivo: `backend/experiments/simulate.py`, `scripts/export_metrics.py`, `scripts/run_minimax_experiment.py`.

Problema: usar `build_random_team()` por separado mezcla fuerza del agente con suerte de equipo.

Diseno recomendado:

1. Generar equipos con `build_balanced_teams()`.
2. Ejecutar batalla normal.
3. Ejecutar batalla invertida con mismos equipos clonados o reconstruidos desde especies.
4. Promediar resultado.

Metricas nuevas:

| Metrica | Uso |
|---|---|
| `win_rate_agent1` | Resultado directo. |
| `side_adjusted_win_rate` | Resultado corregido por lado. |
| `avg_alive_margin` | Calidad de victoria. |
| `seed_count` | Robustez del experimento. |

Criterio de aceptacion:

| Validacion | Resultado esperado |
|---|---|
| Mismas semillas | Resultados reproducibles. |
| Cambio de lado | La metrica reporta sesgo si existe. |
| Depth 2 vs depth 1 | La comparacion es mas estable que la actual. |

### 6. Regresiones automaticas

Archivos objetivo: `tests/test_agents/test_minimax.py`, nuevo `tests/test_experiments/test_minimax_regressions.py`.

Casos minimos:

| Caso | Asercion recomendada |
|---|---|
| `_quick_score()` no duplica tipo | Score proporcional a `calculate_damage() * accuracy`. |
| Accion letal no se excluye por top-K | Accion KO aparece en acciones seleccionadas para busqueda. |
| Simulacion determinista | Dos simulaciones identicas producen estado identico. |
| Switch forzado inteligente | No selecciona primer vivo si otro tiene mejor evaluacion. |

Adicional: instalar o documentar `pytest` como dependencia de desarrollo.

## Fase 4 - Sobrevilla Realmente Optimizado

### 7. Entrenamiento genetico robusto

Archivos objetivo: `backend/experiments/fitness.py`, `backend/experiments/evolution.py`, `scripts/run_evolution.py`.

Precondicion: no entrenar pesos hasta completar Fases 1 a 3. Entrenar sobre una simulacion ruidosa o metricas sesgadas produce pesos fragiles.

Cambios recomendados al fitness:

```text
fitness = 0.55 * win_rate
        + 0.20 * margin_score
        + 0.15 * cross_seed_stability
        + 0.10 * side_balance_score
```

Rivales de entrenamiento:

| Rival | Peso sugerido |
|---|---:|
| Random | 10% |
| Heuristic | 40% |
| Minimax manual | 30% |
| Politica humana simple | 20% |

Criterio de aceptacion:

| Validacion | Umbral |
|---|---:|
| `minimax-optimized` vs `heuristic` | >= 70% en 100 batallas. |
| `minimax-optimized` vs `minimax` | >= 55% en 100 batallas. |
| `test_difficulty_levels.py` | Cumple jerarquia esperada. |
| Archivo generado | `results/best_weights.json` valido y versionable si se decide. |

## Orden De Implementacion Recomendado

| Sprint | Cambios | Motivo |
|---:|---|---|
| 1 | `_quick_score()`, top-K critico, tests unitarios | Maximo impacto con bajo riesgo. |
| 2 | Simulacion determinista, switches forzados inteligentes | Mejora la calidad real de busqueda. |
| 3 | Experimentos balanceados/espejados, regresiones batch | Permite medir sin sesgo antes de entrenar. |
| 4 | Fitness robusto, entrenamiento y validacion de Sobrevilla | Optimiza sobre una base confiable. |

## Comandos De Validacion

Instalar tests si no existe `pytest`:

```powershell
python -m pip install pytest
```

Validacion rapida tras cada cambio:

```powershell
python -m pytest
python -m backend.main --mode experiment --agent1 minimax --agent2 random --battles 20 --seed 7
python -m backend.main --mode experiment --agent1 minimax --agent2 heuristic --battles 20 --seed 7
```

Validacion de Nivel 3:

```powershell
$env:PYTHONIOENCODING='utf-8'; python scripts/run_minimax_experiment.py --battles 30 --depth 2 --seed 7
$env:PYTHONIOENCODING='utf-8'; python scripts/export_metrics.py --depths 1 2 --battles 20 --seed 7
```

Validacion final de dificultad:

```powershell
$env:PYTHONIOENCODING='utf-8'; python scripts/test_difficulty_levels.py --battles 100
```

## Metas De Aceptacion

| Metrica | Linea base observada | Meta inicial | Meta ideal |
|---|---:|---:|---:|
| Minimax vs Random | 75% | >= 85% | >= 90% |
| Minimax vs Heuristic | 40%-65% | >= 60% | >= 70% |
| Depth 2 vs Depth 1 | Depth 2 menor | Depth 2 >= Depth 1 | Depth 2 claramente superior |
| Sobrevilla vs Minimax manual | 30% en validacion | >= 50% | >= 55% |
| Tests/regresiones | No ejecutables sin pytest | 100% pasando local | 100% en CI |

## Riesgos Y Mitigaciones

| Riesgo | Mitigacion |
|---|---|
| Mejorar win rate en una semilla y empeorar en otras | Validar con multiples semillas y equipos espejados. |
| Aumentar tiempo de decision | Medir `time_taken`, nodos y podas en cada experimento. |
| Cambiar comportamiento del motor real por accidente | Mantener cambios de simulacion dentro del arbol Minimax. |
| Entrenar pesos sobre metricas sesgadas | Entrenar solo despues de corregir medicion y simulacion. |
| Sobreoptimizar contra Heuristic | Entrenar contra mezcla de rivales. |

## Recomendacion Final

La mejor ruta tecnica es empezar por correcciones pequenas y verificables antes de introducir algoritmos mas complejos. El orden recomendado es:

1. Corregir `_quick_score()`.
2. Hacer top-K seguro para KOs y switches defensivos.
3. Hacer determinista la simulacion del arbol.
4. Mejorar switches forzados.
5. Medir con equipos balanceados/espejados.
6. Agregar regresiones.
7. Entrenar pesos y activar un `minimax-optimized` realmente superior.

Este plan sigue buenas practicas de ingenieria: cambios pequenos, impacto medible, regresiones automatizadas y optimizacion solo despues de estabilizar el modelo de evaluacion.

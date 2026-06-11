# README Tecnico - Correccion De Cambios Suicidas En Minimax

## Objetivo

Documentar los cambios necesarios para corregir el comportamiento observado donde Minimax realiza cambios voluntarios malos contra un jugador que repite `Brick Break`, sacrificando Pokemon sin obtener dano ni ventaja posicional.

El objetivo tecnico es que Minimax deje de tratar el cambio como una accion defensiva automaticamente buena y aprenda a castigar el costo real de cambiar: el Pokemon entrante recibe el ataque rival sin atacar ese turno.

## Caso Observado

Batalla reportada:

| Campo | Valor |
|---|---|
| Jugador | Machop, Poliwag, Vulpix |
| IA Minimax | Meowth, Sandshrew, Nidoran M |
| Patron del jugador | Repetir `Brick Break` con Machop |
| Resultado | Gana Jugador en 5 turnos |

Secuencia critica:

| Turno | Decision Minimax | Resultado |
|---:|---|---|
| 1 | Meowth cambia a Sandshrew | Aceptable: evita debilidad directa a Lucha, pero Sandshrew queda en 17/50. |
| 2 | Sandshrew cambia a Meowth | Error grave: Meowth entra contra `Brick Break` y muere. |
| 3 | Sandshrew cambia a Nidoran M | Error: Nidoran entra gratis contra `Brick Break` y queda en 11/46. |
| 4 | Nidoran cambia a Sandshrew | Error: Sandshrew entra debilitado y muere. |
| 5 | Nidoran usa `Earthquake` | Buena accion, pero demasiado tarde. |

Linea esperada:

| Turno | Decision esperada |
|---:|---|
| 1 | Cambiar Meowth a Sandshrew puede ser aceptable. |
| 2 | Sandshrew debe atacar antes de caer, no cambiar a Meowth. |
| 3 | Si Sandshrew cae, entrar con Nidoran M. |
| 4 | Nidoran M debe usar `Earthquake` inmediatamente. |

## Diagnostico Tecnico

### Que ya se esta aplicando

Los cambios previos ya cubren parte del plan general:

| Mejora | Estado | Archivo |
|---|---|---|
| No duplicar multiplicador de tipo en `_quick_score()` | Aplicado | `backend/agents/minimax_agent.py` |
| No excluir acciones criticas por `top_k_actions` | Aplicado | `backend/agents/minimax_agent.py` |
| Simulacion determinista por dano esperado en el arbol | Aplicado | `backend/battle/simulator.py` |
| Switches forzados tacticos | Aplicado parcialmente | `backend/agents/minimax_agent.py` |
| Experimentos con equipos balanceados | Aplicado parcialmente | `backend/experiments/*`, `scripts/*` |

### Que no se esta aplicando todavia

El problema observado corresponde a una brecha distinta: cambios voluntarios suicidas.

| Brecha | Descripcion |
|---|---|
| No hay penalizacion explicita por cambiar hacia un ataque letal probable. | `_score_switch()` evalua tipo, HP y vulnerabilidad general, pero no castiga suficientemente que el rival puede repetir el ataque actual. |
| No se compara `switch` contra `atacar antes de morir`. | Si el Pokemon activo ya esta perdido, a veces conviene atacar y causar dano antes de caer. |
| No hay memoria del patron del jugador. | El agente no modela que el humano acaba de usar `Brick Break` repetidamente. |
| La heuristica subvalora tempo/material. | Cambiar consume el turno ofensivo; si el entrante recibe KO o queda casi muerto, se pierde material gratis. |
| Falta telemetria de lineas Minimax. | No se imprime por que una accion fue elegida ni que respuesta rival asumio. |

## Causa Probable

Minimax puede estar sobrevalorando switches porque `_score_switch()` considera vulnerabilidad general ante los movimientos del rival, pero no calcula con fuerza suficiente el resultado inmediato de:

```text
rival repite mejor movimiento probable -> Pokemon entrante recibe dano -> no hay dano propio este turno
```

En el caso reportado, cambiar a Meowth contra Machop es malo porque:

| Factor | Efecto |
|---|---|
| Meowth es tipo Normal | Debil a Lucha. |
| Machop usa `Brick Break` | Movimiento Fighting de alto impacto. |
| Switch tiene prioridad | Meowth entra antes de recibir el ataque. |
| Meowth no ataca ese turno | La IA pierde tempo. |
| Resultado | Meowth muere gratis. |

## Cambios Recomendados

### 1. Penalizar switch voluntario que recibe KO inmediato

Archivo objetivo: `backend/agents/minimax_agent.py`.

Agregar una evaluacion directa del dano que recibiria el Pokemon entrante ante la mejor respuesta ofensiva del rival.

Regla:

```text
si accion == switch y max_expected_damage(rival_activo, pokemon_entrante) >= hp_entrante:
    score_switch -= penalizacion_muy_alta
```

Penalizacion sugerida:

| Caso | Penalizacion |
|---|---:|
| Entrante muere por mejor ataque rival | `-2.0` o menor |
| Entrante queda con menos de 25% HP | `-0.8` |
| Entrante recibe mas dano que el activo actual | `-0.4` |

Criterio de aceptacion:

| Estado | Resultado esperado |
|---|---|
| Machop activo con `Brick Break`, Meowth en banca | Meowth no debe ser elegido como switch voluntario. |
| Sandshrew en 17/50 frente a Machop | Si todos los switches son malos, Sandshrew debe atacar antes de caer. |

### 2. Comparar valor de atacar antes de morir vs cambiar

Archivo objetivo: `backend/agents/minimax_agent.py`.

Agregar regla de conservacion de tempo:

```text
si activo esta en rango de KO:
    si puede causar dano significativo antes de morir:
        aumentar prioridad de ataques
        reducir prioridad de switches que tambien quedan en rango de KO
```

Esto corrige el caso Sandshrew: aunque Sandshrew vaya a morir, puede usar `Bulldoze`, `Rock Slide` o `Scratch` antes de caer. Cambiar a Meowth no causa dano y pierde un Pokemon.

Metrica sugerida:

```text
tempo_value = expected_damage_done_by_active - expected_damage_taken_by_switch
```

Criterio de aceptacion:

| Estado | Resultado esperado |
|---|---|
| Activo debilitado, rival puede matarlo, activo puede danar | Preferir ataque si los switches mueren o quedan inutiles. |
| Activo debilitado, switch seguro con ventaja real | Permitir switch. |

### 3. Simular switch con castigo inmediato en `_quick_score()`

Archivo objetivo: `backend/agents/minimax_agent.py`.

Modificar `_score_switch()` para incluir tres terminos nuevos:

| Termino | Descripcion |
|---|---|
| `incoming_survival` | HP restante esperado del entrante tras mejor ataque rival. |
| `tempo_penalty` | Penalizacion por no atacar este turno. |
| `bad_switch_penalty` | Penalizacion fuerte si el switch aumenta el dano recibido. |

Formula propuesta:

```text
score_switch = base_type_score
             + hp_score
             + survival_score
             - tempo_penalty
             - lethal_switch_penalty
```

Donde:

```text
survival_score = max(0, hp_entrante - dano_rival_esperado) / max_hp_entrante
lethal_switch_penalty = 2.0 si hp_entrante <= dano_rival_esperado
tempo_penalty = mejor_dano_que_activo_puede_hacer / hp_rival_max * 0.5
```

### 4. Agregar memoria corta del ultimo movimiento humano

Archivo objetivo: `backend/battle/state.py` o `backend/agents/minimax_agent.py`.

Actualmente Minimax evalua el estado visible, pero no tiene una senal explicita de que el rival esta repitiendo un movimiento. Para jugadores humanos, una memoria corta puede mejorar la prediccion.

Opcion minima:

| Cambio | Descripcion |
|---|---|
| Guardar ultimo movimiento por jugador en `BattleState.log` parseado | No recomendado: fragil. |
| Agregar `last_actions` en `BattleState` | Recomendado: estructurado. |
| Pasar historial al agente via UI/engine | Mas invasivo. |

Recomendacion:

```python
BattleState.last_actions: list[BattleAction | None]
```

Luego, en el motor:

```python
self.state.last_actions[player_index] = action
```

Uso en Minimax:

```text
si rival uso el mismo movimiento ofensivo en turnos recientes:
    elevar prioridad de esa respuesta rival en el arbol
```

Esto ayuda a detectar `Brick Break` repetido.

### 5. Agregar telemetria de decision

Archivo objetivo: `backend/agents/minimax_agent.py`, `backend/ui/console.py`.

Actualmente se imprime accion elegida, nodos y poda, pero no se ve la razon. Para depurar casos como este se necesita registrar:

| Campo | Uso |
|---|---|
| `candidate_scores` | Valor minimax de cada accion candidata. |
| `worst_response` | Respuesta rival que Minimax asumio para cada accion. |
| `switch_survival` | HP esperado del entrante tras mejor ataque rival. |
| `rejected_critical_actions` | Acciones que entraron como criticas y su valor. |

Ejemplo esperado:

```json
{
  "chosen_action": "Usar Earthquake",
  "candidate_scores": [
    {"action": "Cambiar a Meowth", "value": -0.72, "worst_response": "Brick Break"},
    {"action": "Usar Bulldoze", "value": -0.20, "worst_response": "Brick Break"}
  ]
}
```

## Pruebas De Regresion Necesarias

Crear pruebas especificas para el caso reportado.

Archivo sugerido: `tests/test_agents/test_minimax_switches.py`.

### Test 1: no cambiar a Meowth contra Brick Break

Estado:

| Lado | Pokemon |
|---|---|
| Jugador | Machop con `Brick Break` |
| Minimax activo | Sandshrew 17/50 |
| Minimax banca | Meowth 40/40, Nidoran M 11/46 |

Asercion:

```text
Minimax no debe elegir Cambiar a Meowth.
```

### Test 2: atacar si todos los switches son malos

Estado:

| Condicion | Valor |
|---|---|
| Activo de Minimax | Sandshrew debilitado |
| Rival | Machop repitiendo `Brick Break` |
| Switches disponibles | Mueren o quedan muy debilitados |

Asercion:

```text
Minimax debe elegir un movimiento ofensivo, no switch.
```

### Test 3: Nidoran usa Earthquake inmediatamente

Estado:

| Condicion | Valor |
|---|---|
| Activo Minimax | Nidoran M |
| Rival | Machop |
| Mejor movimiento | `Earthquake` |

Asercion:

```text
Minimax debe elegir Earthquake si es el mejor dano esperado y no hay switch seguro.
```

## Validacion Manual Recomendada

Repetir una batalla equivalente y verificar que la IA no rote inutilmente:

```powershell
python -m backend.main --mode battle --agent1 human --agent2 minimax --seed <seed_del_caso>
```

Durante los turnos:

| Turno | Resultado esperado |
|---:|---|
| 1 | Puede cambiar Meowth a Sandshrew si Meowth muere ante Lucha. |
| 2 | Sandshrew no debe cambiar a Meowth si `Brick Break` lo mata. |
| 3 | Nidoran debe atacar con `Earthquake` si entra frente a Machop. |

## Orden De Implementacion

| Prioridad | Cambio | Riesgo | Impacto |
|---:|---|---|---|
| 1 | Penalizar switch que recibe KO inmediato | Bajo | Alto |
| 2 | Preferir atacar antes de morir si los switches son malos | Medio | Alto |
| 3 | Agregar regresiones del caso Machop vs Meowth/Sandshrew/Nidoran | Bajo | Alto |
| 4 | Agregar telemetria de candidate scores | Bajo | Medio |
| 5 | Agregar memoria corta de acciones rivales | Medio | Medio/Alto |

## Criterios De Aceptacion

| Metrica | Umbral |
|---|---:|
| Caso Machop spameando `Brick Break` | Minimax no debe regalar dos o mas Pokemon por switch. |
| Minimax vs Random | Mantener >= 90% en 20 batallas seed 7. |
| Minimax vs Heuristic | Mejorar o mantener >= 60% en validacion rapida. |
| Depth 2 vs Depth 1 | Depth 2 debe mantenerse superior. |
| Tests de regresion | 100% pasando. |

## Conclusion

El comportamiento observado confirma que Minimax todavia no evalua suficientemente el costo tactico de cambiar. Las mejoras previas ayudan a la busqueda general, pero falta una capa anti-switch-suicida que penalice entrar contra ataques letales, valore el tempo perdido y prefiera causar dano antes de sacrificar material.

La correccion mas importante es modificar la evaluacion de switches voluntarios para que responda esta pregunta antes de cambiar:

```text
Si el rival repite su mejor ataque, el Pokemon entrante sobrevive y mejora la posicion?
```

Si la respuesta es no, Minimax debe atacar, no cambiar.

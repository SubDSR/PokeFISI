# Calculo Tecnico De PS De Pokemon

## Objetivo

Definir como calcular los PS finales de cada Pokemon usando la formula oficial indicada, tomando como `Base` el valor `hp` que ya existe en el codigo dentro de `backend/data/pokemon.py`.

## Formula Base

```text
PS = floor((((2 * Base + IV + floor(EV / 4)) * Nivel) / 100)) + Nivel + 10
```

Donde:

| Variable | Descripcion | Valor para PokeFISI |
|---|---|---:|
| `Base` | PS base del Pokemon | `PokemonSpecies.hp` |
| `IV` | Valor individual | `31` |
| `EV` | Puntos de esfuerzo | `0` |
| `Nivel` | Nivel del Pokemon | `50` |

## Fuente Del PS Base En El Codigo

Actualmente el PS base esta definido en `backend/data/pokemon.py` como el campo `hp` de cada `PokemonSpecies`.

Ejemplo:

```python
PokemonSpecies(
    id="bulbasaur",
    name="Bulbasaur",
    level=50,
    hp=45,
    attack=49,
    defense=49,
    speed=45,
    ...
)
```

En este caso:

```text
Base = 45
```

## Simplificacion Con Los Valores Del Proyecto

Valores fijos:

```text
IV = 31
EV = 0
Nivel = 50
```

Primero se reemplaza `EV`:

```text
floor(EV / 4) = floor(0 / 4) = 0
```

La formula queda:

```text
PS = floor((((2 * Base + 31 + 0) * 50) / 100)) + 50 + 10
```

Se simplifica `50 / 100`:

```text
PS = floor(((2 * Base + 31) * 0.5)) + 60
```

Equivalente:

```text
PS = floor((2 * Base + 31) / 2) + 60
```

Como `2 * Base` siempre es par y `31` es impar:

```text
floor((2 * Base + 31) / 2) = Base + 15
```

Por lo tanto, para este proyecto con `IV=31`, `EV=0` y `Nivel=50`:

```text
PS = Base + 75
```

## Formula Final Recomendada Para PokeFISI

```text
PS_final = PokemonSpecies.hp + 75
```

Esta simplificacion solo es valida mientras se mantengan fijos estos valores:

| Parametro | Valor |
|---|---:|
| `IV` | `31` |
| `EV` | `0` |
| `Nivel` | `50` |

Si en el futuro el proyecto permite niveles, IVs o EVs variables, se debe volver a usar la formula completa.

## Ejemplos Con Pokemon Del Codigo

| Pokemon | Base actual (`hp`) | Calculo | PS final |
|---|---:|---|---:|
| Bulbasaur | 45 | `45 + 75` | 120 |
| Charmander | 39 | `39 + 75` | 114 |
| Squirtle | 44 | `44 + 75` | 119 |
| Pikachu | 35 | `35 + 75` | 110 |
| Machop | 70 | `70 + 75` | 145 |
| Abra | 25 | `25 + 75` | 100 |
| Slowpoke | 90 | `90 + 75` | 165 |

## Comparacion Con El Comportamiento Actual

Actualmente `backend/battle/factory.py` asigna directamente el PS base como PS maximo y PS actual:

```python
max_hp=species.hp,
hp=species.hp,
```

Eso significa que hoy un Bulbasaur con `hp=45` entra a batalla con:

```text
PS actual = 45
PS maximo = 45
```

Con la formula tecnica propuesta deberia entrar con:

```text
PS actual = 120
PS maximo = 120
```

## Implementacion Recomendada

Crear una funcion pequena y testeable para calcular PS.

Ubicacion sugerida:

```text
backend/battle/stats.py
```

Funcion sugerida:

```python
def calculate_hp(base: int, iv: int = 31, ev: int = 0, level: int = 50) -> int:
    return ((2 * base + iv + (ev // 4)) * level) // 100 + level + 10
```

Uso recomendado en `backend/battle/factory.py`:

```python
calculated_hp = calculate_hp(species.hp, level=species.level)

return BattlePokemon(
    ...
    max_hp=calculated_hp,
    hp=calculated_hp,
    ...
)
```

## Criterios De Aceptacion

| Caso | Resultado esperado |
|---|---:|
| `calculate_hp(45)` | `120` |
| `calculate_hp(39)` | `114` |
| `calculate_hp(44)` | `119` |
| `calculate_hp(35)` | `110` |
| `calculate_hp(70)` | `145` |
| `calculate_hp(90)` | `165` |

## Impacto Esperado En Batallas

Aplicar esta formula aumenta significativamente los PS porque el codigo actual usa el valor base directamente.

Efectos esperados:

| Area | Impacto |
|---|---|
| Duracion de batallas | Aumenta, porque los Pokemon tendran mas PS. |
| Formula de dano | Puede requerir recalibracion si las batallas se vuelven demasiado largas. |
| Minimax | Evaluara estados con mas margen de supervivencia. |
| Heuristicas de HP | Seguiran funcionando porque usan ratios (`hp / max_hp`). |
| UI | Mostrara barras de PS mas altas, sin cambios estructurales. |

## Nota Tecnica

Aunque para los valores fijos del proyecto se puede usar `Base + 75`, es mejor implementar la formula completa con `IV`, `EV` y `Nivel` como parametros. Esto mantiene el codigo claro, facilita pruebas y evita reescrituras si luego se agregan niveles o entrenamiento.

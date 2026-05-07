# Resultados de pruebas: Heurística vs Random

## Objetivo

Documentar y comparar el comportamiento de las siguientes configuraciones de agentes:

- `heuristic` vs `heuristic`
- `heuristic` vs `random`
- `random` vs `heuristic`
- `random` vs `random`

Además, mostrar el efecto de escalar el número de simulaciones a `10`, `100` y `1000` batallas.

## Metodología

- Motor usado: `python -m backend.main --mode experiment`
- Tamaño de equipo: `3`
- Semilla fija: `7`
- Métricas observadas: victorias por jugador, tasa de victorias, promedio de turnos y tiempo aproximado de ejecución.

Nota: al fijar la semilla, los resultados son reproducibles en el mismo entorno. No hubo empates en ninguna corrida.

## Comparativa principal (100 batallas)

Esta tabla resume una comparativa base con `100` batallas por configuración, porque ya reduce bastante la variación de una muestra chica y sigue siendo fácil de interpretar.

| Configuración | Victorias J1 | Victorias J2 | Tasa de victorias J1 | Tasa de victorias J2 | Prom. turnos |
| --- | ---: | ---: | ---: | ---: | ---: |
| `heuristic` vs `heuristic` | 53 | 47 | 53.0% | 47.0% | 4.22 |
| `heuristic` vs `random` | 72 | 28 | 72.0% | 28.0% | 4.34 |
| `random` vs `heuristic` | 29 | 71 | 29.0% | 71.0% | 4.63 |
| `random` vs `random` | 51 | 49 | 51.0% | 49.0% | 5.75 |

## Lectura rápida

- El agente `heuristic` supera claramente al agente `random` en ambas direcciones.
- Cuando ambos agentes son iguales, el resultado se acerca al `50/50`, como era esperable.
- Las batallas `random` vs `random` duran más turnos en promedio.
- Las batallas `heuristic` vs `heuristic` tienden a resolverse más rápido.

## Experimento comparativo: 10, 100 y 1000 batallas

| Batallas | Configuración | Victorias | Tasa de victorias | Prom. turnos | Tiempo aprox. |
| ---: | --- | --- | --- | ---: | ---: |
| 10 | `heuristic` vs `heuristic` | J1: 7, J2: 3 | J1: 70.0%, J2: 30.0% | 3.80 | 0.0033 s |
| 10 | `heuristic` vs `random` | J1: 6, J2: 4 | J1: 60.0%, J2: 40.0% | 4.60 | 0.0029 s |
| 10 | `random` vs `heuristic` | J1: 3, J2: 7 | J1: 30.0%, J2: 70.0% | 4.50 | 0.0028 s |
| 10 | `random` vs `random` | J1: 3, J2: 7 | J1: 30.0%, J2: 70.0% | 5.60 | 0.0027 s |
| 100 | `heuristic` vs `heuristic` | J1: 53, J2: 47 | J1: 53.0%, J2: 47.0% | 4.22 | 0.0294 s |
| 100 | `heuristic` vs `random` | J1: 72, J2: 28 | J1: 72.0%, J2: 28.0% | 4.34 | 0.0267 s |
| 100 | `random` vs `heuristic` | J1: 29, J2: 71 | J1: 29.0%, J2: 71.0% | 4.63 | 0.0278 s |
| 100 | `random` vs `random` | J1: 51, J2: 49 | J1: 51.0%, J2: 49.0% | 5.75 | 0.0273 s |
| 1000 | `heuristic` vs `heuristic` | J1: 481, J2: 519 | J1: 48.1%, J2: 51.9% | 4.17 | 0.2911 s |
| 1000 | `heuristic` vs `random` | J1: 763, J2: 237 | J1: 76.3%, J2: 23.7% | 4.42 | 0.2708 s |
| 1000 | `random` vs `heuristic` | J1: 227, J2: 773 | J1: 22.7%, J2: 77.3% | 4.48 | 0.2721 s |
| 1000 | `random` vs `random` | J1: 520, J2: 480 | J1: 52.0%, J2: 48.0% | 5.96 | 0.2782 s |

## Análisis comparativo

### 1. Efecto del número de batallas

- Con solo `10` batallas hay mucha variación. Por ejemplo, `heuristic` vs `heuristic` aparece como `70/30`, pero eso no representa el equilibrio real entre agentes idénticos.
- Con `100` batallas, los resultados ya empiezan a estabilizarse y muestran mejor la tendencia general.
- Con `1000` batallas, los espejos (`heuristic` vs `heuristic` y `random` vs `random`) quedan muy cerca de `50/50`, lo que da una señal más confiable.

### 2. Desempeño del agente heurístico

- En `heuristic` vs `random`, el agente heurístico ganó `76.3%` cuando fue Jugador 1.
- En `random` vs `heuristic`, el agente heurístico ganó `77.3%` cuando fue Jugador 2.
- Esto sugiere que la ventaja viene de la estrategia del agente, no del lado en el que juega.

### 3. Duración promedio de las batallas

- `heuristic` vs `heuristic`: entre `3.80` y `4.22` turnos en muestras chicas y `4.17` en `1000` batallas.
- `heuristic` vs `random`: alrededor de `4.3` a `4.6` turnos.
- `random` vs `random`: es la configuración más larga, llegando a `5.96` turnos en `1000` batallas.

Interpretación: el agente heurístico toma decisiones más agresivas o más eficientes para cerrar el combate en menos turnos que un agente aleatorio.

### 4. Costo computacional

- El tiempo de ejecución escala casi linealmente con el número de batallas.
- Pasar de `10` a `100` batallas multiplica el tiempo aproximadamente por `10`.
- Pasar de `100` a `1000` vuelve a multiplicarlo aproximadamente por `10`.

Esto hace que `1000` batallas sea un punto razonable cuando se busca una comparativa más estable sin un costo alto de ejecución.

## Conclusiones

1. El agente `heuristic` es claramente superior al agente `random` en este simulador.
2. Los enfrentamientos espejo convergen hacia un comportamiento cercano a `50/50`, especialmente con `1000` batallas.
3. Las pruebas con `10` batallas sirven como ejemplo rápido, pero no son suficientes para sacar conclusiones sólidas.
4. Las pruebas con `100` batallas son útiles para una comparativa intermedia.
5. Las pruebas con `1000` batallas ofrecen la lectura más confiable de desempeño relativo.

## Recomendación

Si el objetivo es presentar resultados académicos o una comparativa técnica, conviene usar `1000` batallas por configuración como referencia principal y dejar `10` y `100` como escalas de contraste para mostrar la estabilidad estadística.

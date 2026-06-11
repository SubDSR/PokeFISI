# Justificación Académica de Algoritmos — PokeFISI

## A. Por qué Minimax es el Algoritmo Correcto

### Propiedades del dominio que justifican Minimax:

| Propiedad | Valor en PokeFISI |
|-----------|-------------------|
| Número de agentes | 2 (adversarial) |
| Tipo de juego | Suma cero |
| Información | Completa (ambos ven el estado) |
| Decisiones | Deterministas + precisión aleatoria |
| Horizonte | Finito (~10–30 turnos) |

Un juego de **suma cero con dos adversarios e información completa** es el dominio
canónico de Minimax (Von Neumann, 1928). La victoria de un jugador implica la
derrota del otro, por lo que maximizar la utilidad propia equivale a minimizar
la utilidad del oponente.

### Por qué NO usar otros algoritmos:

- **A\* / Best-First Search**: diseñados para un solo agente que busca un camino
  a un objetivo. No modelan la respuesta adversarial del oponente.
- **Hill-Climbing**: puede quedar atrapado en óptimos locales y no anticipa
  la respuesta del rival.
- **MCTS (Monte Carlo Tree Search)**: aplicable pero requiere muchas simulaciones
  aleatorias; Minimax con buena heurística es más eficiente en horizontes cortos.

---

## B. Cómo el Ordenamiento Heurístico (A*-inspired) Mejora Minimax

### Concepto de A*:

A\* usa una función de evaluación `f(n) = g(n) + h(n)` donde:
- `g(n)`: costo acumulado desde el inicio
- `h(n)`: estimación del costo restante al objetivo

### Aplicación en PokeFISI:

En el agente Minimax de PokeFISI, **no se usa A\*** como algoritmo de búsqueda —
son algoritmos fundamentalmente distintos. En cambio, se toma prestada la idea
de la **función de evaluación heurística** para ordenar acciones antes de
explorar el árbol:

```
Para nodo MAX (jugador propio):
  f(acción) ≈ -heurística(estado_resultante)   → ordenar de mayor a menor
  
Para nodo MIN (oponente):
  f(acción) ≈ +heurística(estado_resultante)   → ordenar de menor a mayor
```

El beneficio es **práctico**: al explorar primero las ramas más prometedoras,
la poda alfa-beta encuentra cotas mejores más rápido y poda más ramas.

**Importante**: Esto NO convierte Minimax en A*. Son algoritmos diferentes:
- A\* es para búsqueda de un agente en grafo con costo acumulado
- Minimax es para juego adversarial con horizontes fijos

---

## C. Función Heurística Compuesta

### Justificación de cada factor:

| Factor | Justificación |
|--------|---------------|
| f_pokemon_vivos | Indicador directo del avance en la batalla |
| f_ventaja_tipo | El sistema de tipos es la mecánica central de Pokémon |
| f_velocidad | Determina quién ataca primero → ventaja táctica crítica |
| f_hp_restante | Proxy de la "vida" del equipo |
| f_riesgo_morir | Evaluación prospectiva del turno siguiente |

### Normalización:

Todos los factores se normalizan a [-1, 1] o [-1, 0] para que los pesos W
sean comparables entre sí. Sin normalización, un factor con rango [-100, 100]
dominaría sobre uno en [-1, 1] independientemente de su peso W.

---

## D. Justificación del Algoritmo Genético

### Espacio de búsqueda:

Los pesos W = [W1, W2, W3, W4, W5] ∈ ℝ⁵ forman un espacio continuo
de dimensión 5. La función de fitness f(W) es:
- **No diferenciable**: no se puede calcular el gradiente analíticamente
- **Estocástica**: el resultado de una batalla varía con el RNG
- **Cara de evaluar**: cada evaluación requiere N batallas completas

### Por qué AG es apropiado:

- **Sin gradiente necesario**: los AGs son métodos de caja negra
- **Exploración global**: evitan óptimos locales mediante recombinación
- **Robustez al ruido**: el promedio de N batallas reduce la varianza
- **Paralelizable**: cada individuo es independiente (embarrasingly parallel)

### Convergencia esperada:

```
Generación 0:  fitness ~30–45  (pesos aleatorios)
Generación 10: fitness ~55–65  (selección elimina malos candidatos)
Generación 30: fitness ~70–80  (refinamiento fino)
Generación 50: fitness ~80–90  (convergencia)
```

---

## E. Plantillas para el Artículo Científico

### Sección: Metodología — Algoritmo Minimax

> Se implementó un agente basado en el algoritmo Minimax con poda alfa-beta
> (Knuth & Moore, 1975) para el problema de decisión en combates por turnos.
> Dado que los combates Pokémon constituyen un juego de suma cero con dos
> adversarios e información completa, Minimax garantiza la selección de la
> acción óptima bajo el supuesto de que el oponente también juega óptimamente.
> Para mitigar la explosión combinatoria (O(b^2d) sin poda), se implementaron
> tres optimizaciones: (1) poda alfa-beta, que reduce la complejidad a
> O(b^d) en el mejor caso; (2) ordenamiento heurístico de acciones inspirado
> en la función de evaluación de A*; y (3) tabla de transposición para
> memoización de estados repetidos.

### Sección: Metodología — Función Heurística

> La función heurística h(s, i) evalúa el estado s desde la perspectiva
> del jugador i como combinación lineal ponderada de cinco factores
> normalizados en [-1, 1]: ventaja en Pokémon vivos (f₁), ventaja de
> tipo elemental (f₂), ventaja de velocidad (f₃), HP total relativo (f₄),
> y riesgo de debilitamiento inminente (f₅). Formalmente:
>
> h(s,i) = W₁·f₁ + W₂·f₂ + W₃·f₃ + W₄·f₄ + W₅·f₅
>
> donde W = [W₁,...,W₅] es el vector de pesos optimizable.
> Para estados terminales, h = ±1000 garantiza que el algoritmo
> prefiera siempre ganar sobre cualquier evaluación heurística.

### Sección: Metodología — Optimización Evolutiva

> Para optimizar el vector de pesos W se empleó un Algoritmo Genético
> estándar con los siguientes operadores: selección por torneo (k=4),
> cruce de un punto y cruce uniforme (probabilidad 0.8), mutación
> gaussiana (σ=0.1, tasa=0.2), y elitismo del 15% de la población.
> La función de fitness evalúa cada individuo mediante 30 batallas
> contra el agente HeuristicAgent de referencia, calculando:
>
> fitness = win_rate × 0.7 + margin_score × 0.3
>
> donde win_rate es el porcentaje de victorias y margin_score es la
> diferencia promedio de Pokémon vivos al finalizar la batalla.
> La estocásticidad inherente de las batallas justifica el uso de un
> método libre de gradiente como los Algoritmos Genéticos.

# Análisis de Complejidad Temporal — Agente Minimax

## 1. Minimax Puro (sin poda)

En el contexto de PokeFISI, un "nivel" del árbol representa la elección simultánea
de ambos jugadores (mi acción × acción del oponente).

- **Branching factor efectivo**: b_mine × b_opp ≈ b²  
  Con b ≈ 5–8 acciones por jugador → branching factor ≈ 25–64 por nivel
- **Profundidad**: d = número de turnos anticipados

| Complejidad | Fórmula |
|-------------|---------|
| Temporal    | O(b^(2d))  → O((b_mine × b_opp)^d) |
| Espacial    | O(b × 2d) por la pila de recursión |

**Ejemplo (b=6, d=2):**  
Sin poda: 6² × 6² = 1296 estados evaluados por turno.

---

## 2. Minimax con Poda Alfa-Beta

La poda alfa-beta elimina subárboles que no pueden afectar la decisión óptima.

| Caso | Complejidad | Descripción |
|------|-------------|-------------|
| Mejor caso (ordenamiento perfecto) | O(b^d) | Solo la mitad del árbol se explora |
| Caso promedio (buen ordenamiento)  | O(b^(3d/4)) | Con ordenamiento heurístico |
| Peor caso (sin ordenamiento)       | O(b^(2d)) | Sin ganancia sobre Minimax puro |

**Ejemplo práctico (b=6, d=2 turnos → 4 plies):**

```
Sin poda:         6^4 = 1296  nodos
Con poda óptima:  6^2 =   36  nodos (97.2% reducción)
Caso promedio:    ~200–400    nodos
```

---

## 3. Impacto de Optimizaciones

### A) Ordenamiento Heurístico (A*-inspired Move Ordering)

El ordenamiento previo de acciones por valor heurístico maximiza los cortes alfa-beta:

- **Sin ordenamiento**: la poda es mínima (peor caso O(b^2d))
- **Con ordenamiento**: se exploran primero las ramas más prometedoras → más cortes tempranos
- **Ganancia observada**: 60–80% reducción de nodos evaluados

### B) Tabla de Transposición

En batallas Pokémon, los switches generan estados repetidos (mismo HP, mismo activo).
La tabla de transposición evita recomputar estados ya vistos:

- Reducción típica: 10–30% de nodos en batallas con switches frecuentes
- Costo: O(S) en memoria, donde S = estados únicos visitados

### C) Top-K Acciones (Control de Branching Factor)

Limitar a K mejores acciones reduce el branching factor efectivo:

| K | Nodos (d=2) | Tiempo estimado |
|---|-------------|-----------------|
| 4 | 4² × 4² = 256 | ~0.05s |
| 6 | 6² × 6² = 1296 | ~0.2s |
| 8 | 8² × 8² = 4096 | ~0.8s |

---

## 4. Trade-offs Prácticos por Profundidad

| Profundidad | Nodos (~) | Tiempo (~) | Calidad de decisión |
|-------------|-----------|------------|---------------------|
| d=1 (greedy) | 25–50 | <0.01s | Mínima (un turno) |
| d=2 (táctico) | 100–500 | 0.05–0.5s | Buena (dos turnos) |
| d=3 (estratégico) | 500–5000 | 0.5–10s | Excelente |
| d=4+ | >10000 | >30s | Impracticable sin restricciones |

**Configuración recomendada para el frontend**: d=2, top_k=6

---

## 5. Comparación Visual (ASCII)

```
Nodos evaluados vs Profundidad
                           
  Nodos |                                          ■ Sin poda
  5000  |                              ■           ▲ Con poda alpha-beta (avg)
        |                                          ● Con poda (mejor caso)
  2000  |                  ■
        |        ■                     ▲
  1000  |                              
   500  |  ■              ▲            ●
   200  |        ▲
   100  |  ▲              ●
    50  |  ●
        +--+----------------+----------+--> d
        d=1                d=2        d=3

Eficiencia de poda (% nodos podados) vs d
  %    |
   80  |         ████████████████████████████
   60  |  ██████
   40  |
       +--+------+------+--> profundidad
       d=1      d=2    d=3
```

*La poda mejora con profundidades mayores porque hay más ramas para cortar.*

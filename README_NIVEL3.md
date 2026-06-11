# PokeFISI — Nivel 3: Minimax + Algoritmo Genético

## Nuevos componentes

| Archivo | Descripción |
|---------|-------------|
| `backend/data/types.py` | Tabla de efectividad elemental desacoplada |
| `backend/battle/simulator.py` | Simulación sin efectos secundarios para Minimax |
| `backend/agents/heuristics.py` | 5 funciones heurísticas normalizadas |
| `backend/agents/minimax_agent.py` | Agente Minimax + poda alfa-beta |
| `backend/experiments/fitness.py` | Evaluador de fitness para el AG |
| `backend/experiments/evolution.py` | Algoritmo Genético completo |
| `backend/config.py` | Gestión de pesos y niveles de dificultad |
| `docs/complexity_analysis.md` | Análisis de complejidad temporal |
| `docs/algorithms_justification.md` | Justificación académica con plantillas |
| `docs/difficulty_system.md` | Documentación del sistema de dificultad |

## Cambios en archivos existentes

| Archivo | Cambio |
|---------|--------|
| `backend/battle/models.py` | + campo `pokemon_type`, + métodos `clone()` |
| `backend/battle/factory.py` | + pasa `pokemon_type` al construir Pokémon |
| `backend/battle/damage.py` | + multiplicador de tipo en fórmula de daño |
| `backend/battle/state.py` | + método `clone()` en `BattleState` |
| `backend/session.py` | + parámetro `difficulty` para selección de agente |
| `backend/server.py` | + acepta `difficulty` en `/api/battle/start` |
| `backend/main.py` | + soporte para agentes `minimax` y `minimax-optimized` |
| `backend/agents/__init__.py` | + exporta `MinimaxAgent` |
| `backend/experiments/simulate.py` | + soporte para `minimax` y `minimax-optimized` |
| `frontend/web/index.html` | + selector de dificultad |
| `frontend/web/app.js` | + pasa `difficulty` al servidor, muestra en pill |
| `frontend/web/styles.css` | + estilo para `.difficulty-hint` |

## Inicio rápido

### Servidor con dificultad seleccionable (web)
```bash
python -m backend.main --mode serve
# Abrir http://localhost:8000
# Seleccionar dificultad en el menú y presionar "Human vs IA"
```

### Experimento CLI: Minimax vs Heuristic
```bash
python -m backend.main --mode battle --agent1 minimax --agent2 heuristic
python scripts/run_minimax_experiment.py --battles 30 --depth 2
```

### Experimento batch comparativo
```bash
python -m backend.main --mode experiment --agent1 minimax --agent2 random --battles 20
```

### Exportar métricas por profundidad
```bash
python scripts/export_metrics.py --depths 1 2 --battles 20
# Genera: results/minimax_metrics_depth1.csv, results/depth_comparison.csv
```

### Entrenar pesos con Algoritmo Genético (offline)
```bash
python scripts/run_evolution.py --generations 50 --battles 30 --depth 4 --top-k 6
# Genera: results/best_weights.json, results/evolution_history.csv
```

### Validar los 4 niveles de dificultad
```bash
python scripts/test_difficulty_levels.py --battles 20
```

## Arquitectura de decisión (Minimax depth=2)

```
Estado actual
    │
    ├─ Mis acciones (top-K, ordenadas heurísticamente)
    │      │
    │      ├─ Respuestas del rival (top-K, minimizando)
    │      │      │
    │      │      ├─ Simular turno → Estado A
    │      │      │      └─ Mis acciones (profundidad 1)
    │      │      │              └─ Respuestas (minimizando)
    │      │      │                     └─ Heurística(estado) ← hoja
    │      │      └─ ...
    │      └─ min(valores) = valor pesimista de mi acción
    └─ max(valores) = mejor acción → ELEGIR
```

## Fórmula de daño extendida con tipos

```
Damage = Max(1, Int(Round(
    (Attack / Max(1, Defense)) × BasePower × TypeModifier − Speed × K
)))

TypeModifier = ∏ chart[move_type, def_type]  para cada tipo del defensor
```

## Función heurística compuesta

```python
h(s, i) = W1·f_pokemon_vivos(s,i)   # [-1,  1]
         + W2·f_ventaja_tipo(s,i)    # [-1,  1]
         + W3·f_velocidad(s,i)       # (-1,  1)
         + W4·f_hp_restante(s,i)     # [-1,  1]
         + W5·f_riesgo_morir(s,i)    # [-1,  0]

# Pesos manuales (nivel hard):    [0.4, 0.2, 0.1, 0.2, 0.1]
# Pesos optimizados (nivel sobrv): cargados de results/best_weights.json
```

## Fitness del Algoritmo Genético

```
fitness(W) = win_rate × 0.7 + margin_score × 0.3

win_rate     = victorias / n_batallas × 100   ∈ [0, 100]
margin_score = Σ(Pokémon_vivos_propio - Pokémon_vivos_rival) / n_batallas / team_size × 100
```

# Sistema de Dificultad Multinivel — PokeFISI

## Niveles de IA disponibles

| Nivel | Nombre | Agente | Depth | Win rate esperado (usuario) |
|-------|--------|--------|-------|---------------------------|
| 1 | Entrenamiento (Fácil) | RandomAgent | - | 85–95% |
| 2 | Competitivo (Medio) | HeuristicAgent | 1 | 60–70% |
| 3 | Experto (Difícil) | MinimaxAgent | 2 | 35–45% |
| 4 | Maestro (Sobrevilla) | MinimaxAgent + GA | 2 | 10–25% |

## Descripción de cada nivel

### Nivel 1 — Entrenamiento (Fácil)
- **Agente**: `RandomAgent`
- **Comportamiento**: Selecciona uniformemente al azar entre acciones legales.
- **Propósito**: Aprender las mecánicas sin presión. Siempre elige sin estrategia.
- **Parámetro API**: `"difficulty": "easy"`

### Nivel 2 — Competitivo (Medio)
- **Agente**: `HeuristicAgent`
- **Comportamiento**: Evaluación greedy depth-1. Maximiza `HP_propio - HP_rival`.
  Estima el daño esperado de cada movimiento y elige el que más reduce HP rival.
- **Propósito**: Oponente con estrategia simple pero efectiva para principiantes.
- **Parámetro API**: `"difficulty": "medium"` (valor por defecto)

### Nivel 3 — Experto (Difícil)
- **Agente**: `MinimaxAgent` con pesos manuales
- **Comportamiento**: Búsqueda adversarial a profundidad 2 con poda alfa-beta.
  Anticipa 2 turnos completos y usa heurística compuesta de 5 factores.
- **Pesos**: `MANUAL_WEIGHTS = [0.4, 0.2, 0.1, 0.2, 0.1]` (ajuste manual).
- **Propósito**: Oponente táctico que planifica. Difícil de vencer.
- **Parámetro API**: `"difficulty": "hard"`

### Nivel 4 — Maestro (Sobrevilla)
- **Agente**: `MinimaxAgent` con pesos optimizados por Algoritmo Genético
- **Comportamiento**: Igual que Nivel 3 pero con pesos encontrados por el GA.
  Si no se han entrenado los pesos, hace fallback a los pesos manuales (Nivel 3).
- **Propósito**: Máximo desafío. Named en honor al profesor Marco Sobrevilla.
- **Parámetro API**: `"difficulty": "sobrevilla"`

## Flujo para activar el Nivel 4 (Maestro)

```bash
# 1. Entrenar offline (una vez, puede tomar 30–120 minutos)
python scripts/run_evolution.py --generations 50 --battles 30

# 2. Iniciar el servidor (carga automáticamente los pesos optimizados)
python -m backend.main --mode serve

# El servidor imprimirá:
# ✓ IA usando pesos optimizados (Fitness: 89.4)
```

## API — Endpoint /api/battle/start

```json
POST /api/battle/start
{
  "mode": "human-vs-ai",
  "teamSize": 3,
  "difficulty": "sobrevilla"
}
```

### Valores válidos de difficulty:
- `"easy"`, `"medium"`, `"hard"`, `"sobrevilla"`
- Default: `"medium"` (retrocompatible)

## Retrocompatibilidad

Si el frontend no envía `difficulty`, el backend asume `"medium"`.
Versiones antiguas del frontend siguen funcionando sin cambios.

## Objetivo académico del sistema

El sistema de dificultad permite:
1. **Comparar empíricamente** los 4 tipos de agentes
2. **Validar la progresión**: Random < Heuristic < Minimax Manual ≤ Minimax GA
3. **Recolectar datos** de win rate de usuarios humanos vs cada nivel
4. **Demostrar** que el algoritmo genético mejora efectivamente la IA

"""Configuración central de agentes y gestión de pesos optimizados.

Flujo:
  1. Entrenamiento offline: run_evolution.py genera results/best_weights.json
  2. Al iniciar el servidor: load_agent_weights() carga los pesos automáticamente
  3. El MinimaxAgent de nivel "sobrevilla" usa los pesos optimizados

Niveles de dificultad:
  easy      → RandomAgent
  medium    → HeuristicAgent
  hard      → MinimaxAgent con MANUAL_WEIGHTS
  sobrevilla → MinimaxAgent con pesos optimizados (fallback: MANUAL_WEIGHTS)
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

# Ruta al archivo de pesos optimizados por el algoritmo genético
_RESULTS_DIR = Path(__file__).resolve().parent.parent / "results"
_BEST_WEIGHTS_FILE = _RESULTS_DIR / "best_weights.json"

# Pesos ajustados manualmente (nivel "hard" y fallback de "sobrevilla")
# Orden: [f_pokemon_vivos, f_ventaja_tipo, f_velocidad, f_hp_restante, f_riesgo_morir]
# Cambio respecto a v1 [0.4, 0.2, 0.1, 0.2, 0.1]:
#   - f_ventaja_tipo 0.2→0.35: el tipo domina la táctica; penaliza matchups 4× más fuerte
#   - f_riesgo_morir 0.1→0.15: penaliza más los estados donde el activo muere en un turno
#   - f_pokemon_vivos 0.4→0.25: menos peso a conteo bruto (tipo importa más que número)
#   - f_velocidad 0.1→0.05: la velocidad ya influye en la fórmula de daño; reducida aquí
MANUAL_WEIGHTS: list[float] = [0.25, 0.35, 0.05, 0.2, 0.15]

# Profundidad de búsqueda Minimax
# Profundidad 3 permite ver 3 turnos completos adelante (vs 2 anteriores).
# Con alpha-beta y top_k=6 el costo práctico es ~1000-5000 nodos vs ~300 de depth=2.
MINIMAX_DEPTH: int = 3

# Rangos válidos para validación de pesos
_WEIGHT_MIN = 0.0
_WEIGHT_MAX = 10.0
_WEIGHT_COUNT = 5


def load_agent_weights(use_optimized: bool = True) -> list[float]:
    """Carga pesos del MinimaxAgent.

    Si use_optimized=True y existe results/best_weights.json con datos válidos,
    retorna los pesos optimizados. En caso contrario retorna MANUAL_WEIGHTS.

    Returns:
        Lista de 5 floats con los pesos heurísticos.
    """
    if not use_optimized:
        logger.info("→ IA usando pesos manuales (use_optimized=False)")
        return list(MANUAL_WEIGHTS)

    if not _BEST_WEIGHTS_FILE.exists():
        logger.info("→ IA usando pesos manuales (archivo de pesos optimizados no encontrado)")
        return list(MANUAL_WEIGHTS)

    try:
        data = json.loads(_BEST_WEIGHTS_FILE.read_text(encoding="utf-8"))
        weights = data.get("weights")
        if not _validate_weights(weights):
            logger.warning("! Pesos en best_weights.json inválidos — usando pesos manuales")
            return list(MANUAL_WEIGHTS)

        fitness = data.get("fitness", "?")
        gen = data.get("generation", "?")
        logger.info(f"✓ IA usando pesos optimizados (generación {gen}, fitness {fitness})")
        print(f"✓ IA usando pesos optimizados (Fitness: {fitness})")
        return [float(w) for w in weights]

    except Exception as exc:
        logger.warning(f"! Error al cargar pesos optimizados: {exc} — usando pesos manuales")
        return list(MANUAL_WEIGHTS)


def save_optimized_weights(
    weights: list[float],
    fitness: float,
    generation: int,
    win_rate: float = 0.0,
    training_config: dict | None = None,
) -> None:
    """Guarda los pesos óptimos encontrados por el algoritmo genético."""
    _RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "weights": [round(w, 6) for w in weights],
        "fitness": round(fitness, 4),
        "generation": generation,
        "win_rate": round(win_rate, 2),
        "timestamp": datetime.now().isoformat(),
        "training_config": training_config or {},
    }
    _BEST_WEIGHTS_FILE.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    logger.info(f"✓ Pesos optimizados guardados en {_BEST_WEIGHTS_FILE}")
    print(f"✓ Pesos guardados: {weights}")


def _validate_weights(weights: object) -> bool:
    if not isinstance(weights, list):
        return False
    if len(weights) != _WEIGHT_COUNT:
        return False
    return all(
        isinstance(w, (int, float)) and _WEIGHT_MIN <= w <= _WEIGHT_MAX
        for w in weights
    )


def build_agent(difficulty: str, rng=None):
    """Construye el agente IA correcto según el nivel de dificultad.

    Args:
        difficulty: "easy" | "medium" | "hard" | "sobrevilla"
        rng: random.Random compartido para el agente (opcional)

    Returns:
        Instancia de BaseAgent lista para usar.
    """
    from backend.agents.heuristic_agent import HeuristicAgent
    from backend.agents.minimax_agent import MinimaxAgent
    from backend.agents.random_agent import RandomAgent

    if difficulty == "easy":
        return RandomAgent(name="IA (Fácil)", rng=rng)

    if difficulty == "medium":
        return HeuristicAgent(name="IA (Medio)")

    if difficulty == "hard":
        return MinimaxAgent(
            name="IA (Difícil)",
            depth=MINIMAX_DEPTH,
            weights=list(MANUAL_WEIGHTS),
        )

    if difficulty == "sobrevilla":
        optimized = load_agent_weights(use_optimized=True)
        if optimized == MANUAL_WEIGHTS:
            logger.info("→ Nivel Sobrevilla usando pesos manuales (sin entrenamiento previo)")
        return MinimaxAgent(
            name="IA Sobrevilla",
            depth=MINIMAX_DEPTH,
            weights=optimized,
        )

    raise ValueError(f"Dificultad desconocida: {difficulty!r}. Valores válidos: easy, medium, hard, sobrevilla")


VALID_DIFFICULTIES = {"easy", "medium", "hard", "sobrevilla"}

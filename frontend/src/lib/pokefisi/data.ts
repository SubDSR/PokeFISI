import type { ApiPokemon, BackendActivePokemon, BackendPartySlot } from "./api";

// ── Tipos base ────────────────────────────────────────────────────────────────

export type PokeType =
  | "water" | "fire" | "grass" | "electric" | "normal" | "psychic"
  | "ghost" | "dragon" | "fighting" | "dark" | "ice" | "flying"
  | "poison" | "ground" | "rock" | "bug" | "steel" | "fairy";

export type Move = {
  name: string;
  type: PokeType;
  pp: number;
  ppMax: number;
  power: number;
  desc: string;
};

export type Pokemon = {
  id: string;
  name: string;
  level: number;
  types: PokeType[];
  sprite: string;       // front — enemigo
  spriteBack: string;   // back  — jugador
  icon: string;         // miniatura para slots de equipo
  hp: number;
  hpMax: number;
  moves: Move[];
  fainted?: boolean;
};

// ── Dificultad ────────────────────────────────────────────────────────────────

export type Difficulty = "facil" | "medio" | "dificil" | "maestro-sobrevilla";

export const DIFFICULTY_TO_API: Record<Difficulty, string> = {
  facil: "easy",
  medio: "medium",
  dificil: "hard",
  "maestro-sobrevilla": "sobrevilla",
};

export const DIFFICULTY_LABEL: Record<Difficulty, string> = {
  facil: "Fácil",
  medio: "Medio",
  dificil: "Difícil",
  "maestro-sobrevilla": "Maestro-Sobrevilla",
};

export const DIFFICULTY_DESC: Record<Difficulty, string> = {
  facil: "La IA juega con decisiones básicas.",
  medio: "La IA prioriza ventajas simples.",
  dificil: "La IA calcula mejor daño, cambios y riesgo.",
  "maestro-sobrevilla": "La IA juega de forma más estratégica y exigente.",
};

// ── Tipos de pokémon ──────────────────────────────────────────────────────────

export const TYPE_LABEL: Record<PokeType, string> = {
  water: "Agua", fire: "Fuego", grass: "Planta", electric: "Eléctrico",
  normal: "Normal", psychic: "Psíquico", ghost: "Fantasma", dragon: "Dragón",
  fighting: "Lucha", dark: "Siniestro", ice: "Hielo", flying: "Volador",
  poison: "Veneno", ground: "Tierra", rock: "Roca", bug: "Bicho",
  steel: "Acero", fairy: "Hada",
};

// ── Mapeadores DTO → modelo visual ───────────────────────────────────────────

/** Convierte un ApiPokemon del GET /api/pokemon al modelo visual. */
export function mapApiPokemon(dto: ApiPokemon): Pokemon {
  return {
    id: dto.id,
    name: dto.name,
    level: dto.level,
    types: dto.types as PokeType[],
    sprite: dto.spriteFrontUrl,
    spriteBack: dto.spriteBackUrl,
    icon: dto.spriteFrontUrl,
    hp: dto.hp,
    hpMax: dto.hp,
    moves: [],  // los movimientos reales llegan en cada frame de batalla
    fainted: false,
  };
}

/**
 * Convierte el pokemon activo de un frame de backend al modelo visual.
 * Usa el pool para obtener tipos e icono (el backend no los incluye en el frame).
 */
export function mapBackendActivePokemon(
  active: BackendActivePokemon,
  perspective: "player" | "enemy",
  pool: Pokemon[],
): Pokemon {
  const found = pool.find((p) => p.name === active.name);
  return {
    id: found?.id ?? active.name.toLowerCase().replace(/\s/g, "-"),
    name: active.name,
    level: active.level,
    types: found?.types ?? [],
    sprite: perspective === "enemy" ? active.spriteUrl : (found?.sprite ?? active.spriteUrl),
    spriteBack: perspective === "player" ? active.spriteUrl : (found?.spriteBack ?? active.spriteUrl),
    icon: found?.sprite ?? active.spriteUrl,
    hp: active.currentHp,
    hpMax: active.maxHp,
    moves: active.moves.map((m) => ({
      name: m.name,
      type: m.type as PokeType,
      pp: m.pp,
      ppMax: m.maxPp,
      power: m.power,
      desc: `Tipo: ${m.type} · Poder: ${m.power > 0 ? m.power : "—"}`,
    })),
    fainted: active.fainted,
  };
}

/**
 * Convierte un slot de equipo de un frame de backend al modelo visual.
 * Usa el pool para obtener stats completos; hp se aproxima desde hpRatio.
 */
export function mapBackendPartySlot(slot: BackendPartySlot, pool: Pokemon[]): Pokemon {
  const found = pool.find((p) => p.name === slot.name);
  const hpMax = found?.hpMax ?? 100;
  return {
    id: found?.id ?? slot.name.toLowerCase().replace(/\s/g, "-"),
    name: slot.name,
    level: found?.level ?? 50,
    types: found?.types ?? [],
    sprite: found?.sprite ?? "",
    spriteBack: found?.spriteBack ?? "",
    icon: found?.sprite ?? "",
    hp: Math.max(0, Math.round(slot.hpRatio * hpMax)),
    hpMax,
    moves: [],
    fainted: slot.fainted,
  };
}

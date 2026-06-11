import type { PokeType } from "./data";

const BG_BASE = "https://play.pokemonshowdown.com/sprites/gen6bgs/";

export const SHOWDOWN_BATTLE_BACKGROUNDS = [
  `${BG_BASE}bg-meadow.jpg`,
  `${BG_BASE}bg-city.jpg`,
  `${BG_BASE}bg-forest.jpg`,
  `${BG_BASE}bg-beach.jpg`,
  `${BG_BASE}bg-desert.jpg`,
  `${BG_BASE}bg-icecave.jpg`,
  `${BG_BASE}bg-earthycave.jpg`,
  `${BG_BASE}bg-deepsea.jpg`,
] as const;

const TYPE_TO_BG: Partial<Record<PokeType, string>> = {
  grass:    `${BG_BASE}bg-forest.jpg`,
  bug:      `${BG_BASE}bg-forest.jpg`,
  poison:   `${BG_BASE}bg-forest.jpg`,
  water:    `${BG_BASE}bg-beach.jpg`,
  dragon:   `${BG_BASE}bg-deepsea.jpg`,
  fire:     `${BG_BASE}bg-desert.jpg`,
  ground:   `${BG_BASE}bg-earthycave.jpg`,
  rock:     `${BG_BASE}bg-earthycave.jpg`,
  ice:      `${BG_BASE}bg-icecave.jpg`,
  electric: `${BG_BASE}bg-city.jpg`,
  normal:   `${BG_BASE}bg-city.jpg`,
  fighting: `${BG_BASE}bg-city.jpg`,
  psychic:  `${BG_BASE}bg-city.jpg`,
  steel:    `${BG_BASE}bg-city.jpg`,
  ghost:    `${BG_BASE}bg-earthycave.jpg`,
  dark:     `${BG_BASE}bg-earthycave.jpg`,
  flying:   `${BG_BASE}bg-meadow.jpg`,
  fairy:    `${BG_BASE}bg-meadow.jpg`,
};

/** Devuelve la URL del fondo Gen 6 correspondiente al tipo primario del Pokemon. */
export function pickBattleBackground(primaryType?: PokeType): string {
  return (primaryType && TYPE_TO_BG[primaryType]) ?? `${BG_BASE}bg-meadow.jpg`;
}

/* ── Sprites de tipo ─────────────────────────────────────────────────────── */

const TYPE_SPRITE_BASE = "https://play.pokemonshowdown.com/sprites/types/";

export const TYPE_SPRITE_URL: Record<PokeType, string> = {
  water:    `${TYPE_SPRITE_BASE}Water.png`,
  fire:     `${TYPE_SPRITE_BASE}Fire.png`,
  grass:    `${TYPE_SPRITE_BASE}Grass.png`,
  electric: `${TYPE_SPRITE_BASE}Electric.png`,
  normal:   `${TYPE_SPRITE_BASE}Normal.png`,
  psychic:  `${TYPE_SPRITE_BASE}Psychic.png`,
  ghost:    `${TYPE_SPRITE_BASE}Ghost.png`,
  dragon:   `${TYPE_SPRITE_BASE}Dragon.png`,
  fighting: `${TYPE_SPRITE_BASE}Fighting.png`,
  dark:     `${TYPE_SPRITE_BASE}Dark.png`,
  ice:      `${TYPE_SPRITE_BASE}Ice.png`,
  flying:   `${TYPE_SPRITE_BASE}Flying.png`,
  poison:   `${TYPE_SPRITE_BASE}Poison.png`,
  ground:   `${TYPE_SPRITE_BASE}Ground.png`,
  rock:     `${TYPE_SPRITE_BASE}Rock.png`,
  bug:      `${TYPE_SPRITE_BASE}Bug.png`,
  steel:    `${TYPE_SPRITE_BASE}Steel.png`,
  fairy:    `${TYPE_SPRITE_BASE}Fairy.png`,
};

/* ── Categoría de movimiento ──────────────────────────────────────────────── */

export type MoveCategory = "Physical" | "Special" | "Status";

const CAT_BASE = "https://play.pokemonshowdown.com/sprites/categories/";
export const MOVE_CATEGORY_URL: Record<MoveCategory, string> = {
  Physical: `${CAT_BASE}Physical.png`,
  Special:  `${CAT_BASE}Special.png`,
  Status:   `${CAT_BASE}Status.png`,
};

// En Gen 1-3 la categoría depende del tipo, no del movimiento individual.
const PHYSICAL_TYPES = new Set<PokeType>([
  "normal", "fighting", "flying", "ground", "rock", "bug", "ghost", "poison", "steel",
]);

export function getMoveCategory(type: PokeType, power: number): MoveCategory {
  if (power === 0) return "Status";
  return PHYSICAL_TYPES.has(type) ? "Physical" : "Special";
}

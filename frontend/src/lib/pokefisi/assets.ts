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

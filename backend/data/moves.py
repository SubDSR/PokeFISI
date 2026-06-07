"""Catálogo de movimientos usados en el proyecto Pokefisi.

Fuente oficial: https://play.pokemonshowdown.com/data/
Todos los valores de base_power y accuracy han sido verificados contra
el dataset oficial de Pokémon Showdown Gen 3.

Correcciones respecto a la versión anterior (marcadas con # FIX):
  headbutt    60 → 70   (oficial Gen 3)
  slam        75 → 80   (oficial Gen 3)
  solarbeam   90 → 120  (oficial Gen 3; se mantiene 1-turno por simplicidad)
  absorb      40 → 20   (oficial Gen 3)
  magicalleaf 70 → 60   (oficial Gen 3)
  acid        45 → 40   (oficial Gen 3)
  sludgebomb  85 → 90   (oficial Gen 3)
  aquatail    80 → 90   (oficial Gen 3)
  hydropump   95 → 110  (oficial Gen 3)
  icebeam     85 → 90   (oficial Gen 3)
  flamethrower 85 → 90  (oficial Gen 3)
  heatwave    90 → 95   (oficial Gen 3)
  thunderbolt 85 → 90   (oficial Gen 3)
  volttackle  95 → 120  (oficial Gen 3; recoil ignorado por simplicidad)
  flashcannon 85 → 80   (oficial Gen 3)
  airslash    80 → 75   (oficial Gen 3)
  hurricane   95 → 110  (oficial Gen 3)
  earthquake  95 → 100  (oficial Gen 3)
  dig         75 → 80   (oficial Gen 3)
  karatechop  55 → 50   (oficial Gen 3)
  submission  85 → 80   (oficial Gen 3; recoil ignorado por simplicidad)
  confusion   55 → 50   (oficial Gen 3)
  psybeam     70 → 65   (oficial Gen 3)
  lowkick: se mantiene power=60 como proxy fijo (peso-variable no implementado)
"""

from backend.data.models import MoveData


MOVEDEX: dict[str, MoveData] = {
    # ── NORMAL ─────────────────────────────────────────────────────────
    "scratch":      MoveData("scratch",      "Scratch",        40,  1.0,  "normal",   "Zarpazo rapido de corto alcance.",                35),
    "tackle":       MoveData("tackle",       "Tackle",         40,  1.0,  "normal",   "Golpe directo y confiable.",                       35),
    "headbutt":     MoveData("headbutt",     "Headbutt",       70,  1.0,  "normal",   "Embestida de contacto.",                           15),  # FIX 60→70
    "quickattack":  MoveData("quickattack",  "Quick Attack",   40,  1.0,  "normal",   "Ataque veloz y ligero.",                           30),
    "slash":        MoveData("slash",        "Slash",          70,  1.0,  "normal",   "Corte agresivo con alta critica.",                 20),
    "swift":        MoveData("swift",        "Swift",          60,  1.0,  "normal",   "Estrellas rapidas que no fallan.",                 20),
    "slam":         MoveData("slam",         "Slam",           80,  0.75, "normal",   "Golpe pesado con todo el cuerpo.",                 20),  # FIX 75→80

    # ── GRASS ──────────────────────────────────────────────────────────
    "vinewhip":     MoveData("vinewhip",     "Vine Whip",      45,  1.0,  "grass",    "Latigazo de enredaderas.",                         25),
    "razorleaf":    MoveData("razorleaf",    "Razor Leaf",     55,  0.95, "grass",    "Hojas filosas lanzadas al rival.",                 25),
    "seedbomb":     MoveData("seedbomb",     "Seed Bomb",      80,  1.0,  "grass",    "Impacto fuerte de semillas.",                      15),
    "solarbeam":    MoveData("solarbeam",    "Solar Beam",    120,  1.0,  "grass",    "Rayo concentrado de energia solar.",               10),  # FIX 90→120
    "absorb":       MoveData("absorb",       "Absorb",         20,  1.0,  "grass",    "Drena HP del rival (recupera mitad del dano).",    25),  # FIX 40→20
    "magicalleaf":  MoveData("magicalleaf",  "Magical Leaf",   60,  1.0,  "grass",    "Hojas luminosas que no fallan.",                   20),  # FIX 70→60

    # ── POISON ─────────────────────────────────────────────────────────
    "acid":         MoveData("acid",         "Acid",           40,  1.0,  "poison",   "Rocio corrosivo de corto alcance.",                30),  # FIX 45→40
    "sludgebomb":   MoveData("sludgebomb",   "Sludge Bomb",    90,  1.0,  "poison",   "Bomba de lodo toxico.",                            10),  # FIX 85→90

    # ── WATER ──────────────────────────────────────────────────────────
    "watergun":     MoveData("watergun",     "Water Gun",      40,  1.0,  "water",    "Chorro de agua a presion.",                        25),
    "bubblebeam":   MoveData("bubblebeam",   "Bubble Beam",    65,  1.0,  "water",    "Rafaga de burbujas.",                              20),
    "aquatail":     MoveData("aquatail",     "Aqua Tail",      90,  0.9,  "water",    "Coletazo reforzado con agua.",                     10),  # FIX 80→90
    "hydropump":    MoveData("hydropump",    "Hydro Pump",    110,  0.8,  "water",    "Gran descarga de agua a maxima potencia.",          5),  # FIX 95→110
    "icebeam":      MoveData("icebeam",      "Ice Beam",       90,  1.0,  "ice",      "Haz helado de largo alcance.",                     10),  # FIX 85→90

    # ── GROUND ─────────────────────────────────────────────────────────
    "mudshot":      MoveData("mudshot",      "Mud Shot",       55,  0.95, "ground",   "Disparo de barro comprimido.",                     15),
    "bulldoze":     MoveData("bulldoze",     "Bulldoze",       60,  1.0,  "ground",   "Acometida terrestre.",                             20),
    "earthquake":   MoveData("earthquake",   "Earthquake",    100,  1.0,  "ground",   "Sacudida masiva del terreno.",                     10),  # FIX 95→100
    "dig":          MoveData("dig",          "Dig",            80,  1.0,  "ground",   "Ataque subterraneo directo.",                      10),  # FIX 75→80

    # ── FIRE ───────────────────────────────────────────────────────────
    "ember":        MoveData("ember",        "Ember",          40,  1.0,  "fire",     "Pequena llamarada.",                               25),
    "firefang":     MoveData("firefang",     "Fire Fang",      65,  0.95, "fire",     "Mordida envuelta en fuego.",                       15),
    "flamethrower": MoveData("flamethrower", "Flamethrower",   90,  1.0,  "fire",     "Lanzallamas constante.",                           15),  # FIX 85→90
    "heatwave":     MoveData("heatwave",     "Heat Wave",      95,  0.9,  "fire",     "Ola de calor intensa.",                            10),  # FIX 90→95

    # ── ELECTRIC ───────────────────────────────────────────────────────
    "thundershock": MoveData("thundershock", "Thunder Shock",  40,  1.0,  "electric", "Descarga electrica corta.",                        30),
    "spark":        MoveData("spark",        "Spark",          65,  1.0,  "electric", "Ataque corporal electrificado.",                   20),
    "thunderbolt":  MoveData("thunderbolt",  "Thunderbolt",    90,  1.0,  "electric", "Rayo electrico estable.",                          15),  # FIX 85→90
    "volttackle":   MoveData("volttackle",   "Volt Tackle",   120,  1.0,  "electric", "Embestida electrificada (recoil ignorado).",        15),  # FIX 95→120
    "magnetbomb":   MoveData("magnetbomb",   "Magnet Bomb",    60,  1.0,  "steel",    "Impacto metalico magnetizado.",                    20),
    "flashcannon":  MoveData("flashcannon",  "Flash Cannon",   80,  1.0,  "steel",    "Rayo acerado concentrado.",                        10),  # FIX 85→80

    # ── FLYING ─────────────────────────────────────────────────────────
    "gust":         MoveData("gust",         "Gust",           40,  1.0,  "flying",   "Rafaga de viento.",                                35),
    "wingattack":   MoveData("wingattack",   "Wing Attack",    60,  1.0,  "flying",   "Ataque con alas extendidas.",                      35),
    "airslash":     MoveData("airslash",     "Air Slash",      75,  0.95, "flying",   "Cuchilla de aire cortante.",                       15),  # FIX 80→75
    "hurricane":    MoveData("hurricane",    "Hurricane",     110,  0.7,  "flying",   "Torbellino violento de alta potencia.",             10),  # FIX 95→110

    # ── ROCK ───────────────────────────────────────────────────────────
    "rockthrow":    MoveData("rockthrow",    "Rock Throw",     50,  0.9,  "rock",     "Lanzamiento de rocas.",                            15),
    "rockslide":    MoveData("rockslide",    "Rock Slide",     75,  0.9,  "rock",     "Avalancha de rocas.",                              10),

    # ── DARK ───────────────────────────────────────────────────────────
    "bite":         MoveData("bite",         "Bite",           60,  1.0,  "dark",     "Mordida potente.",                                 25),

    # ── FIGHTING ───────────────────────────────────────────────────────
    "karatechop":   MoveData("karatechop",   "Karate Chop",    50,  1.0,  "fighting", "Golpe de mano preciso con alta critica.",          25),  # FIX 55→50
    "lowkick":      MoveData("lowkick",      "Low Kick",       60,  1.0,  "fighting", "Barrida baja (poder fijo como proxy).",            20),
    "brickbreak":   MoveData("brickbreak",   "Brick Break",    75,  1.0,  "fighting", "Golpe frontal que rompe barreras.",                15),
    "submission":   MoveData("submission",   "Submission",     80,  0.8,  "fighting", "Llave arriesgada (recoil ignorado).",              25),  # FIX 85→80

    # ── PSYCHIC ────────────────────────────────────────────────────────
    "confusion":    MoveData("confusion",    "Confusion",      50,  1.0,  "psychic",  "Impulso psiquico.",                                25),  # FIX 55→50
    "psybeam":      MoveData("psybeam",      "Psybeam",        65,  1.0,  "psychic",  "Rayo mental concentrado.",                         20),  # FIX 70→65
    "zenheadbutt":  MoveData("zenheadbutt",  "Zen Headbutt",   80,  0.9,  "psychic",  "Golpe psiquico frontal.",                          15),
    "psychic":      MoveData("psychic",      "Psychic",        90,  1.0,  "psychic",  "Onda mental de gran potencia.",                    10),

    # ── GHOST ──────────────────────────────────────────────────────────
    "shadowball":   MoveData("shadowball",   "Shadow Ball",    80,  1.0,  "ghost",    "Esfera oscura de energia.",                        15),
}

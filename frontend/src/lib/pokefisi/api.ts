// ── Tipos de respuesta del backend ───────────────────────────────────────────

export type ApiPokemon = {
  id: string;
  name: string;
  level: number;
  hp: number;
  attack: number;
  defense: number;
  speed: number;
  types: string[];
  moveIds: string[];
  spriteFrontUrl: string;
  spriteBackUrl: string;
};

export type StartBattlePayload = {
  mode: "human-vs-ai" | "ai-vs-ai";
  teamSize: number;
  difficulty: string;
  playerPokemonIds?: string[];
};

export type HumanAction = {
  actionType: string;
  index: number;
};

export type BackendMoveSlot = {
  name: string;
  pp: number;
  maxPp: number;
  type: string;
  power: number;
};

export type BackendActivePokemon = {
  name: string;
  level: number;
  currentHp: number;
  maxHp: number;
  hpRatio: number;
  spriteUrl: string;
  moves: BackendMoveSlot[];
  fainted: boolean;
};

export type BackendPartySlot = {
  name: string;
  fainted: boolean;
  active: boolean;
  hpRatio: number;
  status: string;
};

export type BackendViewState = {
  turn: number;
  message: string;
  player: {
    trainer: string;
    active: BackendActivePokemon;
    party: BackendPartySlot[];
  };
  enemy: {
    trainer: string;
    active: BackendActivePokemon;
    party: BackendPartySlot[];
  };
  actionGroups: {
    moves: Array<{ actionType: string; index: number; label: string }>;
    switches: Array<{ actionType: string; index: number; label: string }>;
    forcedSwitch: boolean;
  };
  panel: {
    menu: string;
    selectedGroup: string | null;
    selectedIndex: number | null;
    locked: boolean;
  };
};

export type BackendFrame = {
  type: string;
  animation: { type: string; side?: string; target?: string };
  state: BackendViewState;
};

export type BattleResponse = {
  sessionId: string;
  mode: string;
  over: boolean;
  winner: string | null;
  requiresHumanAction: boolean;
  currentState: BackendViewState;
  frames: BackendFrame[];
};

// ── Cliente HTTP ──────────────────────────────────────────────────────────────

// Usa la variable de entorno VITE_API_BASE_URL si esta definida; de lo contrario
// cae en el backend local de desarrollo. Si se usa proxy de Vite, dejar la variable
// como cadena vacia para que las rutas sean relativas.
const API_BASE_URL: string =
  (import.meta.env as Record<string, string | undefined>)["VITE_API_BASE_URL"] ?? "http://127.0.0.1:8000";

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json", ...init?.headers },
    ...init,
  });
  if (!response.ok) {
    const errorBody = await response.json().catch(() => ({ error: response.statusText }));
    throw new Error(((errorBody as Record<string, unknown>)["error"] as string | undefined) ?? "Error de comunicacion con el backend");
  }
  return response.json() as Promise<T>;
}

export const fetchPokemon = (): Promise<ApiPokemon[]> =>
  requestJson<{ pokemon: ApiPokemon[] }>("/api/pokemon").then((r) => r.pokemon);

export const startBattle = (payload: StartBattlePayload): Promise<BattleResponse> =>
  requestJson<BattleResponse>("/api/battle/start", {
    method: "POST",
    body: JSON.stringify(payload),
  });

export const sendHumanAction = (
  sessionId: string,
  action: HumanAction,
): Promise<BattleResponse> =>
  requestJson<BattleResponse>(`/api/battle/${sessionId}/action`, {
    method: "POST",
    body: JSON.stringify(action),
  });

export const stepAiBattle = (sessionId: string): Promise<BattleResponse> =>
  requestJson<BattleResponse>(`/api/battle/${sessionId}/step`, {
    method: "POST",
    body: "{}",
  });

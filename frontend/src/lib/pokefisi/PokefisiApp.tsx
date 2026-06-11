import { useEffect, useRef, useState } from "react";
import {
  DIFFICULTY_LABEL,
  DIFFICULTY_DESC,
  DIFFICULTY_TO_API,
  mapApiPokemon,
  mapBackendActivePokemon,
  mapBackendPartySlot,
  type Pokemon,
  type Move,
  type Difficulty,
} from "./data";
import {
  fetchPokemon,
  startBattle,
  sendHumanAction,
  stepAiBattle,
  type BattleResponse,
  type BackendViewState,
  type BackendFrame,
} from "./api";
import {
  PixelPanel,
  PixelButton,
  PokemonCard,
  PokemonSlot,
  PokemonHUD,
  TeamPokeballRow,
  MoveButton,
  MessagePanel,
  Pokeball,
} from "./components";

type Mode = "human" | "ai";
type TeamSize = 3 | 4;
type Screen = "menu" | "select" | "intro" | "battle" | "result";
type Speed = 1 | 2;
type ActionView = "main" | "moves" | "party";
type Anim = { side: "player" | "enemy" | null; kind: "attack" | "hit" | "faint" | "enter" | null };

const ENEMY_TRAINER = "https://play.pokemonshowdown.com/sprites/trainers/youngster-gen4dp.png";
const PLAYER_TRAINER_BACK = "https://play.pokemonshowdown.com/sprites/trainers/red.png";

/* ============ Main App ============ */

export default function PokefisiApp() {
  const [screen, setScreen] = useState<Screen>("menu");
  const [mode, setMode] = useState<Mode>("human");
  const [difficulty, setDifficulty] = useState<Difficulty>("medio");
  const [teamSize, setTeamSize] = useState<TeamSize>(3);

  // Pool de Pokemon cargado desde GET /api/pokemon
  const [pokemonPool, setPokemonPool] = useState<Pokemon[]>([]);
  // Estado de sesion de batalla activa
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [initialBattleResponse, setInitialBattleResponse] = useState<BattleResponse | null>(null);

  // Equipos para IntroScreen y ResultScreen (derivados del backend)
  const [playerTeam, setPlayerTeam] = useState<Pokemon[]>([]);
  const [enemyTeam, setEnemyTeam] = useState<Pokemon[]>([]);
  const [winner, setWinner] = useState<"player" | "enemy" | null>(null);

  const [loading, setLoading] = useState(false);
  const [apiError, setApiError] = useState<string | null>(null);

  // Cargar pool de Pokemon al montar
  useEffect(() => {
    fetchPokemon()
      .then((dtos) => setPokemonPool(dtos.map(mapApiPokemon)))
      .catch((err) => setApiError(`No se pudo conectar al backend: ${err.message}`));
  }, []);

  const handleStart = async (chosenMode: Mode) => {
    setMode(chosenMode);
    setApiError(null);
    if (chosenMode === "human") {
      setScreen("select");
      return;
    }
    setLoading(true);
    try {
      const response = await startBattle({
        mode: "ai-vs-ai",
        teamSize,
        difficulty: DIFFICULTY_TO_API[difficulty],
      });
      setSessionId(response.sessionId);
      setInitialBattleResponse(response);
      setPlayerTeam(response.currentState.player.party.map((s) => mapBackendPartySlot(s, pokemonPool)));
      setEnemyTeam(response.currentState.enemy.party.map((s) => mapBackendPartySlot(s, pokemonPool)));
      setScreen("intro");
    } catch (err) {
      setApiError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  };

  const handleConfirmTeam = async (chosen: Pokemon[]) => {
    setApiError(null);
    setLoading(true);
    try {
      const response = await startBattle({
        mode: "human-vs-ai",
        teamSize,
        difficulty: DIFFICULTY_TO_API[difficulty],
        playerPokemonIds: chosen.map((p) => p.id),
      });
      setSessionId(response.sessionId);
      setInitialBattleResponse(response);
      setPlayerTeam(chosen);
      setEnemyTeam(response.currentState.enemy.party.map((s) => mapBackendPartySlot(s, pokemonPool)));
      setScreen("intro");
    } catch (err) {
      setApiError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  };

  const handleBattleEnd = (w: "player" | "enemy", finalState: BackendViewState) => {
    setWinner(w);
    setPlayerTeam(finalState.player.party.map((s) => mapBackendPartySlot(s, pokemonPool)));
    setEnemyTeam(finalState.enemy.party.map((s) => mapBackendPartySlot(s, pokemonPool)));
    setScreen("result");
  };

  const handleAgain = async () => {
    setApiError(null);
    if (mode === "human") {
      setWinner(null);
      setSessionId(null);
      setInitialBattleResponse(null);
      setScreen("menu");
      return;
    }
    setLoading(true);
    try {
      const response = await startBattle({
        mode: "ai-vs-ai",
        teamSize,
        difficulty: DIFFICULTY_TO_API[difficulty],
      });
      setSessionId(response.sessionId);
      setInitialBattleResponse(response);
      setPlayerTeam(response.currentState.player.party.map((s) => mapBackendPartySlot(s, pokemonPool)));
      setEnemyTeam(response.currentState.enemy.party.map((s) => mapBackendPartySlot(s, pokemonPool)));
      setWinner(null);
      setScreen("intro");
    } catch (err) {
      setApiError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  };

  const reset = () => {
    setPlayerTeam([]);
    setEnemyTeam([]);
    setWinner(null);
    setSessionId(null);
    setInitialBattleResponse(null);
    setApiError(null);
    setScreen("menu");
  };

  return (
    <div className="fixed inset-0 w-screen h-screen bg-[oklch(0.94_0.04_140)] overflow-hidden flex items-center justify-center p-2">
      <div
        className="relative mx-auto"
        style={{
          width: "min(100vw - 1rem, (100vh - 1rem) * 16 / 9)",
          height: "min(100vh - 1rem, (100vw - 1rem) * 9 / 16)",
        }}
      >
        {/* Overlay de carga global */}
        {loading && (
          <div className="absolute inset-0 z-50 bg-ink/50 flex items-center justify-center">
            <PixelPanel>
              <p className="font-pixel text-sm text-ink px-8 py-6">Conectando con el backend...</p>
            </PixelPanel>
          </div>
        )}

        {/* Banner de error */}
        {apiError && (
          <div className="absolute bottom-4 left-4 right-4 z-50">
            <div className="pixel-border bg-pkred px-4 py-3 flex items-center justify-between">
              <p className="font-pixel text-[10px] text-cream">{apiError}</p>
              <button onClick={() => setApiError(null)} className="font-pixel text-[10px] text-cream ml-4 cursor-pointer">✕</button>
            </div>
          </div>
        )}

        {screen === "menu" && (
          <MenuScreen
            difficulty={difficulty}
            setDifficulty={setDifficulty}
            teamSize={teamSize}
            setTeamSize={setTeamSize}
            onStart={handleStart}
          />
        )}
        {screen === "select" && (
          <SelectScreen
            teamSize={teamSize}
            pokemonPool={pokemonPool}
            onBack={() => setScreen("menu")}
            onConfirm={handleConfirmTeam}
          />
        )}
        {screen === "intro" && (
          <IntroScreen
            mode={mode}
            playerTeam={playerTeam}
            enemyTeam={enemyTeam}
            onDone={() => setScreen("battle")}
          />
        )}
        {screen === "battle" && sessionId && initialBattleResponse && (
          <BattleScreen
            mode={mode}
            sessionId={sessionId}
            initialResponse={initialBattleResponse}
            pokemonPool={pokemonPool}
            onEnd={handleBattleEnd}
            onSurrender={(finalState) => handleBattleEnd("enemy", finalState)}
          />
        )}
        {screen === "result" && (
          <ResultScreen
            winner={winner}
            mode={mode}
            playerTeam={playerTeam}
            enemyTeam={enemyTeam}
            onMenu={reset}
            onAgain={handleAgain}
          />
        )}
      </div>
    </div>
  );
}

/* ============ MENU SCREEN ============ */

function MenuScreen({
  difficulty,
  setDifficulty,
  teamSize,
  setTeamSize,
  onStart,
}: {
  difficulty: Difficulty;
  setDifficulty: (d: Difficulty) => void;
  teamSize: TeamSize;
  setTeamSize: (n: TeamSize) => void;
  onStart: (m: Mode) => void;
}) {
  return (
    <div className="absolute inset-0 flex items-center justify-center">
      <div
        className="absolute inset-0 opacity-30 pointer-events-none"
        style={{
          backgroundImage:
            "linear-gradient(0deg, oklch(0.42 0.18 260 / 0.15) 1px, transparent 1px), linear-gradient(90deg, oklch(0.42 0.18 260 / 0.15) 1px, transparent 1px)",
          backgroundSize: "24px 24px",
        }}
      />
      <PixelPanel className="relative w-[640px] max-w-[92%]">
        <div className="p-8">
          <div className="flex items-center justify-center gap-3 mb-1">
            <Pokeball size={28} />
            <span className="font-pixel text-[10px] tracking-widest text-pkblue-deep">POKEFISI</span>
            <Pokeball size={28} />
          </div>
          <h1 className="font-pixel text-center text-lg text-ink mt-3">
            Selecciona el modo<br />de combate
          </h1>
          <p className="font-body-pixel text-center text-xl text-ink-soft mt-3 px-4">
            Elige si deseas jugar directamente contra la IA o mirar una batalla automática entre agentes.
          </p>

          <div className="mt-6 grid grid-cols-2 gap-4">
            <DropdownRetro
              label="Dificultad de la IA"
              value={difficulty}
              onChange={(v) => setDifficulty(v as Difficulty)}
              options={[
                { value: "facil", label: "Fácil" },
                { value: "medio", label: "Medio" },
                { value: "dificil", label: "Difícil" },
                { value: "maestro-sobrevilla", label: "Maestro-Sobrevilla" },
              ]}
            />
            <DropdownRetro
              label="Tamaño del equipo"
              value={String(teamSize)}
              onChange={(v) => setTeamSize(Number(v) as TeamSize)}
              options={[
                { value: "3", label: "3 vs 3" },
                { value: "4", label: "4 vs 4" },
              ]}
            />
          </div>

          <p className="font-body-pixel text-lg text-ink mt-3 px-1 min-h-[2.5rem]">
            {difficulty === "maestro-sobrevilla" ? (
              <span className="text-[oklch(0.55_0.15_80)]">★ {DIFFICULTY_DESC[difficulty]}</span>
            ) : (
              DIFFICULTY_DESC[difficulty]
            )}
          </p>

          <div className="mt-6 grid grid-cols-2 gap-4">
            <PixelButton size="lg" variant="primary" onClick={() => onStart("human")}>
              ▶ Human vs IA
            </PixelButton>
            <PixelButton size="lg" variant="secondary" onClick={() => onStart("ai")}>
              ◆ IA vs IA
            </PixelButton>
          </div>
        </div>
      </PixelPanel>
    </div>
  );
}

function DropdownRetro({
  label,
  value,
  onChange,
  options,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  options: { value: string; label: string }[];
}) {
  return (
    <label className="block">
      <span className="font-pixel text-[9px] text-pkblue-deep block mb-2">{label}</span>
      <div className="relative">
        <select
          value={value}
          onChange={(e) => onChange(e.target.value)}
          className="w-full font-pixel text-xs bg-cream pixel-border-blue px-3 py-3 pr-8 appearance-none cursor-pointer text-ink"
        >
          {options.map((o) => (
            <option key={o.value} value={o.value}>{o.label}</option>
          ))}
        </select>
        <span className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 font-pixel text-xs text-pkblue-deep">▼</span>
      </div>
    </label>
  );
}

/* ============ SELECT SCREEN ============ */

function SelectScreen({
  teamSize,
  pokemonPool,
  onBack,
  onConfirm,
}: {
  teamSize: TeamSize;
  pokemonPool: Pokemon[];
  onBack: () => void;
  onConfirm: (chosen: Pokemon[]) => void;
}) {
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const selected = selectedIds.map((id) => pokemonPool.find((p) => p.id === id)!).filter(Boolean);
  const full = selectedIds.length === teamSize;

  const toggle = (id: string) => {
    setSelectedIds((cur) => {
      if (cur.includes(id)) return cur.filter((x) => x !== id);
      if (cur.length >= teamSize) return cur;
      return [...cur, id];
    });
  };

  if (pokemonPool.length === 0) {
    return (
      <div className="absolute inset-0 flex items-center justify-center p-6">
        <PixelPanel>
          <p className="font-pixel text-sm text-ink px-8 py-6">Cargando Pokémon del backend...</p>
        </PixelPanel>
      </div>
    );
  }

  return (
    <div className="absolute inset-0 p-6">
      <PixelPanel className="h-full">
        <div className="p-6 h-full flex flex-col">
          <div className="flex items-center justify-between">
            <PixelButton variant="ghost" size="sm" onClick={onBack}>← Volver</PixelButton>
            <h2 className="font-pixel text-sm text-ink">Selecciona tu equipo</h2>
            <span className="font-pixel text-xs text-pkblue-deep">{selectedIds.length}/{teamSize}</span>
          </div>

          <div className="flex-1 mt-4 min-h-0 overflow-auto">
            <div className="grid grid-cols-6 gap-2">
              {pokemonPool.map((p) => {
                const isSelected = selectedIds.includes(p.id);
                return (
                  <PokemonCard
                    key={p.id}
                    pokemon={p}
                    selected={isSelected}
                    disabled={!isSelected && full}
                    onClick={() => toggle(p.id)}
                    compact
                  />
                );
              })}
            </div>
          </div>

          <div className="mt-5 flex items-center justify-between gap-4">
            <div className="flex items-center gap-2">
              {Array.from({ length: teamSize }).map((_, i) => (
                <div key={i} className="w-10 h-10 pixel-border bg-cream flex items-center justify-center">
                  {selected[i] ? (
                    <img src={selected[i].icon} alt="" className="max-h-9" style={{ imageRendering: "pixelated" }} />
                  ) : (
                    <Pokeball size={20} state="fainted" />
                  )}
                </div>
              ))}
            </div>
            <PixelButton variant="primary" size="lg" disabled={!full} onClick={() => onConfirm(selected)}>
              Confirmar equipo
            </PixelButton>
          </div>
        </div>
      </PixelPanel>
    </div>
  );
}

/* ============ INTRO SCREEN ============ */

function IntroScreen({
  mode,
  playerTeam,
  enemyTeam,
  onDone,
}: {
  mode: Mode;
  playerTeam: Pokemon[];
  enemyTeam: Pokemon[];
  onDone: () => void;
}) {
  const [step, setStep] = useState(0);
  const messages = [
    "¡Un entrenador rival quiere combatir!",
    mode === "ai"
      ? "¡Dos agentes IA están listos para luchar!"
      : "¡La IA desafiante envía a su primer Pokémon!",
    "¡Prepárate para el combate!",
  ];

  useEffect(() => {
    const t = setTimeout(() => {
      if (step < messages.length - 1) setStep(step + 1);
      else onDone();
    }, 1400);
    return () => clearTimeout(t);
    // onDone es estable desde el padre; messages es constante local — sin riesgo de stale.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [step]);

  return (
    <div className="absolute inset-0 p-6">
      <div className="relative h-full pixel-border bg-gradient-to-b from-[oklch(0.85_0.08_220)] to-[oklch(0.88_0.1_140)] overflow-hidden rounded-md">
        <div className="absolute bottom-0 left-0 right-0 h-[40%] bg-gradient-to-b from-[oklch(0.82_0.12_135)] to-[oklch(0.7_0.14_130)]" />
        <div className="absolute top-16 right-24 anim-enter">
          <div className="flex flex-col items-center gap-2">
            <img src={ENEMY_TRAINER} alt="Rival" className="h-32" style={{ imageRendering: "pixelated" }} />
            <TeamPokeballRow team={enemyTeam} />
          </div>
        </div>
        <div className="absolute bottom-32 left-24 anim-enter">
          <div className="flex flex-col items-center gap-2">
            <img src={PLAYER_TRAINER_BACK} alt="Jugador" className="h-56" style={{ imageRendering: "pixelated", transform: "scaleX(-1)" }} />
            <TeamPokeballRow team={playerTeam} />
          </div>
        </div>
        <div className="absolute bottom-6 left-6 right-6">
          <MessagePanel text={messages[step]} />
        </div>
      </div>
    </div>
  );
}

/* ============ BATTLE SCREEN ============ */

type PlayResult = { over: boolean; winnerSide: "player" | "enemy" | null; finalState: BackendViewState };

function BattleScreen({
  mode,
  sessionId,
  initialResponse,
  pokemonPool,
  onEnd,
  onSurrender,
}: {
  mode: Mode;
  sessionId: string;
  initialResponse: BattleResponse;
  pokemonPool: Pokemon[];
  onEnd: (w: "player" | "enemy", finalState: BackendViewState) => void;
  onSurrender: (finalState: BackendViewState) => void;
}) {
  const [backendState, setBackendState] = useState<BackendViewState>(initialResponse.currentState);
  const [message, setMessage] = useState(initialResponse.currentState.message);
  const [anim, setAnim] = useState<Anim>({ side: null, kind: null });
  const [busy, setBusy] = useState(true);
  const [view, setView] = useState<ActionView>("main");
  const [needsPlayerSwap, setNeedsPlayerSwap] = useState(false);
  const [hoverMove, setHoverMove] = useState<Move | null>(null);
  const [showSurrender, setShowSurrender] = useState(false);
  const [showPartyConfirm, setShowPartyConfirm] = useState<{ pokemon: Pokemon; index: number } | null>(null);
  const [paused, setPaused] = useState(false);
  const [speed, setSpeed] = useState<Speed>(1);

  const speedRef = useRef(speed);
  useEffect(() => { speedRef.current = speed; }, [speed]);

  // Estado derivado del frame actual
  const playerActive = mapBackendActivePokemon(backendState.player.active, "player", pokemonPool);
  const enemyActive = mapBackendActivePokemon(backendState.enemy.active, "enemy", pokemonPool);
  const playerParty = backendState.player.party.map((s) => mapBackendPartySlot(s, pokemonPool));
  const enemyParty = backendState.enemy.party.map((s) => mapBackendPartySlot(s, pokemonPool));
  const playerActiveIndex = backendState.player.party.findIndex((s) => s.active);
  const legalMoveIndices = new Set(backendState.actionGroups.moves.map((m) => m.index));
  const legalSwitchIndices = new Set(backendState.actionGroups.switches.map((s) => s.index));

  const delay = (ms: number) => new Promise<void>((r) => setTimeout(r, Math.max(50, ms / speedRef.current)));

  // ── Reproduccion de frames ─────────────────────────────────────────────────

  const playFrames = async (frames: BackendFrame[]): Promise<PlayResult> => {
    for (const frame of frames) {
      const { animation, state, type } = frame;

      setMessage(state.message);

      if (animation.type === "attack" && animation.side) {
        const attackSide = animation.side as "player" | "enemy";
        const hitSide = (animation.target ?? (attackSide === "player" ? "enemy" : "player")) as "player" | "enemy";
        setAnim({ side: attackSide, kind: "attack" });
        await delay(380);
        setBackendState(state);
        setAnim({ side: hitSide, kind: "hit" });
        await delay(280);
        setAnim({ side: null, kind: null });
      } else if (animation.type === "faint" && animation.side) {
        const side = animation.side as "player" | "enemy";
        setAnim({ side, kind: "faint" });
        setBackendState(state);
        await delay(800);
        setAnim({ side: null, kind: null });
      } else if (animation.type === "switch" && animation.side) {
        const side = animation.side as "player" | "enemy";
        setAnim({ side, kind: "enter" });
        setBackendState(state);
        await delay(650);
        setAnim({ side: null, kind: null });
      } else {
        setBackendState(state);
        await delay(320);
      }

      if (type === "result") {
        return { over: true, winnerSide: (animation.side as "player" | "enemy") ?? "enemy", finalState: state };
      }
    }
    const lastState = frames.length > 0 ? frames[frames.length - 1].state : backendState;
    return { over: false, winnerSide: null, finalState: lastState };
  };

  const applyResponse = async (response: BattleResponse) => {
    const result = await playFrames(response.frames);
    if (result.over && result.winnerSide) {
      onEnd(result.winnerSide, result.finalState);
      return;
    }
    const fs = result.finalState;
    const forced = fs.actionGroups.forcedSwitch;
    if (forced && mode === "human") {
      setNeedsPlayerSwap(true);
      setView("party");
    } else {
      setNeedsPlayerSwap(false);
      setView("main");
    }
    setBusy(fs.panel.locked);
  };

  // ── Intro al entrar a BattleScreen ─────────────────────────────────────────

  const introRan = useRef(false);
  useEffect(() => {
    if (introRan.current) return;
    introRan.current = true;
    applyResponse(initialResponse);
    // Efecto de entrada único; introRan.current evita doble ejecución en StrictMode.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // ── Loop de IA vs IA ───────────────────────────────────────────────────────

  useEffect(() => {
    if (mode !== "ai" || busy || paused) return;
    const t = setTimeout(async () => {
      setBusy(true);
      try {
        const response = await stepAiBattle(sessionId);
        await applyResponse(response);
      } catch {
        setBusy(false);
      }
    }, 700 / speedRef.current);
    return () => clearTimeout(t);
    // sessionId es estable durante la sesión; applyResponse captura estado fresco via setters.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [mode, busy, paused]);

  // ── Acciones del jugador ───────────────────────────────────────────────────

  const handleMove = async (moveIndex: number) => {
    if (busy) return;
    setBusy(true);
    setView("main");
    try {
      const response = await sendHumanAction(sessionId, { actionType: "move", index: moveIndex });
      await applyResponse(response);
    } catch (err) {
      setMessage(`Error: ${err instanceof Error ? err.message : String(err)}`);
      setBusy(false);
    }
  };

  const handleSwitch = async (partySlotIndex: number) => {
    setBusy(true);
    setView("main");
    setNeedsPlayerSwap(false);
    try {
      const response = await sendHumanAction(sessionId, { actionType: "switch", index: partySlotIndex });
      await applyResponse(response);
    } catch (err) {
      setMessage(`Error: ${err instanceof Error ? err.message : String(err)}`);
      setBusy(false);
    }
  };

  const handlePartyPick = (p: Pokemon, idx: number) => {
    if (!legalSwitchIndices.has(idx)) return;
    if (needsPlayerSwap) {
      handleSwitch(idx);
      return;
    }
    setShowPartyConfirm({ pokemon: p, index: idx });
  };

  const confirmSwap = () => {
    if (!showPartyConfirm) return;
    const { index } = showPartyConfirm;
    setShowPartyConfirm(null);
    handleSwitch(index);
  };

  return (
    <div className="absolute inset-0 p-4">
      <div className="relative h-full pixel-border overflow-hidden rounded-md bg-gradient-to-b from-[oklch(0.85_0.08_220)] via-[oklch(0.9_0.08_180)] to-[oklch(0.85_0.14_135)]">

        {/* Controles IA vs IA */}
        {mode === "ai" && (
          <div className="absolute top-3 left-3 z-30 flex gap-2">
            <PixelButton size="sm" variant="ghost" onClick={() => setPaused((x) => !x)}>
              {paused ? "▶ Continuar" : "❚❚ Pausar"}
            </PixelButton>
            <PixelButton size="sm" variant="ghost" onClick={() => setSpeed((s) => (s === 1 ? 2 : 1))}>
              {speed === 1 ? "x1" : "x2"}
            </PixelButton>
          </div>
        )}

        {/* Botón rendirse */}
        <button
          onClick={() => setShowSurrender(true)}
          className="absolute top-3 right-3 z-30 font-pixel text-[9px] bg-cream/80 border-2 border-ink px-2 py-1 rounded-sm hover:bg-cream cursor-pointer"
        >
          ⚐ Rendirse
        </button>

        {/* HUD enemigo */}
        <div className="absolute top-6 left-6 z-20">
          <PokemonHUD pokemon={enemyActive} side="enemy" />
          <div className="mt-2"><TeamPokeballRow team={enemyParty} /></div>
        </div>

        {/* Sprite enemigo */}
        <div className="absolute top-12 right-[12%] z-10">
          <div className="relative">
            <div className="absolute -bottom-4 left-1/2 -translate-x-1/2 w-48 h-10 rounded-[50%] bg-[oklch(0.55_0.1_130)] opacity-60 blur-[1px]" />
            <div className={`relative transition-opacity
              ${anim.side === "enemy" && anim.kind === "hit" ? "anim-shake anim-flash" : ""}
              ${anim.side === "enemy" && anim.kind === "attack" ? "anim-attack-enemy" : ""}
              ${anim.side === "enemy" && anim.kind === "faint" ? "anim-faint" : ""}
              ${anim.side === "enemy" && anim.kind === "enter" ? "anim-enter" : ""}
            `}>
              <img src={enemyActive.sprite} alt={enemyActive.name} className="h-36 anim-float" style={{ imageRendering: "pixelated" }} />
            </div>
          </div>
        </div>

        {/* Sprite jugador */}
        <div className="absolute bottom-[26%] left-[10%] z-10">
          <div className="relative">
            <div className="absolute -bottom-6 left-1/2 -translate-x-1/2 w-64 h-12 rounded-[50%] bg-[oklch(0.5_0.1_125)] opacity-70 blur-[1px]" />
            <div className={`relative
              ${anim.side === "player" && anim.kind === "hit" ? "anim-shake anim-flash" : ""}
              ${anim.side === "player" && anim.kind === "attack" ? "anim-attack-player" : ""}
              ${anim.side === "player" && anim.kind === "faint" ? "anim-faint" : ""}
              ${anim.side === "player" && anim.kind === "enter" ? "anim-enter" : ""}
            `}>
              <img
                src={playerActive.spriteBack}
                alt={playerActive.name}
                className="h-56"
                style={{ imageRendering: "pixelated" }}
                onError={(e) => { (e.target as HTMLImageElement).src = playerActive.sprite; }}
              />
            </div>
          </div>
        </div>

        {/* HUD jugador */}
        <div className="absolute bottom-[28%] right-6 z-20">
          <PokemonHUD pokemon={playerActive} side="player" />
          <div className="mt-2"><TeamPokeballRow team={playerParty} align="right" /></div>
        </div>

        {/* Barra inferior: mensaje + acciones */}
        <div className="absolute bottom-0 left-0 right-0 z-30 grid grid-cols-2 gap-2 p-3 bg-gradient-to-t from-ink/15 to-transparent">
          <MessagePanel text={message} />
          <ActionPanel
            view={view}
            setView={setView}
            player={playerActive}
            playerTeam={playerParty}
            playerIdx={playerActiveIndex}
            hoverMove={hoverMove}
            setHoverMove={setHoverMove}
            busy={busy || mode === "ai"}
            legalMoveIndices={legalMoveIndices}
            onMove={handleMove}
            onPickParty={handlePartyPick}
            onMessage={setMessage}
            needsSwap={needsPlayerSwap}
          />
        </div>

        {/* Modal rendirse */}
        {showSurrender && (
          <ModalOverlay>
            <PixelPanel className="w-[420px]">
              <div className="p-6">
                <p className="font-body-pixel text-2xl text-ink">¿Seguro que deseas rendirte?</p>
                <div className="mt-5 flex gap-3 justify-end">
                  <PixelButton variant="ghost" onClick={() => setShowSurrender(false)}>NO</PixelButton>
                  <PixelButton variant="danger" onClick={() => { setShowSurrender(false); onSurrender(backendState); }}>SÍ</PixelButton>
                </div>
              </div>
            </PixelPanel>
          </ModalOverlay>
        )}

        {/* Modal cambio voluntario */}
        {showPartyConfirm && (
          <ModalOverlay>
            <PixelPanel className="w-[420px]">
              <div className="p-6">
                <p className="font-body-pixel text-2xl text-ink">¿Cambiar a {showPartyConfirm.pokemon.name}?</p>
                <div className="mt-5 flex gap-3 justify-end">
                  <PixelButton variant="ghost" onClick={() => setShowPartyConfirm(null)}>NO</PixelButton>
                  <PixelButton variant="primary" onClick={confirmSwap}>SÍ</PixelButton>
                </div>
              </div>
            </PixelPanel>
          </ModalOverlay>
        )}
      </div>
    </div>
  );
}

function ModalOverlay({ children }: { children: React.ReactNode }) {
  return (
    <div className="absolute inset-0 z-50 bg-ink/40 flex items-center justify-center backdrop-blur-[1px]">
      {children}
    </div>
  );
}

/* ============ ACTION PANEL ============ */

function ActionPanel({
  view,
  setView,
  player,
  playerTeam,
  playerIdx,
  hoverMove,
  setHoverMove,
  busy,
  legalMoveIndices,
  onMove,
  onPickParty,
  onMessage,
  needsSwap,
}: {
  view: ActionView;
  setView: (v: ActionView) => void;
  player: Pokemon;
  playerTeam: Pokemon[];
  playerIdx: number;
  hoverMove: Move | null;
  setHoverMove: (m: Move | null) => void;
  busy: boolean;
  legalMoveIndices: Set<number>;
  onMove: (index: number) => void;
  onPickParty: (p: Pokemon, i: number) => void;
  onMessage: (s: string) => void;
  needsSwap: boolean;
}) {
  return (
    <div className="pixel-border bg-cream p-3 min-h-[110px]">
      {view === "main" && (
        <div className="grid grid-cols-2 gap-3 h-full">
          <PixelButton
            variant="primary"
            size="lg"
            disabled={busy}
            onClick={() => { setView("moves"); onMessage("Elige un movimiento."); }}
            className="!text-base"
          >
            ⚔ LUCHAR
          </PixelButton>
          <PixelButton
            variant="secondary"
            size="lg"
            disabled={busy && !needsSwap}
            onClick={() => setView("party")}
            className="!text-base"
          >
            ◉ POKÉMON
          </PixelButton>
        </div>
      )}

      {view === "moves" && (
        <div className="grid grid-cols-2 gap-2 h-full">
          {player.moves.map((m, i) => (
            <MoveButton
              key={i}
              move={m}
              disabled={busy || !legalMoveIndices.has(i)}
              onHover={() => { setHoverMove(m); onMessage(m.desc); }}
              onClick={() => onMove(i)}
            />
          ))}
          <button
            onClick={() => { setView("main"); onMessage(`¿Qué hará ${player.name}?`); }}
            className="col-span-2 font-pixel text-[10px] text-pkblue-deep underline mt-1 cursor-pointer"
          >
            ← ATRÁS
          </button>
        </div>
      )}

      {view === "party" && (
        <div className="grid grid-cols-2 gap-2">
          {playerTeam.map((p, i) => (
            <PokemonSlot
              key={p.id + i}
              pokemon={p}
              active={i === playerIdx}
              onClick={() => onPickParty(p, i)}
            />
          ))}
          {!needsSwap && (
            <button
              onClick={() => { setView("main"); onMessage(`¿Qué hará ${player.name}?`); }}
              className="col-span-2 font-pixel text-[10px] text-pkblue-deep underline mt-1 cursor-pointer"
            >
              ← ATRÁS
            </button>
          )}
        </div>
      )}
    </div>
  );
}

/* ============ RESULT SCREEN ============ */

function ResultScreen({
  winner,
  mode,
  playerTeam,
  enemyTeam,
  onMenu,
  onAgain,
}: {
  winner: "player" | "enemy" | null;
  mode: Mode;
  playerTeam: Pokemon[];
  enemyTeam: Pokemon[];
  onMenu: () => void;
  onAgain: () => void;
}) {
  const title =
    mode === "ai"
      ? winner === "player" ? "¡La IA Aliada ganó!" : "¡La IA Rival ganó!"
      : winner === "player" ? "¡Ganaste!" : "Perdiste...";

  const playerAlive = playerTeam.filter((p) => !p.fainted).length;
  const enemyAlive = enemyTeam.filter((p) => !p.fainted).length;

  return (
    <div className="absolute inset-0 flex items-center justify-center p-6">
      <PixelPanel className="w-[640px] max-w-full">
        <div className="p-8">
          <h2 className="font-pixel text-center text-xl text-ink">{title}</h2>
          <p className="font-body-pixel text-center text-xl text-ink-soft mt-2">Combate finalizado.</p>

          <div className="mt-6 grid grid-cols-2 gap-4">
            <TeamSummary label="Tu equipo" team={playerTeam} alive={playerAlive} />
            <TeamSummary label="Rival" team={enemyTeam} alive={enemyAlive} />
          </div>

          <div className="mt-6 grid grid-cols-2 gap-3">
            <PixelButton variant="ghost" size="lg" onClick={onMenu}>← VOLVER AL MENÚ</PixelButton>
            <PixelButton variant="primary" size="lg" onClick={onAgain}>⚔ NUEVA BATALLA</PixelButton>
          </div>
        </div>
      </PixelPanel>
    </div>
  );
}

function TeamSummary({ label, team, alive }: { label: string; team: Pokemon[]; alive: number }) {
  return (
    <div className="pixel-border bg-cream p-3">
      <div className="flex items-center justify-between">
        <span className="font-pixel text-[10px] text-pkblue-deep">{label}</span>
        <span className="font-pixel text-[9px] text-ink-soft">{alive}/{team.length}</span>
      </div>
      <div className="mt-2 grid grid-cols-4 gap-1.5">
        {team.map((p, i) => (
          <div key={i} className="flex flex-col items-center gap-1">
            <div className="w-12 h-12 flex items-center justify-center bg-[oklch(0.93_0.04_140)] border-2 border-ink/60 rounded-sm">
              <img
                src={p.icon}
                alt={p.name}
                className={`max-h-10 ${p.fainted ? "grayscale opacity-50" : ""}`}
                style={{ imageRendering: "pixelated" }}
              />
            </div>
            <Pokeball size={14} state={p.fainted ? "fainted" : "alive"} />
          </div>
        ))}
      </div>
    </div>
  );
}

(function () {
  const DIFFICULTY_HINTS = {
    easy: "Ideal para aprender. La IA actua aleatoriamente.",
    medium: "Estrategia basica. La IA maximiza HP.",
    hard: "Planificacion tactica. La IA anticipa 2 turnos.",
    sobrevilla: "IA entrenada con algoritmos geneticos. Maximo desafio.",
  };

  const DIFFICULTY_LABELS = {
    easy: "Facil",
    medium: "Medio",
    hard: "Dificil",
    sobrevilla: "Maestro",
  };

  const elements = {
    modeScreen: document.getElementById("mode-screen"),
    startHuman: document.getElementById("start-human"),
    startAi: document.getElementById("start-ai"),
    difficulty: document.getElementById("difficulty"),
    difficultyHint: document.getElementById("difficulty-hint"),
    teamSize: document.getElementById("team-size"),
    battleScreen: document.getElementById("battle-screen"),
    battlefield: document.getElementById("battlefield"),
    message: document.getElementById("battle-message"),
    statusPill: document.getElementById("battle-status-pill"),
    winnerBanner: document.getElementById("winner-banner"),
    panelTitle: document.getElementById("panel-title"),
    panelSubtitle: document.getElementById("panel-subtitle"),
    panelBack: document.getElementById("panel-back"),
    playerName: document.getElementById("player-name"),
    playerLevel: document.getElementById("player-level"),
    playerHpFill: document.getElementById("player-hp-fill"),
    playerHpText: document.getElementById("player-hp-text"),
    playerSprite: document.getElementById("player-sprite"),
    playerSpriteWrapper: document.getElementById("player-sprite-wrapper"),
    playerParty: document.getElementById("player-party"),
    enemyName: document.getElementById("enemy-name"),
    enemyLevel: document.getElementById("enemy-level"),
    enemyHpFill: document.getElementById("enemy-hp-fill"),
    enemySprite: document.getElementById("enemy-sprite"),
    enemySpriteWrapper: document.getElementById("enemy-sprite-wrapper"),
    enemyParty: document.getElementById("enemy-party"),
    actionButtons: [0, 1, 2, 3].map((index) => document.getElementById(`action-${index}`)),
    newGame: document.getElementById("new-game"),
    next: document.getElementById("next-frame"),
    toggle: document.getElementById("toggle-play"),
  };

  const api = {
    async post(path, body) {
      const response = await fetch(path, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body || {}),
      });
      const payload = await response.json();
      if (!response.ok) {
        throw new Error(payload.error || "No se pudo completar la operacion.");
      }
      return payload;
    },
  };

  const state = {
    sessionId: null,
    mode: null,
    packet: null,
    visibleState: null,
    autoplay: false,
    busy: false,
    menu: "root",
  };

  const POKEBALL_SPRITE = "https://play.pokemonshowdown.com/sprites/bwicons-pokeball-sheet.png";
  const FRAME_DELAY_TURN = 1100;
  const FRAME_DELAY_ACTION = 1500;
  const AI_FRAME_DELAYS = {
    turn: 1800,
    choice: 2200,
    attack: 2400,
    switch: 2400,
    faint: 2400,
    result: 2600,
    prompt: 1800,
    default: 2200,
  };

  function renderParty(container, party) {
    container.innerHTML = "";
    party.forEach((member) => {
      const ball = document.createElement("span");
      ball.className = `party-ball is-${member.status}`;
      ball.title = member.name;
      ball.style.backgroundImage = `url('${POKEBALL_SPRITE}')`;
      container.appendChild(ball);
    });
  }

  function setActionButtons(items, options) {
    const handlers = options.handlers || [];
    const locked = Boolean(options.locked);
    elements.panelTitle.textContent = options.title;
    elements.panelSubtitle.textContent = options.subtitle || "";
    elements.panelSubtitle.classList.toggle("hidden", !options.subtitle);
    elements.panelBack.onclick = null;
    elements.panelBack.classList.toggle("hidden", !options.showBack);
    if (options.showBack && options.onBack) {
      elements.panelBack.onclick = options.onBack;
    }

    elements.actionButtons.forEach((button, index) => {
      const item = items[index];
      button.onclick = null;
      button.classList.remove("is-hidden", "action-btn--fight", "action-btn--pokemon", "action-btn--command", "is-selected");

      if (!item) {
        button.textContent = "-";
        button.classList.add("is-disabled", "is-hidden");
        button.classList.remove("is-active");
        button.disabled = true;
        return;
      }

      const disabled = Boolean(item.disabled);
      button.textContent = item.label.toUpperCase();
      button.disabled = disabled;
      button.classList.toggle("is-disabled", disabled);
      button.classList.toggle("is-active", !disabled || Boolean(item.selected));
      button.classList.toggle("is-selected", Boolean(item.selected));
      if (item.variant) {
        button.classList.add(...item.variant.split(" "));
      }
      if (!disabled && !locked && handlers[index]) {
        button.onclick = handlers[index];
      }
    });
  }

  function getVisibleViewState() {
    return state.visibleState || state.packet?.currentState || null;
  }

  function getFrameDelay(frame) {
    if (state.mode !== "ai-vs-ai") {
      return frame.type === "turn" ? FRAME_DELAY_TURN : FRAME_DELAY_ACTION;
    }

    return AI_FRAME_DELAYS[frame.type] || AI_FRAME_DELAYS.default;
  }

  function animateFrame(frame) {
    const animation = frame.animation || { type: "idle" };
    const playerWrapper = elements.playerSpriteWrapper;
    const enemyWrapper = elements.enemySpriteWrapper;

    [playerWrapper, enemyWrapper].forEach((wrapper) => {
      wrapper.classList.remove("attack", "hit", "switch", "faint");
      void wrapper.offsetWidth;
    });

    if (animation.type === "attack") {
      const attacker = animation.side === "player" ? playerWrapper : enemyWrapper;
      const target = animation.target === "player" ? playerWrapper : enemyWrapper;
      attacker.classList.add("attack");
      target.classList.add("hit");
    }

    if (animation.type === "switch") {
      const target = animation.side === "player" ? playerWrapper : enemyWrapper;
      target.classList.add("switch");
    }

    if (animation.type === "faint") {
      const target = animation.side === "player" ? playerWrapper : enemyWrapper;
      target.classList.add("faint");
    }
  }

  function renderView(viewState, animation) {
    const player = viewState.player.active;
    const enemy = viewState.enemy.active;

    elements.message.textContent = viewState.message;

    elements.playerName.textContent = player.name.toUpperCase();
    elements.playerLevel.textContent = `Lv${player.level}`;
    elements.playerHpFill.style.width = `${player.hpPercent}%`;
    elements.playerHpFill.style.backgroundColor = player.hpColor;
    elements.playerHpText.textContent = `${player.currentHp} / ${player.maxHp}`;
    elements.playerSprite.src = player.spriteUrl;

    elements.enemyName.textContent = enemy.name.toUpperCase();
    elements.enemyLevel.textContent = `Lv${enemy.level}`;
    elements.enemyHpFill.style.width = `${enemy.hpPercent}%`;
    elements.enemyHpFill.style.backgroundColor = enemy.hpColor;
    elements.enemySprite.src = enemy.spriteUrl;

    renderParty(elements.playerParty, viewState.player.party);
    renderParty(elements.enemyParty, viewState.enemy.party);
    animateFrame({ animation: animation || { type: "idle" } });
  }

  function updateTopControls() {
    elements.newGame.disabled = state.busy;

    if (state.mode === "ai-vs-ai") {
      elements.toggle.classList.remove("hidden");
      elements.next.classList.remove("hidden");
      const canAutoplay = !state.packet?.over && !state.busy;
      const canStep = !state.packet?.over && !state.busy;
      elements.toggle.disabled = !canAutoplay;
      elements.next.disabled = !canStep;
      elements.toggle.textContent = state.autoplay ? "PAUSE" : "AUTO";
      elements.next.textContent = "NEXT";
      elements.statusPill.textContent = "Modo espectador";
      return;
    }

    elements.toggle.classList.add("hidden");
    elements.next.classList.add("hidden");
    elements.toggle.disabled = true;
    elements.next.disabled = true;
    const diffLabel = DIFFICULTY_LABELS[state.difficulty] || "";
    elements.statusPill.textContent = diffLabel
      ? `Modo jugador (${diffLabel})`
      : "Modo jugador";
  }

  function updateWinnerBanner() {
    if (!state.packet?.over) {
      elements.winnerBanner.classList.add("hidden");
      elements.winnerBanner.textContent = "";
      return;
    }
    const winner = state.packet.winner || "Empate";
    elements.winnerBanner.textContent = `GANADOR: ${winner.toUpperCase()}`;
    elements.winnerBanner.classList.remove("hidden");
  }

  function renderActionPanel(viewState) {
    const currentView = viewState || getVisibleViewState();
    if (!state.packet || !currentView) {
      setActionButtons([], {
        title: "Comandos",
        subtitle: "Selecciona un modo para comenzar",
      });
      return;
    }

    const actionGroups = currentView.actionGroups;
    const panel = currentView.panel || {};
    const isForcedSwitch = actionGroups.forcedSwitch;
    const hasSwitches = Boolean(actionGroups.switches.length);
    const lockedPanel = Boolean(panel.locked);

    if (state.packet.over) {
      setActionButtons(
        [
          { label: "Nueva", disabled: false },
          { label: "Batalla", disabled: false },
        ],
        {
          title: "Fin del combate",
          subtitle: "Puedes iniciar otra partida",
          handlers: [showModeScreen, showModeScreen],
        }
      );
      return;
    }

    let activeMenu = panel.menu || (isForcedSwitch ? "switch" : "root");
    if (!lockedPanel) {
      if (isForcedSwitch) {
        state.menu = "switch";
      } else if (state.menu === "switch" && !hasSwitches) {
        state.menu = "root";
      } else if (state.menu !== "moves" && state.menu !== "switch") {
        state.menu = "root";
      }
      activeMenu = state.menu;
    }

    if (activeMenu === "root") {
      setActionButtons(
        [
          {
            label: "Luchar",
            disabled: !lockedPanel && state.busy,
            selected: panel.selectedGroup === "moves",
            variant: "action-btn--fight action-btn--command",
          },
          {
            label: "Pokemon",
            disabled: (!lockedPanel && state.busy) || !hasSwitches,
            selected: panel.selectedGroup === "switch",
            variant: "action-btn--pokemon action-btn--command",
          },
        ],
        {
          title: "Comandos",
          subtitle: lockedPanel ? "La IA decide entre Lucha o Pokemon" : "Selecciona Lucha o Pokemon",
          locked: lockedPanel,
          handlers: [
            () => {
              state.menu = "moves";
              renderActionPanel();
            },
            () => {
              state.menu = "switch";
              renderActionPanel();
            },
          ],
        }
      );
      return;
    }

    if (activeMenu === "switch") {
      const items = actionGroups.switches.map((entry) => ({
        label: entry.label,
        disabled: !lockedPanel && state.busy,
        selected: panel.selectedIndex === entry.index,
      }));
      const handlers = actionGroups.switches.map((entry) => () => submitHumanAction(entry));
      setActionButtons(items.slice(0, 4), {
        title: "Pokemon",
        subtitle: lockedPanel ? "La IA elige un cambio aleatorio" : "Selecciona un Pokemon",
        handlers,
        locked: lockedPanel,
        showBack: !isForcedSwitch && !lockedPanel,
        onBack: () => {
          state.menu = "root";
          renderActionPanel();
        },
      });
      return;
    }

    setActionButtons(actionGroups.moves.map((move) => ({
        label: move.label,
        disabled: !lockedPanel && state.busy,
        selected: panel.selectedIndex === move.index,
      })).slice(0, 4), {
        title: "Lucha",
        subtitle: lockedPanel ? "La IA elige un movimiento aleatorio" : "Selecciona un movimiento",
        handlers: actionGroups.moves.map((move) => () => submitHumanAction(move)),
        locked: lockedPanel,
        showBack: !lockedPanel,
        onBack: () => {
          state.menu = "root";
          renderActionPanel();
        },
      });
  }

  function renderPacket(packet) {
    state.packet = packet;
    state.visibleState = packet.currentState;
    renderView(packet.currentState, { type: "idle" });
    updateTopControls();
    updateWinnerBanner();
    renderActionPanel(packet.currentState);
  }

  function playFrames(frames) {
    if (!frames.length) {
      renderPacket(state.packet);
      afterFrames();
      return;
    }

    state.busy = true;
    updateTopControls();

    const queue = frames.slice();
    const runNext = function () {
      const frame = queue.shift();
      if (!frame) {
        state.busy = false;
        renderPacket(state.packet);
        afterFrames();
        return;
      }

      state.visibleState = frame.state;
      renderView(frame.state, frame.animation);
      updateWinnerBanner();
      renderActionPanel(frame.state);
      window.setTimeout(runNext, getFrameDelay(frame));
    };
    runNext();
  }

  function afterFrames() {
    if (state.autoplay && state.mode === "ai-vs-ai" && state.packet && !state.packet.over) {
      requestAiStep();
      return;
    }
    updateTopControls();
    renderActionPanel();
  }

  function applyPacket(packet) {
    state.packet = packet;
    playFrames(packet.frames || []);
  }

  async function startBattle(mode) {
    const difficulty = elements.difficulty ? elements.difficulty.value : "medium";
    state.autoplay = false;
    state.menu = "root";
    state.difficulty = difficulty;
    elements.modeScreen.classList.add("hidden");
    elements.message.textContent = "Preparando batalla...";
    try {
      const packet = await api.post("/api/battle/start", {
        mode,
        teamSize: Number(elements.teamSize.value),
        difficulty,
      });
      state.sessionId = packet.sessionId;
      state.mode = packet.mode;
      state.menu = packet.currentState.actionGroups.forcedSwitch ? "switch" : "root";
      applyPacket(packet);
    } catch (error) {
      elements.modeScreen.classList.remove("hidden");
      elements.message.textContent = error.message;
    }
  }

  async function requestAiStep() {
    if (!state.sessionId || state.busy || !state.packet || state.packet.over) {
      return;
    }
    state.busy = true;
    updateTopControls();
    try {
      const packet = await api.post(`/api/battle/${state.sessionId}/step`, {});
      applyPacket(packet);
    } catch (error) {
      state.busy = false;
      state.autoplay = false;
      elements.message.textContent = error.message;
      updateTopControls();
    }
  }

  async function submitHumanAction(action) {
    if (!state.sessionId || state.busy || !state.packet || state.packet.over) {
      return;
    }
    state.busy = true;
    updateTopControls();
    try {
      const packet = await api.post(`/api/battle/${state.sessionId}/action`, {
        actionType: action.actionType,
        index: action.index,
      });
      state.menu = packet.currentState.actionGroups.forcedSwitch ? "switch" : "root";
      applyPacket(packet);
    } catch (error) {
      state.busy = false;
      elements.message.textContent = error.message;
      updateTopControls();
      renderActionPanel();
    }
  }

  function showModeScreen() {
    state.autoplay = false;
    state.busy = false;
    state.sessionId = null;
    state.mode = null;
    state.packet = null;
    state.visibleState = null;
    state.menu = "root";
    elements.modeScreen.classList.remove("hidden");
    elements.winnerBanner.classList.add("hidden");
    elements.message.textContent = "Selecciona un modo para comenzar.";
    elements.statusPill.textContent = "Esperando inicio";
    renderActionPanel();
  }

  if (elements.difficulty) {
    elements.difficulty.addEventListener("change", () => {
      const hint = DIFFICULTY_HINTS[elements.difficulty.value] || "";
      if (elements.difficultyHint) elements.difficultyHint.textContent = hint;
    });
  }

  elements.startHuman.addEventListener("click", () => startBattle("human-vs-ai"));
  elements.startAi.addEventListener("click", () => startBattle("ai-vs-ai"));
  elements.newGame.addEventListener("click", showModeScreen);
  elements.next.addEventListener("click", requestAiStep);
  elements.toggle.addEventListener("click", () => {
    if (!state.packet || state.packet.over || state.busy) {
      return;
    }

    if (state.mode !== "ai-vs-ai") {
      return;
    }
    state.autoplay = !state.autoplay;
    updateTopControls();
    if (state.autoplay && !state.busy) {
      requestAiStep();
    }
  });

  renderActionPanel();
  updateTopControls();
  elements.message.textContent = "Selecciona un modo para comenzar.";
})();

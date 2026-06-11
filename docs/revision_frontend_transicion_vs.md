# Revision tecnica del frontend y transicion VS de inicio de combate

## Objetivo

Revisar el frontend actual en `frontend/` y documentar una animacion cinematica de transicion `VS` para el inicio de combate de Pokefisi.

La transicion debe funcionar como una capa superpuesta temporal. No debe modificar el DOM estructural de la pantalla de batalla, no debe mover HUDs, no debe alterar la cuadricula visual ni cambiar la posicion clasica GBA/NDS de los elementos ya definidos.

## Estado Actual Del Frontend

El frontend actual es una app Vite directa. El flujo activo es:

```text
frontend/index.html
  -> frontend/src/main.tsx
    -> frontend/src/styles.css
    -> frontend/src/lib/pokefisi/PokefisiApp.tsx
      -> frontend/src/lib/pokefisi/api.ts
      -> frontend/src/lib/pokefisi/data.ts
      -> frontend/src/lib/pokefisi/assets.ts
      -> frontend/src/lib/pokefisi/components.tsx
```

Archivos relevantes para esta mejora:

| Archivo | Estado | Uso |
|---|---|---|
| `frontend/src/lib/pokefisi/PokefisiApp.tsx` | Activo | Controla pantallas, inicio de sesion, `IntroScreen`, `BattleScreen` y reproduccion de frames |
| `frontend/src/styles.css` | Activo | Contiene tokens, utilidades pixel, animaciones actuales y CSS global |
| `frontend/src/lib/pokefisi/components.tsx` | Activo | Contiene `Pokeball`, `PixelPanel`, `PixelButton`, HUDs y componentes visuales |
| `frontend/src/lib/pokefisi/assets.ts` | Activo | Contiene fondos Gen 6 de Pokemon Showdown |

No existe `app.js` en el flujo actual. Cualquier implementacion debe hacerse sobre componentes `.tsx` y `styles.css`.

## Verificacion Ejecutada

### Build

Comando ejecutado:

```bash
npm run build
```

Resultado:

```text
vite v7.3.5 building client environment for production...
33 modules transformed.
dist/index.html
dist/assets/index-*.css
dist/assets/index-*.js
built in 680ms
```

Conclusion: el frontend compila correctamente.

### Lint

Comando ejecutado:

```bash
npm run lint
```

Resultado: finalizo sin errores visibles.

Conclusion: el frontend actual pasa lint.

## Restriccion Fundamental

La transicion `VS` debe ser un overlay visual:

- No reemplaza `BattleScreen`.
- No modifica el markup interno del campo de batalla.
- No altera HUDs, barras de vida, sprites, plataformas ni panel de acciones.
- No cambia el posicionamiento GBA/NDS actual.
- Se monta encima de la pantalla ya instanciada.
- Se desmonta despues de `4000ms`.
- Al desaparecer, revela el combate cargado debajo.

## Punto De Integracion Recomendado

El flujo actual tiene esta secuencia:

```text
MenuScreen
  -> Human vs IA
    -> SelectScreen
      -> Confirmar equipo
        -> startBattle(...)
        -> IntroScreen
        -> BattleScreen

MenuScreen
  -> IA vs IA
    -> startBattle(...)
    -> IntroScreen
    -> BattleScreen
```

La animacion solicitada debe ocurrir despues de que la batalla ya tenga datos de backend y antes de que los Pokemon empiecen a salir al campo. Para respetar la restriccion de overlay, la opcion mas segura es:

1. Instanciar `BattleScreen` detras del overlay.
2. Mostrar `BattleTransitionOverlay` encima durante `4000ms`.
3. No tocar el layout interno de batalla.
4. Iniciar o revelar la reproduccion real del combate cuando el overlay termine.

Si se desea conservar `IntroScreen`, el overlay debe mostrarse al entrar a `BattleScreen`. Si se desea que ocurra inmediatamente despues del boton de inicio, `IntroScreen` debe omitirse o convertirse en parte del mismo flujo visual, pero eso ya seria una decision de producto porque cambia el pacing actual.

## Contrato Del Componente

Nombre recomendado:

```text
BattleTransitionOverlay
```

Ubicacion recomendada:

```text
frontend/src/lib/pokefisi/BattleTransitionOverlay.tsx
```

Props recomendadas:

```ts
type BattleTransitionOverlayProps = {
  playerName: string;
  enemyName: string;
  playerTrainerSrc: string;
  enemyTrainerSrc: string;
  onDone: () => void;
};
```

Reglas:

- `onDone` se ejecuta exactamente despues de `4000ms`.
- El componente se renderiza con `position: absolute` o `fixed`, `inset: 0`, `z-index` superior a HUDs y controles.
- `pointer-events: auto` mientras esta activo para bloquear clicks accidentales.
- Al final de la animacion, el padre lo desmonta.
- No debe leer ni modificar estado de combate, HP, acciones o party.

## Estructura Del Componente

```tsx
import { useEffect } from "react";
import { Pokeball } from "./components";

type BattleTransitionOverlayProps = {
  playerName: string;
  enemyName: string;
  playerTrainerSrc: string;
  enemyTrainerSrc: string;
  onDone: () => void;
};

export function BattleTransitionOverlay({
  playerName,
  enemyName,
  playerTrainerSrc,
  enemyTrainerSrc,
  onDone,
}: BattleTransitionOverlayProps) {
  useEffect(() => {
    const timer = window.setTimeout(onDone, 4000);
    return () => window.clearTimeout(timer);
  }, [onDone]);

  return (
    <div className="vs-overlay" aria-hidden="true">
      <div className="vs-eclipse" />

      <div className="vs-pokeball-burst">
        <Pokeball size={104} state="alive" />
      </div>

      <div className="vs-diagonal vs-diagonal-player" />
      <div className="vs-diagonal vs-diagonal-enemy" />
      <div className="vs-speed-lines vs-speed-lines-player" />
      <div className="vs-speed-lines vs-speed-lines-enemy" />

      <div className="vs-trainer vs-trainer-player">
        <img src={playerTrainerSrc} alt="" />
      </div>

      <div className="vs-trainer vs-trainer-enemy">
        <img src={enemyTrainerSrc} alt="" />
      </div>

      <div className="vs-name vs-name-player">{playerName}</div>
      <div className="vs-name vs-name-enemy">{enemyName}</div>

      <div className="vs-logo">VS</div>
      <div className="vs-final-flash" />
    </div>
  );
}
```

## Timeline Tecnico

| Fase | Tiempo | Elementos | Comportamiento |
|---|---:|---|---|
| Eclipse | `0.0s - 0.8s` | `vs-eclipse`, `vs-pokeball-burst`, `vs-logo` | Oscurece menu/batalla, Pokeball escala desde centro y revela `VS` |
| Choque de entrenadores | `0.8s - 2.0s` | diagonales, speed lines, trainers | Division diagonal rojo/azul, entrenadores entran desde esquinas opuestas |
| Tension | `2.0s - 3.2s` | trainers, names, logo | Zoom dramatico, nombres aparecen con destello, `VS` palpita |
| Revelacion | `3.2s - 4.0s` | final flash, overlay | Giro/destello expansivo, fade blanco corto y opacity a 0 |

## CSS Y Keyframes

Agregar al final de `frontend/src/styles.css`.

```css
/* Battle VS transition overlay */
.vs-overlay {
  position: absolute;
  inset: 0;
  z-index: 80;
  overflow: hidden;
  pointer-events: auto;
  background: transparent;
  animation: vs-overlay-out 4s linear forwards;
  isolation: isolate;
}

.vs-eclipse {
  position: absolute;
  inset: 0;
  background: oklch(0.08 0.03 260 / 0.92);
  animation: vs-eclipse 4s linear forwards;
}

.vs-pokeball-burst {
  position: absolute;
  left: 50%;
  top: 50%;
  z-index: 6;
  transform: translate(-50%, -50%) scale(0);
  filter: drop-shadow(0 0 18px white);
  animation: vs-pokeball-burst 800ms cubic-bezier(0.2, 0.9, 0.25, 1.25) forwards;
}

.vs-logo {
  position: absolute;
  left: 50%;
  top: 50%;
  z-index: 20;
  transform: translate(-50%, -50%) scale(0.2) rotate(-8deg);
  font-family: var(--font-pixel);
  font-size: clamp(2.4rem, 8vw, 6rem);
  letter-spacing: -0.08em;
  color: white;
  text-shadow:
    0 0 8px white,
    0 0 22px var(--color-pkyellow),
    5px 5px 0 var(--color-ink),
    -5px -5px 0 var(--color-pkred);
  opacity: 0;
  animation: vs-logo 4s cubic-bezier(0.2, 0.8, 0.2, 1) forwards;
}

.vs-diagonal {
  position: absolute;
  inset: -18%;
  opacity: 0;
  z-index: 2;
  transform: translateX(0) skewX(-18deg);
}

.vs-diagonal-player {
  clip-path: polygon(0 30%, 58% 0, 42% 100%, 0 100%);
  background: linear-gradient(135deg, #ff243a 0%, #b60f2d 55%, #4d0716 100%);
  animation: vs-panel-player 4s ease forwards;
}

.vs-diagonal-enemy {
  clip-path: polygon(58% 0, 100% 0, 100% 72%, 42% 100%);
  background: linear-gradient(315deg, #1f7bff 0%, #1550c8 55%, #06143f 100%);
  animation: vs-panel-enemy 4s ease forwards;
}

.vs-speed-lines {
  position: absolute;
  inset: 0;
  z-index: 3;
  opacity: 0;
  background-image: repeating-linear-gradient(
    -18deg,
    transparent 0 18px,
    oklch(1 0 0 / 0.24) 18px 22px,
    transparent 22px 44px
  );
  animation: vs-speed-lines 4s linear forwards;
}

.vs-speed-lines-player {
  clip-path: polygon(0 34%, 58% 0, 42% 100%, 0 100%);
}

.vs-speed-lines-enemy {
  clip-path: polygon(58% 0, 100% 0, 100% 68%, 42% 100%);
  transform: scaleX(-1);
}

.vs-trainer {
  position: absolute;
  z-index: 12;
  opacity: 0;
  filter: drop-shadow(8px 8px 0 oklch(0.08 0.03 260 / 0.5));
}

.vs-trainer img {
  display: block;
  height: clamp(9rem, 30vh, 17rem);
  image-rendering: pixelated;
}

.vs-trainer-player {
  left: 7%;
  bottom: 7%;
  transform: translate(-45%, 35%) scale(0.86);
  animation: vs-trainer-player 4s cubic-bezier(0.2, 0.9, 0.2, 1) forwards;
}

.vs-trainer-player img {
  transform: scaleX(-1);
}

.vs-trainer-enemy {
  right: 7%;
  top: 7%;
  transform: translate(45%, -35%) scale(0.86);
  animation: vs-trainer-enemy 4s cubic-bezier(0.2, 0.9, 0.2, 1) forwards;
}

.vs-name {
  position: absolute;
  z-index: 18;
  opacity: 0;
  padding: 0.55rem 0.85rem;
  border: 4px solid white;
  background: oklch(0.1 0.03 260 / 0.72);
  color: white;
  font-family: var(--font-pixel);
  font-size: clamp(0.65rem, 2vw, 1.1rem);
  text-transform: uppercase;
  text-shadow: 3px 3px 0 var(--color-ink);
  box-shadow: 0 0 18px oklch(1 0 0 / 0.32);
  animation: vs-name-pop 4s ease forwards;
}

.vs-name-player {
  left: 8%;
  bottom: 34%;
}

.vs-name-enemy {
  right: 8%;
  top: 34%;
}

.vs-final-flash {
  position: absolute;
  inset: 0;
  z-index: 90;
  background: white;
  opacity: 0;
  pointer-events: none;
  animation: vs-final-flash 4s ease forwards;
}

@keyframes vs-eclipse {
  0% { opacity: 0; }
  8% { opacity: 0.92; }
  80% { opacity: 0.92; }
  100% { opacity: 0; }
}

@keyframes vs-pokeball-burst {
  0% { opacity: 0; transform: translate(-50%, -50%) scale(0.05) rotate(-90deg); }
  58% { opacity: 1; transform: translate(-50%, -50%) scale(1.25) rotate(16deg); }
  78% { opacity: 1; transform: translate(-50%, -50%) scale(1.05) rotate(0); }
  100% { opacity: 0; transform: translate(-50%, -50%) scale(2.2) rotate(35deg); }
}

@keyframes vs-logo {
  0%, 14% { opacity: 0; transform: translate(-50%, -50%) scale(0.2) rotate(-8deg); }
  20% { opacity: 1; transform: translate(-50%, -50%) scale(1.16) rotate(-8deg); }
  30% { opacity: 1; transform: translate(-50%, -50%) scale(1) rotate(-8deg); }
  56% { opacity: 1; transform: translate(-50%, -50%) scale(1.12) rotate(-6deg); }
  70% { opacity: 1; transform: translate(-50%, -50%) scale(1.22) rotate(4deg); }
  83% { opacity: 1; transform: translate(-50%, -50%) scale(1.36) rotate(18deg); }
  100% { opacity: 0; transform: translate(-50%, -50%) scale(3.4) rotate(90deg); }
}

@keyframes vs-panel-player {
  0%, 20% { opacity: 0; transform: translateX(-90%) skewX(-18deg); }
  34% { opacity: 1; transform: translateX(0) skewX(-18deg); }
  80% { opacity: 1; transform: translateX(0) skewX(-18deg); }
  100% { opacity: 0; transform: translateX(-12%) scale(1.08) skewX(-18deg); }
}

@keyframes vs-panel-enemy {
  0%, 20% { opacity: 0; transform: translateX(90%) skewX(-18deg); }
  34% { opacity: 1; transform: translateX(0) skewX(-18deg); }
  80% { opacity: 1; transform: translateX(0) skewX(-18deg); }
  100% { opacity: 0; transform: translateX(12%) scale(1.08) skewX(-18deg); }
}

@keyframes vs-speed-lines {
  0%, 22% { opacity: 0; background-position: 0 0; }
  35% { opacity: 0.42; }
  78% { opacity: 0.35; background-position: 240px 0; }
  100% { opacity: 0; background-position: 360px 0; }
}

@keyframes vs-trainer-player {
  0%, 22% { opacity: 0; transform: translate(-45%, 35%) scale(0.86); }
  38% { opacity: 1; transform: translate(0, 0) scale(0.95); }
  60% { opacity: 1; transform: translate(2%, -2%) scale(1.12); }
  80% { opacity: 1; transform: translate(3%, -3%) scale(1.2); }
  100% { opacity: 0; transform: translate(0, 0) scale(1.35); }
}

@keyframes vs-trainer-enemy {
  0%, 22% { opacity: 0; transform: translate(45%, -35%) scale(0.86); }
  38% { opacity: 1; transform: translate(0, 0) scale(0.95); }
  60% { opacity: 1; transform: translate(-2%, 2%) scale(1.12); }
  80% { opacity: 1; transform: translate(-3%, 3%) scale(1.2); }
  100% { opacity: 0; transform: translate(0, 0) scale(1.35); }
}

@keyframes vs-name-pop {
  0%, 48% { opacity: 0; transform: translateY(12px) scale(0.88); filter: brightness(1); }
  55% { opacity: 1; transform: translateY(0) scale(1.08); filter: brightness(1.8); }
  64% { opacity: 1; transform: translateY(0) scale(1); filter: brightness(1); }
  82% { opacity: 1; transform: translateY(0) scale(1); }
  100% { opacity: 0; transform: translateY(-8px) scale(1.12); }
}

@keyframes vs-final-flash {
  0%, 78% { opacity: 0; }
  84% { opacity: 0.92; }
  92% { opacity: 0.38; }
  100% { opacity: 0; }
}

@keyframes vs-overlay-out {
  0%, 88% { opacity: 1; }
  100% { opacity: 0; pointer-events: none; }
}

@media (prefers-reduced-motion: reduce) {
  .vs-overlay,
  .vs-eclipse,
  .vs-pokeball-burst,
  .vs-logo,
  .vs-diagonal,
  .vs-speed-lines,
  .vs-trainer,
  .vs-name,
  .vs-final-flash {
    animation-duration: 1ms !important;
    animation-delay: 0ms !important;
  }
}
```

## Logica De Desmontaje Tras 4 Segundos

El componente no debe desmontarse a si mismo sin avisar al padre. Debe emitir `onDone` y dejar que el padre quite el overlay.

Ejemplo de estado en el componente padre:

```tsx
const [showVsTransition, setShowVsTransition] = useState(true);

{showVsTransition && (
  <BattleTransitionOverlay
    playerName={mode === "ai" ? "IA 1" : "SubSonicoYT"}
    enemyName="IA Rival"
    playerTrainerSrc={PLAYER_TRAINER_BACK}
    enemyTrainerSrc={ENEMY_TRAINER}
    onDone={() => setShowVsTransition(false)}
  />
)}
```

Si se integra dentro de `BattleScreen`, debe renderizarse como ultimo hijo del contenedor principal para quedar encima:

```tsx
<div className="relative h-full pixel-border overflow-hidden rounded-md ...">
  {/* layout actual de batalla sin cambios */}

  {showVsTransition && (
    <BattleTransitionOverlay
      playerName={backendState.player.trainer}
      enemyName={backendState.enemy.trainer}
      playerTrainerSrc={PLAYER_TRAINER_BACK}
      enemyTrainerSrc={ENEMY_TRAINER}
      onDone={() => setShowVsTransition(false)}
    />
  )}
</div>
```

## Evitar Que Los Pokemon Salgan Antes Del Overlay

Para cumplir que la transicion termina justo antes de que los Pokemon salgan al campo, hay que evitar que `applyResponse(initialResponse)` reproduzca frames mientras el overlay sigue visible.

El flujo recomendado es:

```tsx
const [showVsTransition, setShowVsTransition] = useState(true);
const introRan = useRef(false);

useEffect(() => {
  if (showVsTransition) return;
  if (introRan.current) return;
  introRan.current = true;
  applyResponse(initialResponse);
}, [showVsTransition]);
```

Con esto:

- `BattleScreen` ya esta montado detras.
- El overlay cubre toda la pantalla por `4000ms`.
- Los frames de entrada de Pokemon comienzan despues de `onDone`.
- La estructura visual del combate no se toca.

## Integracion Con El Flujo Actual

### Human vs IA

Punto de activacion recomendado:

```text
SelectScreen
  -> Confirmar equipo
  -> startBattle(...)
  -> setScreen("battle")
  -> BattleScreen montado detras
  -> BattleTransitionOverlay 4s
  -> applyResponse(initialResponse)
```

Si se conserva `IntroScreen`, entonces:

```text
SelectScreen
  -> Confirmar equipo
  -> startBattle(...)
  -> IntroScreen
  -> BattleScreen montado detras
  -> BattleTransitionOverlay 4s
  -> applyResponse(initialResponse)
```

### IA vs IA

Punto de activacion recomendado:

```text
MenuScreen
  -> IA vs IA
  -> startBattle(...)
  -> BattleScreen montado detras
  -> BattleTransitionOverlay 4s
  -> applyResponse(initialResponse)
```

## Relacion Con El IntroScreen Actual

`IntroScreen` actualmente muestra entrenadores, mensajes y una entrada previa al combate. La transicion VS propuesta puede convivir con ella, pero son recursos de pacing similares.

Opciones validas:

| Opcion | Resultado | Riesgo |
|---|---|---|
| Conservar `IntroScreen` y luego mostrar VS | Transicion mas larga, no rompe nada | Puede sentirse redundante |
| Reemplazar visualmente `IntroScreen` por VS | Flujo mas cinematografico | Cambia pacing actual |
| Mostrar VS solo al entrar a `BattleScreen` | Respeta overlay y no toca layout de combate | Recomendado |

La opcion recomendada es mostrar VS al entrar a `BattleScreen`, como overlay encima del layout ya instanciado.

## Criterios De Aceptacion

La transicion se considera correcta si cumple:

- Dura exactamente `4000ms` antes de llamar `onDone`.
- Se renderiza como overlay absoluto sobre la batalla.
- No modifica HUDs, grid, sprites, posiciones ni paneles del combate.
- No cambia el DOM interno de `BattleScreen`, salvo agregar el overlay como ultimo hijo.
- Bloquea clicks durante la animacion.
- Desaparece con fade final y `pointer-events: none`.
- La batalla queda visible debajo al terminar.
- Los Pokemon no reproducen su entrada antes de que termine la transicion.
- `npm run build` pasa.
- `npm run lint` pasa.

## Riesgos Y Mitigaciones

| Riesgo | Mitigacion |
|---|---|
| Los frames de batalla empiezan detras del overlay | Retardar `applyResponse(initialResponse)` hasta `onDone` |
| El overlay bloquea permanentemente clicks | Desmontarlo desde el padre y usar `pointer-events: none` al final |
| Se altera el layout GBA/NDS | Renderizar overlay como ultimo hijo absoluto sin tocar elementos existentes |
| La animacion se siente demasiado larga con `IntroScreen` | Evaluar conservar solo una de las dos transiciones |
| Problemas de accesibilidad por movimiento | Agregar `prefers-reduced-motion` |
| Z-index insuficiente | Usar `z-index: 80` o mayor que HUDs/modal actuales |

## Resumen Tecnico

La mejora debe implementarse como un componente aislado `BattleTransitionOverlay`. Su responsabilidad es puramente visual: cubrir la pantalla, reproducir la secuencia `VS` durante cuatro segundos y desmontarse.

La batalla debe estar cargada detras, pero la reproduccion de frames iniciales debe esperar a que el overlay termine. Asi se cumple que la transicion revela el layout de batalla ya definido sin alterar su estructura ni afectar la jugabilidad actual.

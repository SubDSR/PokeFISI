import { useEffect, useRef } from "react";
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
  // Ref para que el timer siempre llame a la versión más reciente de onDone
  // sin reiniciar el temporizador si el padre re-renderiza.
  const onDoneRef = useRef(onDone);
  useEffect(() => { onDoneRef.current = onDone; });

  useEffect(() => {
    const timer = window.setTimeout(() => onDoneRef.current(), 4000);
    return () => window.clearTimeout(timer);
  }, []);

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

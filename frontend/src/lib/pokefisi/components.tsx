import type { ReactNode, ButtonHTMLAttributes } from "react";
import { TYPE_LABEL, type PokeType, type Pokemon, type Move } from "./data";

/* ============ Pixel primitives ============ */

export function PixelPanel({
  children,
  className = "",
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <div className={`pixel-panel ${className}`}>
      <div className="scanlines rounded-md">{children}</div>
    </div>
  );
}

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "secondary" | "ghost" | "danger" | "gold";
  size?: "sm" | "md" | "lg";
};

export function PixelButton({
  variant = "primary",
  size = "md",
  className = "",
  children,
  disabled,
  ...rest
}: ButtonProps) {
  const palette: Record<string, string> = {
    primary: "bg-pkyellow text-ink",
    secondary: "bg-[oklch(0.78_0.1_240)] text-ink",
    ghost: "bg-cream text-ink",
    danger: "bg-pkred text-cream",
    gold: "bg-gold text-ink",
  };
  const sizes: Record<string, string> = {
    sm: "px-3 py-1.5 text-xs",
    md: "px-5 py-3 text-xs",
    lg: "px-8 py-5 text-sm",
  };
  return (
    <button
      {...rest}
      disabled={disabled}
      className={`font-pixel ${sizes[size]} ${palette[variant]} pixel-border-blue btn-press
        ${disabled ? "opacity-50 cursor-not-allowed" : "hover:-translate-y-0.5 active:translate-y-1 active:shadow-none cursor-pointer"}
        ${className}`}
    >
      {children}
    </button>
  );
}

export function TypeBadge({ type, className = "" }: { type: PokeType; className?: string }) {
  return (
    <span
      className={`type-${type} inline-block px-2 py-0.5 text-[10px] font-pixel rounded-sm border-2 border-ink ${className}`}
    >
      {TYPE_LABEL[type].toUpperCase()}
    </span>
  );
}

/* ============ HP bar ============ */

export function HPBar({
  hp,
  hpMax,
  showNumber = false,
  width = "w-44",
}: {
  hp: number;
  hpMax: number;
  showNumber?: boolean;
  width?: string;
}) {
  const pct = Math.max(0, Math.min(100, (hp / hpMax) * 100));
  const color =
    pct > 50 ? "bg-hp-high" : pct > 20 ? "bg-hp-mid" : "bg-hp-low";
  return (
    <div className="flex items-center gap-2">
      <span className="font-pixel text-[9px] text-pkblue-deep">PS</span>
      <div className={`${width} h-3 bg-ink/80 border-2 border-ink rounded-sm overflow-hidden p-[1px]`}>
        <div
          className={`hp-fill h-full ${color} rounded-sm`}
          style={{ width: `${pct}%` }}
        />
      </div>
      {showNumber && (
        <span className="font-pixel text-[10px] text-ink whitespace-nowrap">
          {Math.max(0, Math.round(hp))}/{hpMax}
        </span>
      )}
    </div>
  );
}

/* ============ Pokemon HUD ============ */

export function PokemonHUD({
  pokemon,
  side,
}: {
  pokemon: Pokemon;
  side: "player" | "enemy";
}) {
  return (
    <div className="pixel-hud px-4 py-2 min-w-[260px]">
      <div className="flex items-baseline justify-between gap-3">
        <span className="font-pixel text-xs text-ink truncate">
          {pokemon.name.toUpperCase()}
        </span>
        <span className="font-pixel text-[10px] text-ink">
          Nv{pokemon.level}
        </span>
      </div>
      <div className="mt-1">
        <HPBar
          hp={pokemon.hp}
          hpMax={pokemon.hpMax}
          showNumber={side === "player"}
          width="w-40"
        />
      </div>
    </div>
  );
}

/* ============ Team poke balls ============ */

export function TeamPokeballRow({
  team,
  align = "left",
}: {
  team: Pokemon[];
  align?: "left" | "right";
}) {
  return (
    <div className={`flex gap-1.5 ${align === "right" ? "justify-end" : "justify-start"}`}>
      {team.map((p, i) => (
        <Pokeball key={i} state={p.fainted ? "fainted" : "alive"} />
      ))}
    </div>
  );
}

export function Pokeball({
  state = "alive",
  size = 22,
}: {
  state?: "alive" | "fainted" | "active";
  size?: number;
}) {
  const opacity = state === "fainted" ? 0.3 : 1;
  const filter = state === "fainted" ? "grayscale(1)" : "none";
  return (
    <div
      style={{ width: size, height: size, opacity, filter }}
      className={state === "active" ? "anim-float" : ""}
      aria-label={state}
    >
      <svg viewBox="0 0 20 20" className="w-full h-full" shapeRendering="crispEdges">
        <circle cx="10" cy="10" r="9" fill="#fff" stroke="#0d0d24" strokeWidth="2" />
        <path d="M1 10 A9 9 0 0 1 19 10 Z" fill="#e63946" stroke="#0d0d24" strokeWidth="2" />
        <rect x="1" y="9" width="18" height="2" fill="#0d0d24" />
        <circle cx="10" cy="10" r="3" fill="#fff" stroke="#0d0d24" strokeWidth="2" />
      </svg>
    </div>
  );
}

/* ============ Move button ============ */

export function MoveButton({
  move,
  onClick,
  onHover,
  disabled,
}: {
  move: Move;
  onClick?: () => void;
  onHover?: () => void;
  disabled?: boolean;
}) {
  const noPP = move.pp <= 0;
  return (
    <button
      disabled={disabled || noPP}
      onClick={onClick}
      onMouseEnter={onHover}
      className={`type-${move.type} font-pixel text-left px-3 py-2 pixel-border-blue btn-press
        ${disabled || noPP ? "grayscale opacity-50 cursor-not-allowed" : "hover:-translate-y-0.5 active:translate-y-1 active:shadow-none cursor-pointer"}`}
    >
      <div className="text-[10px] leading-tight">{move.name}</div>
      <div className="flex items-center justify-between mt-2 text-[8px]">
        <span className="bg-ink/70 px-1.5 py-0.5 rounded-sm">
          {TYPE_LABEL[move.type]}
        </span>
        <span>PP {move.pp}/{move.ppMax}</span>
      </div>
    </button>
  );
}

/* ============ Message panel ============ */

export function MessagePanel({
  text,
  className = "",
}: {
  text: string;
  className?: string;
}) {
  return (
    <div className={`pixel-border bg-cream px-6 py-4 min-h-[110px] flex items-center ${className}`}>
      <p className="font-body-pixel text-2xl text-ink leading-tight">{text}</p>
    </div>
  );
}

/* ============ Pokemon Card (selection) ============ */

export function PokemonCard({
  pokemon,
  selected,
  disabled,
  onClick,
  compact = false,
}: {
  pokemon: Pokemon;
  selected?: boolean;
  disabled?: boolean;
  onClick?: () => void;
  compact?: boolean;
}) {
  if (compact) {
    return (
      <button
        type="button"
        disabled={disabled && !selected}
        onClick={onClick}
        title={`${pokemon.name} • Nv${pokemon.level}`}
        className={`relative pixel-border bg-cream p-1 text-left transition-transform flex flex-col items-center
          ${disabled && !selected ? "opacity-40 cursor-not-allowed" : "hover:scale-[1.06] cursor-pointer"}
          ${selected ? "ring-4 ring-pkyellow" : ""}`}
      >
        {selected && (
          <div className="absolute -top-2 -right-2 z-10">
            <Pokeball state="active" size={16} />
          </div>
        )}
        <div className="flex items-center justify-center w-full h-12 bg-[oklch(0.95_0.04_140)] border-2 border-ink/60 rounded-sm">
          <img
            src={pokemon.sprite}
            alt={pokemon.name}
            className="max-h-11 max-w-full"
            style={{ imageRendering: "pixelated" }}
            loading="lazy"
          />
        </div>
        <span className="font-pixel text-[7px] text-ink truncate w-full text-center mt-1 leading-tight">
          {pokemon.name}
        </span>
      </button>
    );
  }
  return (
    <button
      type="button"
      disabled={disabled && !selected}
      onClick={onClick}
      className={`relative pixel-panel bg-cream p-3 text-left transition-transform
        ${disabled && !selected ? "opacity-40 cursor-not-allowed" : "hover:scale-[1.03] cursor-pointer"}
        ${selected ? "ring-4 ring-pkyellow ring-offset-2 ring-offset-cream-dark" : ""}`}
    >
      {selected && (
        <div className="absolute -top-3 -right-3">
          <Pokeball state="active" size={28} />
        </div>
      )}
      <div className="flex items-center justify-center h-24 bg-[oklch(0.95_0.04_140)] border-2 border-ink/60 rounded-sm">
        <img
          src={pokemon.sprite}
          alt={pokemon.name}
          className="max-h-24 max-w-full"
          style={{ imageRendering: "pixelated" }}
          loading="lazy"
        />
      </div>
      <div className="mt-2 flex items-center justify-between">
        <span className="font-pixel text-[10px] text-ink truncate">{pokemon.name}</span>
        <span className="font-pixel text-[9px] text-ink-soft">Nv{pokemon.level}</span>
      </div>
      <div className="mt-1.5 flex gap-1 flex-wrap">
        {pokemon.types.map((t) => <TypeBadge key={t} type={t} />)}
      </div>
    </button>
  );
}

/* ============ Pokemon slot (party panel during battle) ============ */

export function PokemonSlot({
  pokemon,
  active,
  onClick,
}: {
  pokemon: Pokemon;
  active?: boolean;
  onClick?: () => void;
}) {
  const fainted = !!pokemon.fainted;
  const disabled = fainted || active;
  return (
    <button
      type="button"
      disabled={disabled}
      onClick={onClick}
      className={`w-full pixel-border bg-cream p-2 flex items-center gap-3 text-left btn-press
        ${disabled ? "opacity-50 cursor-not-allowed" : "hover:-translate-y-0.5 cursor-pointer"}
        ${active ? "ring-4 ring-pkyellow" : ""}`}
    >
      <div className="w-14 h-14 flex items-center justify-center bg-[oklch(0.93_0.04_140)] border-2 border-ink/60 rounded-sm shrink-0 overflow-hidden">
        <img
          src={pokemon.icon}
          alt={pokemon.name}
          className={`max-h-12 max-w-12 ${fainted ? "grayscale" : ""}`}
          style={{ imageRendering: "pixelated" }}
          loading="lazy"
          onError={(e) => {
            const img = e.currentTarget as HTMLImageElement;
            if (img.src !== pokemon.sprite) img.src = pokemon.sprite;
          }}
        />
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-baseline justify-between gap-2">
          <span className="font-pixel text-[10px] text-ink truncate">{pokemon.name}</span>
          <span className="font-pixel text-[9px] text-ink-soft">Nv{pokemon.level}</span>
        </div>
        <div className="mt-1">
          <HPBar hp={pokemon.hp} hpMax={pokemon.hpMax} showNumber width="w-32" />
        </div>
      </div>
    </button>
  );
}

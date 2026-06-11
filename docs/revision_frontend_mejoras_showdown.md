# Revision tecnica del frontend y mejoras visuales con Pokemon Showdown

## Objetivo

Revisar el frontend actual en `frontend/` y documentar como incorporar mejoras visuales usando recursos publicos de Pokemon Showdown, sin descargar assets, sin alojarlos localmente y sin modificar componentes que ya esten funcionando correctamente.

Este documento no aplica cambios de codigo. Sirve como guia tecnica para implementar las mejoras de forma segura y progresiva.

## Estado Actual Del Frontend

El frontend vigente es una aplicacion Vite directa. El flujo activo real es:

```text
frontend/index.html
  -> frontend/src/main.tsx
    -> frontend/src/styles.css
    -> frontend/src/lib/pokefisi/PokefisiApp.tsx
      -> frontend/src/lib/pokefisi/api.ts
      -> frontend/src/lib/pokefisi/data.ts
      -> frontend/src/lib/pokefisi/components.tsx
```

No existe `app.js` en el flujo actual. Cualquier referencia a `app.js` corresponde a una estructura anterior y no debe usarse para esta implementacion.

## Verificacion Ejecutada

### Build

Comando ejecutado:

```bash
npm run build
```

Resultado:

```text
vite v7.3.5 building client environment for production...
32 modules transformed.
dist/index.html
dist/assets/index-*.css
dist/assets/index-*.js
built in 689ms
```

Conclusion: el frontend compila correctamente.

### Lint

Comando ejecutado:

```bash
npm run lint
```

Resultado: finalizo sin errores visibles.

Conclusion: el frontend actual pasa lint en el estado revisado.

## Archivos Relevantes Para Las Mejoras

| Archivo | Uso actual | Accion recomendada |
|---|---|---|
| `frontend/src/lib/pokefisi/PokefisiApp.tsx` | Renderiza menu, selector, intro, batalla, frames y resultado | Agregar fondos de batalla y controlar nuevas fases de animacion aqui |
| `frontend/src/styles.css` | Define Tailwind source, tokens, utilidades pixel y animaciones | Agregar keyframes nuevos sin eliminar los existentes |
| `frontend/src/lib/pokefisi/data.ts` | Mapea DTOs del backend a modelo visual | Mantener uso de `spriteFrontUrl` y `spriteBackUrl`; no duplicar URLs si ya vienen del backend |
| `frontend/src/lib/pokefisi/components.tsx` | Componentes visuales reutilizables | No modificar salvo que se quiera reemplazar Pokeball SVG por sheet externo |
| `frontend/src/lib/pokefisi/api.ts` | Cliente HTTP hacia backend | No requiere cambios para assets visuales si el backend ya entrega sprites |

## Recursos Publicos De Pokemon Showdown

Todos los assets deben usarse directamente por URL desde `https://play.pokemonshowdown.com`. No deben descargarse, versionarse ni alojarse dentro de `frontend/`.

### Sprites Pokemon Animados

| URL | Uso recomendado |
|---|---|
| `https://play.pokemonshowdown.com/sprites/ani/{id}.gif` | Sprite frontal animado para enemigo |
| `https://play.pokemonshowdown.com/sprites/ani-back/{id}.gif` | Sprite trasero animado para jugador |
| `https://play.pokemonshowdown.com/sprites/gen5ani/{id}.gif` | Alternativa Gen 5 mas pixelada para enemigo |
| `https://play.pokemonshowdown.com/sprites/gen5ani-back/{id}.gif` | Alternativa Gen 5 trasera para jugador |

Donde `{id}` debe coincidir con el identificador en minusculas y sin espacios, por ejemplo:

```text
bulbasaur
charmander
nidoranf
```

Estado actual: el proyecto ya recibe `spriteFrontUrl` y `spriteBackUrl` desde backend y los mapea en `data.ts`. Esto confirma que `ani` y `ani-back` son las rutas correctas. No se recomienda cambiar esta parte si ya se esta mostrando correctamente.

### Pokeball Sheet Para Iconos De Equipo

Recursos disponibles:

| URL | Uso recomendado |
|---|---|
| `https://play.pokemonshowdown.com/sprites/gen5icons-pokeball-sheet.png` | Sheet Gen 5, equivalente visual a BW |
| `https://play.pokemonshowdown.com/sprites/gen6icons-pokeball-sheet.png` | Sheet Gen 6, variacion visual ligera |

Estado actual: en el frontend revisado, `TeamPokeballRow` usa el componente `Pokeball` con SVG inline dentro de `frontend/src/lib/pokefisi/components.tsx`. No se encontro una llamada activa a `bwicons-pokeball-sheet.png` en el flujo actual.

Recomendacion: mantener el SVG actual si ya se muestra correctamente. Solo cambiar a sheet si se busca fidelidad visual Pokemon Showdown y se acepta implementar sprites por coordenadas CSS.

### Fondos De Campo De Batalla Gen 6

Fondos disponibles:

```text
https://play.pokemonshowdown.com/sprites/gen6bgs/bg-meadow.jpg
https://play.pokemonshowdown.com/sprites/gen6bgs/bg-city.jpg
https://play.pokemonshowdown.com/sprites/gen6bgs/bg-forest.jpg
https://play.pokemonshowdown.com/sprites/gen6bgs/bg-beach.jpg
https://play.pokemonshowdown.com/sprites/gen6bgs/bg-desert.jpg
https://play.pokemonshowdown.com/sprites/gen6bgs/bg-icecave.jpg
https://play.pokemonshowdown.com/sprites/gen6bgs/bg-earthycave.jpg
https://play.pokemonshowdown.com/sprites/gen6bgs/bg-deepsea.jpg
```

Estos fondos pueden reemplazar el gradiente actual de la pantalla de batalla para dar mayor calidad visual y variedad.

## Revision De Animaciones Existentes

En `frontend/src/styles.css` ya existen:

| Clase | Estado | Uso |
|---|---|---|
| `.anim-shake` | Existente | Golpe/impacto |
| `.anim-flash` | Existente | Flash de impacto |
| `.anim-attack-player` | Existente | Ataque del jugador |
| `.anim-attack-enemy` | Existente | Ataque enemigo |
| `.anim-faint` | Existente | Salida simple por debilitamiento |
| `.anim-enter` | Existente | Entrada simple de Pokemon |
| `.anim-float` | Existente | Flotacion leve del sprite |

En `PokefisiApp.tsx`, el tipo actual de animacion es:

```ts
type Anim = {
  side: "player" | "enemy" | null;
  kind: "attack" | "hit" | "faint" | "enter" | null;
};
```

La reproduccion de frames se controla en `playFrames`, donde ya se detectan:

```ts
animation.type === "attack"
animation.type === "faint"
animation.type === "switch"
```

Conclusion: las mejoras deben extender este sistema, no reemplazarlo por completo.

## Principio De No Duplicar Trabajo

Si una mejora ya esta funcionando en el frontend actual, no debe modificarse salvo que el cambio sea estrictamente incremental.

| Area | Estado actual | Decision recomendada |
|---|---|---|
| Sprites `ani` y `ani-back` | Ya usados por backend/frontend | Mantener |
| Conexion backend para Pokemon | Ya implementada con `GET /api/pokemon` | Mantener |
| Animacion base de entrada | Existe `.anim-enter` | Extender opcionalmente, no eliminar |
| Animacion base de faint | Existe `.anim-faint` | Extender opcionalmente, no eliminar |
| Pokeball de equipo | SVG inline funcional | Mantener salvo decision visual explicita |
| `app.js` | No existe en flujo actual | No usar |

## Mejora 1: Centralizar URLs De Pokemon Showdown

### Objetivo

Documentar y centralizar URLs publicas sin mover assets al repositorio.

### Archivo recomendado

`frontend/src/lib/pokefisi/data.ts` o un archivo nuevo pequeno:

```text
frontend/src/lib/pokefisi/assets.ts
```

### Enfoque recomendado

Usar constantes solo para fondos y alternativas. Para sprites de Pokemon, conservar las URLs recibidas desde el backend.

Ejemplo conceptual:

```ts
export const SHOWDOWN_BATTLE_BACKGROUNDS = [
  "https://play.pokemonshowdown.com/sprites/gen6bgs/bg-meadow.jpg",
  "https://play.pokemonshowdown.com/sprites/gen6bgs/bg-city.jpg",
  "https://play.pokemonshowdown.com/sprites/gen6bgs/bg-forest.jpg",
  "https://play.pokemonshowdown.com/sprites/gen6bgs/bg-beach.jpg",
  "https://play.pokemonshowdown.com/sprites/gen6bgs/bg-desert.jpg",
  "https://play.pokemonshowdown.com/sprites/gen6bgs/bg-icecave.jpg",
  "https://play.pokemonshowdown.com/sprites/gen6bgs/bg-earthycave.jpg",
  "https://play.pokemonshowdown.com/sprites/gen6bgs/bg-deepsea.jpg",
] as const;
```

No recomendado:

- Descargar fondos a `public/`.
- Crear copias locales en `src/assets/`.
- Hardcodear sprites Pokemon en el frontend si ya vienen del backend.

## Mejora 2: Fondos De Batalla Gen 6

### Estado actual

La pantalla de batalla usa un fondo de gradiente en `PokefisiApp.tsx`:

```tsx
<div className="relative h-full pixel-border overflow-hidden rounded-md bg-gradient-to-b ...">
```

### Opcion A: fondo aleatorio al iniciar batalla

Esta opcion es simple y no requiere cambios en backend.

Puntos de implementacion:

- Agregar un estado `battleBackgroundUrl` dentro de `BattleScreen`.
- Inicializarlo una vez por sesion con `useState(() => pickRandomBackground())`.
- Aplicarlo como `backgroundImage` al contenedor principal de batalla.
- Mantener un overlay de gradiente para preservar contraste de HUD y barra inferior.

Ejemplo conceptual:

```tsx
const [battleBackgroundUrl] = useState(() => pickRandomBattleBackground());

<div
  className="relative h-full pixel-border overflow-hidden rounded-md bg-cover bg-center"
  style={{ backgroundImage: `url(${battleBackgroundUrl})` }}
>
  <div className="absolute inset-0 bg-gradient-to-b from-white/10 via-transparent to-ink/20" />
</div>
```

### Opcion B: fondo por tipo del Pokemon activo del jugador

Esta opcion da coherencia tematica, pero cambia el fondo cuando cambia el activo si no se congela al inicio.

Mapeo recomendado:

| Tipo | Fondo |
|---|---|
| `grass`, `bug`, `poison` | `bg-forest.jpg` |
| `water` | `bg-beach.jpg` o `bg-deepsea.jpg` |
| `fire`, `ground`, `rock` | `bg-desert.jpg` o `bg-earthycave.jpg` |
| `ice` | `bg-icecave.jpg` |
| `electric`, `normal`, `fighting`, `psychic`, `steel` | `bg-city.jpg` |
| fallback | `bg-meadow.jpg` |

Recomendacion: seleccionar el fondo segun el primer Pokemon activo al iniciar la batalla y mantenerlo fijo durante la sesion para evitar cambios visuales bruscos.

## Mejora 3: Entrada Del Pokemon Con Pokeball Y Flash

### Objetivo

Mejorar el evento `switch-in` sin romper el sistema actual de frames.

### Estado actual

Cuando el backend envia `animation.type === "switch"`, `PokefisiApp.tsx` aplica:

```ts
setAnim({ side, kind: "enter" });
await delay(650);
```

Y CSS aplica:

```css
.anim-enter { animation: enter-pokemon 450ms cubic-bezier(0.34, 1.56, 0.64, 1); }
```

### Mejora solicitada

Entrada total aproximada: `800ms`.

Fases:

1. Pokeball cae desde arriba: `translateY(-60px)` a `0` con rebote.
2. Flash blanco simulando apertura.
3. Sprite aparece escalando de `0.2` a `1.0` con overshoot leve.

### Implementacion recomendada

No eliminar `.anim-enter`. Agregar una nueva clase, por ejemplo:

```css
.anim-switch-in-deluxe { ... }
.anim-switch-ball-drop { ... }
.anim-switch-flash { ... }
```

En `PokefisiApp.tsx`, extender el tipo `Anim` solo si se implementa esta mejora:

```ts
type AnimKind = "attack" | "hit" | "faint" | "enter" | "switch-in" | null;
```

Luego, para `animation.type === "switch"`, usar `switch-in` en lugar de `enter` solo cuando la nueva animacion este completa.

### CSS conceptual

```css
@keyframes pokeball-drop {
  0% { opacity: 0; transform: translateY(-60px) scale(0.9); }
  70% { opacity: 1; transform: translateY(4px) scale(1.05); }
  100% { opacity: 1; transform: translateY(0) scale(1); }
}

@keyframes pokeball-open-flash {
  0%, 100% { opacity: 0; transform: scale(0.8); }
  40% { opacity: 0.9; transform: scale(1.3); }
}

@keyframes pokemon-switch-in {
  0% { opacity: 0; transform: scale(0.2) translateY(10px); }
  70% { opacity: 1; transform: scale(1.08) translateY(-4px); }
  100% { opacity: 1; transform: scale(1) translateY(0); }
}
```

### Consideracion importante

El componente `Pokeball` actual es SVG y puede reutilizarse para la fase de caida. No es necesario cambiar a sheet de Pokemon Showdown para esta mejora.

## Mejora 4: Salida Por Debilitamiento Con Shake Y Caida

### Estado actual

`styles.css` ya tiene:

```css
@keyframes faint {
  0% { opacity: 1; transform: translateY(0); }
  100% { opacity: 0; transform: translateY(40px); }
}

.anim-faint { animation: faint 700ms ease forwards; }
```

Esto ya cubre parte del requerimiento: caida hacia abajo con reduccion de opacidad en `700ms`.

### Mejora solicitada

Antes de caer, agregar un temblor horizontal 3 veces en aproximadamente `200ms`.

### Implementacion recomendada

No reemplazar directamente `.anim-faint` si ya funciona. Agregar una variante:

```css
.anim-faint-enhanced { animation: faint-enhanced 700ms ease forwards; }
```

CSS conceptual:

```css
@keyframes faint-enhanced {
  0% { opacity: 1; transform: translateX(0) translateY(0); }
  8% { transform: translateX(-5px) translateY(0); }
  16% { transform: translateX(5px) translateY(0); }
  24% { transform: translateX(-4px) translateY(0); }
  30% { opacity: 1; transform: translateX(0) translateY(0); }
  100% { opacity: 0; transform: translateX(0) translateY(40px); }
}
```

## Mejora 5: Derrota Con Tinte Rojo Y Recall A Pokeball

### Objetivo

Cuando un Pokemon llega a `0 HP`, ejecutar una animacion en dos fases antes de desaparecer completamente.

### Estado actual

El frontend recibe el evento desde backend como frame:

```ts
animation.type === "faint"
```

Luego aplica `kind: "faint"` y actualiza el estado:

```ts
setAnim({ side, kind: "faint" });
setBackendState(state);
await delay(800);
```

### Fase 1: tinte rojo suave

Duracion recomendada: `180ms` a `220ms`.

Efecto:

- `filter: sepia(...) saturate(...) hue-rotate(...) brightness(...)`
- leve shake horizontal
- no cambiar todavia el estado final si causa desaparicion anticipada del sprite

### Fase 2: encogimiento hacia la Pokeball

Duracion recomendada: `450ms` a `520ms`.

Efecto:

- `scale(1)` a `scale(0.1)`
- `translateY(0)` a `translateY(-35px)`
- `opacity: 1` a `0`

CSS conceptual:

```css
@keyframes faint-recall {
  0% {
    opacity: 1;
    filter: none;
    transform: translateX(0) translateY(0) scale(1);
  }
  12% {
    filter: sepia(0.8) saturate(2) hue-rotate(-35deg) brightness(1.1);
    transform: translateX(-5px) scale(1);
  }
  24% {
    filter: sepia(0.8) saturate(2) hue-rotate(-35deg) brightness(1.1);
    transform: translateX(5px) scale(1);
  }
  35% {
    opacity: 1;
    filter: sepia(0.4) saturate(1.4) hue-rotate(-25deg);
    transform: translateX(0) translateY(0) scale(1);
  }
  100% {
    opacity: 0;
    filter: brightness(1.4);
    transform: translateY(-35px) scale(0.1);
  }
}

.anim-faint-recall {
  animation: faint-recall 700ms ease-in forwards;
}
```

### Ajuste recomendado en `playFrames`

Para que la animacion no desaparezca antes de tiempo:

1. Activar animacion de faint/recall.
2. Esperar la primera fase si se necesita mantener sprite previo.
3. Aplicar `setBackendState(state)` cuando el frame final de backend deba reflejar HP 0.
4. Esperar el resto de la animacion.

Este punto debe probarse visualmente, porque el backend ya envia un `state` con el Pokemon debilitado y el frontend puede renderizar inmediatamente el siguiente activo si el estado cambia demasiado pronto.

## Mejora 6: Fondos Y Capas De Escenario

### Objetivo

Reemplazar el fondo de gradiente por escenario Gen 6 sin perder legibilidad.

### Implementacion recomendada

Mantener las plataformas actuales o ajustarlas con opacidad, ya que ayudan a posicionar los sprites.

Capas sugeridas:

```text
Contenedor de batalla
  -> background-image Gen 6
  -> overlay suave para contraste
  -> plataformas Pokemon actuales
  -> sprites
  -> HUDs
  -> barra inferior
```

No recomendado:

- Eliminar HUDs.
- Eliminar plataformas sin revisar posicionamiento.
- Usar fondos locales.
- Cambiar tamaños de sprites al mismo tiempo que se cambian animaciones.

## Plan De Implementacion Por Fases

### Fase 1: constantes de assets

Crear constantes para fondos Showdown.

Validar:

```bash
npm run build
npm run lint
```

### Fase 2: fondo aleatorio de batalla

Agregar fondo Gen 6 en `BattleScreen`.

Validar:

- Menu carga igual.
- Selector carga igual.
- La batalla muestra fondo nuevo.
- HUDs y textos siguen siendo legibles.
- No hay parpadeo al avanzar frames.

### Fase 3: switch-in deluxe

Agregar nuevas clases CSS y activar solo en evento `switch`.

Validar:

- Entrada inicial del Pokemon.
- Cambio voluntario.
- Cambio forzado por faint.
- Modo `IA vs IA`.

### Fase 4: faint mejorado

Agregar `anim-faint-enhanced` o `anim-faint-recall`.

Validar:

- Pokemon derrotado no desaparece antes de completar animacion.
- El siguiente Pokemon no aparece demasiado pronto.
- El resultado final no se retrasa excesivamente.

### Fase 5: Pokeball sheet opcional

Solo si se decide cambiar el SVG actual.

Validar:

- Iconos de equipo vivos.
- Iconos de equipo debilitados.
- Escalado correcto en desktop y mobile.

## Criterios De Aceptacion

La mejora visual se considera correcta si cumple:

- No se descargan assets de Pokemon Showdown al repositorio.
- Los sprites siguen usando URLs publicas `ani` y `ani-back`.
- Los fondos Gen 6 se cargan por URL publica.
- `npm run build` termina correctamente.
- `npm run lint` termina correctamente.
- `Human vs IA` mantiene seleccion, batalla, acciones y resultado.
- `IA vs IA` mantiene pausa, velocidad y reproduccion automatica.
- Las animaciones existentes no se pierden.
- Si se agrega `switch-in` deluxe, dura aproximadamente `800ms`.
- Si se agrega `faint-recall`, dura aproximadamente `700ms`.
- No se modifica `app.js` porque no existe en el frontend actual.

## Riesgos Y Mitigaciones

| Riesgo | Mitigacion |
|---|---|
| Cambiar estado de backend antes de terminar faint | Separar fase visual y `setBackendState(state)` cuidadosamente |
| Fondos reducen legibilidad | Usar overlay semitransparente y conservar HUDs actuales |
| URLs externas fallan temporalmente | Mantener gradiente como fallback CSS |
| Animacion nueva rompe timing en `IA vs IA` | Respetar `speedRef.current` y probar pausa/velocidad |
| Duplicar URLs de sprites ya enviadas por backend | No hardcodear sprites Pokemon en frontend salvo alternativas documentadas |
| Reemplazar Pokeball SVG funcional innecesariamente | Mantener SVG y dejar sheet como mejora opcional |

## Resumen Tecnico

El frontend ya esta conectado al backend y ya usa los sprites correctos de Pokemon Showdown a traves de `spriteFrontUrl` y `spriteBackUrl`. Las mejoras recomendadas deben enfocarse en:

- Agregar fondos Gen 6 por URL publica.
- Extender la animacion `switch` con Pokeball, flash y entrada con overshoot.
- Extender la animacion `faint` con shake, tinte rojo y recall.
- Mantener los componentes actuales si ya se muestran correctamente.
- No tocar `app.js` ni estructuras antiguas.

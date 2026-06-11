# Revision tecnica y limpieza segura del frontend

## Objetivo

Revisar el frontend actual en `frontend/` para identificar carpetas y archivos que no participan en el flujo vigente del proyecto, proponer una limpieza segura y evitar eliminar cualquier archivo que este siendo usado o que pueda afectar la visualizacion actual.

Este documento es una revision tecnica. No elimina ni modifica archivos del frontend.

## Alcance Revisado

Frontend actual:

```text
frontend/
  index.html
  package.json
  package-lock.json
  vite.config.ts
  tsconfig.json
  eslint.config.js
  components.json
  src/
```

El frontend vigente ya no esta dentro de `frontend/retro-poke-battle-main/`. La aplicacion actual es una app Vite directa ubicada en `frontend/`.

## Resultado Ejecutivo

El flujo activo del frontend es pequeno y directo:

```text
index.html
  -> src/main.tsx
    -> src/styles.css
    -> src/lib/pokefisi/PokefisiApp.tsx
      -> src/lib/pokefisi/api.ts
      -> src/lib/pokefisi/data.ts
      -> src/lib/pokefisi/components.tsx
```

Los archivos de `src/routes/`, `src/router.tsx`, `src/routeTree.gen.ts`, `src/start.ts`, `src/server.ts`, `src/components/ui/`, `src/hooks/use-mobile.tsx`, `src/lib/api/example.functions.ts`, `src/lib/config.server.ts`, `src/lib/error-*` y `src/lib/lovable-error-reporting.ts` no forman parte del flujo actual iniciado por `index.html` y `src/main.tsx`.

La limpieza recomendada es retirar o aislar primero los archivos heredados de TanStack Start, TanStack Router, Lovable y shadcn/ui, pero solo despues de validar el build y una prueba visual completa. Actualmente el build productivo funciona porque Vite solo empaqueta el grafo que nace en `src/main.tsx`.

## Verificaciones Ejecutadas

### Build productivo

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
built in 699ms
```

Conclusion: el flujo productivo actual compila correctamente.

### Lint

Comando ejecutado:

```bash
npm run lint
```

Resultado:

```text
Error [ERR_MODULE_NOT_FOUND]: Cannot find package 'eslint-plugin-prettier' imported from frontend/eslint.config.js
```

Conclusion: el lint no llega a analizar el codigo porque `eslint.config.js` importa `eslint-plugin-prettier/recommended`, pero `eslint-plugin-prettier` no esta declarado en `package.json`.

## Flujo Activo Real

### Entry point HTML

Archivo:

```text
frontend/index.html
```

Linea clave:

```html
<script type="module" src="/src/main.tsx"></script>
```

Este archivo define el punto de entrada real del frontend.

### Entry point React

Archivo:

```text
frontend/src/main.tsx
```

Imports activos:

```ts
import "./styles.css";
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import PokefisiApp from "./lib/pokefisi/PokefisiApp";
```

Conclusion: no existe uso activo de TanStack Router, rutas file-based, `router.tsx`, `routeTree.gen.ts`, ni `src/routes/` desde el entrypoint actual.

## Archivos Y Carpetas Activos

Estos archivos participan directamente en el flujo actual y no deben eliminarse.

| Ruta | Estado | Motivo |
|---|---|---|
| `frontend/index.html` | Activo | Carga `/src/main.tsx` |
| `frontend/src/main.tsx` | Activo | Monta React en `#root` |
| `frontend/src/styles.css` | Activo | Importado por `main.tsx`; contiene Tailwind, variables, clases pixel y animaciones |
| `frontend/src/lib/pokefisi/PokefisiApp.tsx` | Activo | Componente principal de menu, seleccion, batalla y resultado |
| `frontend/src/lib/pokefisi/api.ts` | Activo | Cliente HTTP hacia backend: Pokemon, inicio de batalla, acciones y step IA |
| `frontend/src/lib/pokefisi/data.ts` | Activo | Tipos, labels, mapeo dificultad/API y mapeadores backend -> UI |
| `frontend/src/lib/pokefisi/components.tsx` | Activo | Componentes visuales usados por `PokefisiApp` |
| `frontend/package.json` | Activo | Scripts y dependencias reales del frontend |
| `frontend/package-lock.json` | Activo | Lockfile de dependencias instaladas |
| `frontend/vite.config.ts` | Activo | Configura Vite, React, Tailwind y path aliases |
| `frontend/tsconfig.json` | Activo | Configuracion TypeScript y alias `@/*` |
| `frontend/.gitignore` | Activo | Ignora `node_modules`, `dist`, `.output`, etc. |
| `frontend/.prettierrc` | Activo de tooling | Usado por `npm run format` |
| `frontend/.prettierignore` | Activo de tooling | Usado por Prettier |
| `frontend/eslint.config.js` | Activo de tooling, con error | Usado por `npm run lint`, pero referencia una dependencia faltante |

## Archivos Potencialmente No Utilizados En El Flujo Actual

Estos archivos no son llamados por el flujo activo `index.html -> main.tsx -> PokefisiApp`. La recomendacion es no borrarlos de forma manual sin una PR de limpieza y validacion, pero son candidatos claros a remocion o cuarentena.

### Capa TanStack Start/Router heredada

| Ruta | Estado actual | Motivo |
|---|---|---|
| `frontend/src/router.tsx` | No llamado | Importa `@tanstack/react-router`, pero `main.tsx` no usa router |
| `frontend/src/routeTree.gen.ts` | No llamado | Generado por TanStack Router; solo usado por `router.tsx` |
| `frontend/src/routes/__root.tsx` | No llamado | Root route de TanStack; no entra en Vite actual |
| `frontend/src/routes/index.tsx` | No llamado | Ruta TanStack que renderiza `PokefisiApp`, pero `main.tsx` ya lo renderiza directo |
| `frontend/src/routes/README.md` | No llamado | Documentacion de convenciones TanStack no aplicadas al flujo actual |
| `frontend/src/start.ts` | No llamado | Configuracion TanStack Start; no existe en `vite.config.ts` actual |
| `frontend/src/server.ts` | No llamado | Wrapper SSR TanStack/Cloudflare; no participa en app SPA Vite |

Observacion importante: `package.json` actual no declara `@tanstack/react-start`, `@tanstack/react-router` ni `@tanstack/react-query`. Si estos archivos se incluyeran en un typecheck estricto o en una app TanStack, fallarian por dependencias faltantes.

### Capa Lovable/error SSR heredada

| Ruta | Estado actual | Motivo |
|---|---|---|
| `frontend/src/lib/error-page.ts` | No llamado por flujo activo | Solo usado por `src/start.ts` y `src/server.ts` |
| `frontend/src/lib/error-capture.ts` | No llamado por flujo activo | Solo usado por `src/server.ts` |
| `frontend/src/lib/lovable-error-reporting.ts` | No llamado por flujo activo | Solo usado por `src/routes/__root.tsx` |
| `frontend/.lovable/project.json` | No runtime | Metadata de Lovable; no afecta la ejecucion Vite local |

Recomendacion: si ya no se usa Lovable/TanStack Start como plataforma de generacion o deploy, mover estos archivos a una rama de limpieza o eliminarlos junto con la capa TanStack. Si se mantiene Lovable como herramienta externa, conservar `.lovable/project.json` aunque no sea runtime.

### shadcn/ui residual

Carpeta:

```text
frontend/src/components/ui/
```

Estado: no llamada desde `src/main.tsx`, `PokefisiApp.tsx` ni `src/lib/pokefisi/components.tsx`.

Motivo: la UI activa usa componentes propios en `src/lib/pokefisi/components.tsx` (`PixelPanel`, `PixelButton`, `PokemonCard`, `PokemonHUD`, `MoveButton`, etc.). No hay imports activos hacia `@/components/ui/*` en el flujo principal.

Archivos detectados en esta carpeta:

```text
accordion.tsx
alert-dialog.tsx
alert.tsx
aspect-ratio.tsx
avatar.tsx
badge.tsx
breadcrumb.tsx
button.tsx
calendar.tsx
card.tsx
carousel.tsx
chart.tsx
checkbox.tsx
collapsible.tsx
command.tsx
context-menu.tsx
dialog.tsx
drawer.tsx
dropdown-menu.tsx
form.tsx
hover-card.tsx
input-otp.tsx
input.tsx
label.tsx
menubar.tsx
navigation-menu.tsx
pagination.tsx
popover.tsx
progress.tsx
radio-group.tsx
resizable.tsx
scroll-area.tsx
select.tsx
separator.tsx
sheet.tsx
sidebar.tsx
skeleton.tsx
slider.tsx
sonner.tsx
switch.tsx
textarea.tsx
toggle-group.tsx
toggle.tsx
tooltip.tsx
```

Riesgo actual: aunque no entran al build productivo, estos archivos contienen imports a dependencias que no estan declaradas en `package.json`, por ejemplo `@radix-ui/*`, `lucide-react`, `class-variance-authority`, `cmdk`, `recharts`, `vaul`, `embla-carousel-react`, `react-hook-form`, `date-fns`, `react-day-picker`, `sonner` e `input-otp`.

Recomendacion: eliminar esta carpeta en una limpieza controlada si no se planea usar shadcn/ui. Si se desea conservar shadcn/ui para desarrollo futuro, declarar las dependencias faltantes y mantener `components.json`.

### Utilidades asociadas a shadcn/ui

| Ruta | Estado actual | Motivo |
|---|---|---|
| `frontend/src/lib/utils.ts` | No llamado por flujo activo | Solo usado por `src/components/ui/*` |
| `frontend/src/hooks/use-mobile.tsx` | No llamado por flujo activo | Solo usado por `src/components/ui/sidebar.tsx` |
| `frontend/components.json` | No runtime | Configuracion shadcn/ui; util si se conserva `components/ui` |

Recomendacion: si se elimina `src/components/ui/`, tambien evaluar eliminar `src/lib/utils.ts`, `src/hooks/use-mobile.tsx` y `components.json`, siempre que no se reintroduzcan componentes shadcn.

### Ejemplo de API server-side heredado

| Ruta | Estado actual | Motivo |
|---|---|---|
| `frontend/src/lib/api/example.functions.ts` | No llamado | Ejemplo TanStack Start `createServerFn`; no usado por `PokefisiApp` |
| `frontend/src/lib/config.server.ts` | No llamado por flujo activo | Solo usado por `example.functions.ts` |

Recomendacion: eliminar ambos si el frontend se mantiene como SPA Vite y el backend Python sigue siendo la unica capa server-side.

## Dependencias

### Dependencias runtime usadas

| Dependencia | Estado | Uso |
|---|---|---|
| `react` | Usada | Componentes y hooks |
| `react-dom` | Usada | `createRoot` en `src/main.tsx` |
| `tw-animate-css` | Usada | Importada desde `src/styles.css` |

### Dev dependencies usadas

| Dependencia | Estado | Uso |
|---|---|---|
| `vite` | Usada | `npm run dev`, `npm run build`, `npm run preview` |
| `@vitejs/plugin-react` | Usada | `vite.config.ts` |
| `@tailwindcss/vite` | Usada | `vite.config.ts` |
| `tailwindcss` | Usada | CSS y plugin Tailwind |
| `vite-tsconfig-paths` | Usada | Alias de paths en Vite |
| `typescript` | Usada indirectamente | Tooling TS |
| `typescript-eslint`, `@eslint/js`, `eslint`, `globals`, `eslint-plugin-react-hooks`, `eslint-plugin-react-refresh` | Usadas por config de lint | El lint no corre por dependencia faltante adicional |
| `prettier` | Usada | `npm run format` |

### Dependencia faltante para lint

`eslint.config.js` importa:

```ts
import eslintPluginPrettier from "eslint-plugin-prettier/recommended";
```

Pero `package.json` no declara `eslint-plugin-prettier`. Hay dos opciones correctas:

1. Instalar y declarar `eslint-plugin-prettier` si se desea validar Prettier dentro de ESLint.
2. Quitar ese import y dejar Prettier como comando separado (`npm run format`) si se prefiere mantener ESLint mas simple.

La opcion 2 suele ser mas limpia para proyectos pequenos porque evita mezclar formato con lint.

## Impacto En CSS Y Bundle

El build productivo genera CSS de aproximadamente `82.11 kB`. Una causa probable es esta linea en `src/styles.css`:

```css
@source "../src";
```

Tailwind escanea todo `src/`, incluyendo archivos residuales de `src/components/ui/` y rutas TanStack. Aunque esos archivos no entren al JavaScript final, sus clases pueden alimentar el CSS generado.

Mejor practica posterior a la limpieza:

- Mantener `src/styles.css` porque contiene las animaciones y estilos actuales.
- Despues de eliminar o aislar residuos, volver a correr `npm run build` y comparar el tamano CSS.
- Si se conserva una estructura minima, evaluar restringir fuentes de Tailwind a rutas activas, por ejemplo `src/main.tsx` y `src/lib/pokefisi/**/*`, siempre validando que no se pierdan clases necesarias.

No se recomienda tocar `src/styles.css` antes de remover residuos, porque ahi viven clases criticas como `pixel-border`, `pixel-panel`, `pixel-hud`, `anim-shake`, `anim-flash`, `anim-attack-player`, `anim-attack-enemy`, `anim-faint`, `anim-enter`, `anim-float` y colores de tipos Pokemon.

## Limpieza Recomendada Por Fases

### Fase 1: Corregir tooling sin tocar UI

Objetivo: que las herramientas reporten problemas reales.

Acciones recomendadas:

1. Decidir si ESLint debe integrar Prettier.
2. Si no se desea esa integracion, quitar `eslint-plugin-prettier/recommended` de `eslint.config.js`.
3. Si se desea mantenerla, agregar `eslint-plugin-prettier` a `devDependencies`.
4. Ejecutar `npm run lint`.
5. Ejecutar `npm run build`.

### Fase 2: Retirar capa TanStack/Lovable no usada

Objetivo: remover archivos que no forman parte de la app Vite actual y que dependen de paquetes no declarados.

Candidatos:

```text
src/router.tsx
src/routeTree.gen.ts
src/routes/
src/start.ts
src/server.ts
src/lib/error-page.ts
src/lib/error-capture.ts
src/lib/lovable-error-reporting.ts
src/lib/api/example.functions.ts
src/lib/config.server.ts
```

Validacion requerida despues de retirar:

```bash
npm run build
npm run lint
```

Prueba manual requerida:

- Abrir menu.
- Abrir selector `Human vs IA`.
- Confirmar equipo.
- Entrar a batalla.
- Ejecutar al menos una accion de ataque y un cambio si el backend esta disponible.
- Probar `IA vs IA`, pausa y velocidad.

### Fase 3: Retirar shadcn/ui si no se usa

Objetivo: eliminar UI generica no llamada por la app actual.

Candidatos:

```text
src/components/ui/
src/hooks/use-mobile.tsx
src/lib/utils.ts
components.json
```

Condicion: solo hacerlo si se confirma que no se va a usar shadcn/ui en proximas pantallas.

Validacion:

```bash
npm run build
npm run lint
```

### Fase 4: Optimizar CSS

Objetivo: reducir CSS generado y mantener animaciones actuales.

Acciones recomendadas:

1. Ejecutar build antes y despues de retirar residuos.
2. Comparar `dist/assets/index-*.css`.
3. Si el CSS sigue inflado, restringir `@source` con cuidado.
4. Validar visualmente todas las pantallas.

## Archivos Que No Deben Eliminarse En La Primera Limpieza

| Ruta | Motivo |
|---|---|
| `src/styles.css` | Contiene animaciones, tokens, utilidades pixel y colores de tipos |
| `src/lib/pokefisi/PokefisiApp.tsx` | App principal |
| `src/lib/pokefisi/components.tsx` | Componentes visuales reales del proyecto |
| `src/lib/pokefisi/data.ts` | Tipos y mapeadores activos |
| `src/lib/pokefisi/api.ts` | Conexion activa con backend |
| `index.html` | Entry HTML real |
| `vite.config.ts` | Build actual depende de esta configuracion |
| `package.json` y `package-lock.json` | Dependencias reproducibles |

## Matriz De Riesgo De Limpieza

| Candidato | Riesgo | Recomendacion |
|---|---|---|
| `src/routes/`, `src/router.tsx`, `src/routeTree.gen.ts` | Bajo en flujo actual | Remover en una PR si no se vuelve a TanStack Router |
| `src/start.ts`, `src/server.ts` | Bajo en flujo actual | Remover si no hay SSR/TanStack Start |
| `src/lib/error-*` | Bajo despues de remover `server.ts/start.ts` | Remover junto a capa SSR heredada |
| `src/lib/lovable-error-reporting.ts` | Bajo si no se usa Lovable runtime | Remover si se elimina `routes/__root.tsx` |
| `src/components/ui/` | Medio | Remover solo si no hay plan inmediato de usar shadcn/ui |
| `src/lib/utils.ts` | Medio | Depende de `components/ui`; remover despues de esa carpeta |
| `src/hooks/use-mobile.tsx` | Medio | Depende de `sidebar.tsx`; remover despues de `components/ui` |
| `components.json` | Bajo/medio | Remover solo si se abandona shadcn/ui |
| `.lovable/project.json` | Bajo runtime, incierto tooling | Conservar si Lovable sigue siendo herramienta del equipo |

## Criterios De Aceptacion Para Una Limpieza Correcta

La limpieza se considera segura si despues de aplicarla se cumple:

- `npm run build` termina correctamente.
- `npm run lint` termina correctamente o se documenta una excepcion temporal.
- El menu principal se renderiza sin cambios visuales.
- El dropdown de dificultad sigue funcionando.
- El selector de Pokemon carga desde backend.
- `Human vs IA` mantiene seleccion, intro, batalla, acciones y resultado.
- `IA vs IA` mantiene pausa, velocidad y reproduccion automatica.
- Las animaciones `attack`, `hit`, `faint`, `enter` y `float` se mantienen.
- No se elimina `src/styles.css` ni los componentes propios de `src/lib/pokefisi/`.
- No quedan imports rotos hacia archivos eliminados.

## Plan De Revision Manual Antes De Borrar

Antes de eliminar cualquier archivo candidato, ejecutar:

```bash
cd frontend
npm run build
```

Despues de la limpieza, ejecutar:

```bash
cd frontend
npm run build
npm run lint
```

Si se agregara un script de typecheck, ejecutar tambien:

```bash
npm run typecheck
```

Script recomendado para `package.json`:

```json
{
  "scripts": {
    "typecheck": "tsc --noEmit"
  }
}
```

Nota: antes de activar `typecheck`, conviene retirar o excluir los archivos heredados que importan dependencias no declaradas.

## Conclusion

El frontend actual esta funcionando como SPA Vite directa. La parte realmente usada esta concentrada en `src/main.tsx`, `src/styles.css` y `src/lib/pokefisi/`.

La mayor oportunidad de limpieza esta en remover residuos de una plantilla previa TanStack/Lovable/shadcn que no forman parte del flujo actual. La limpieza debe hacerse por fases, validando build, lint y prueba visual despues de cada fase para no afectar lo que se muestra correctamente hoy.

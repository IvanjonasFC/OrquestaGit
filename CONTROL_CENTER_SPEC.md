# 🎛️ OrquestaGit — Spec del "Control Center" (layout RepoBar)

> Para **Antigravity** (dueño del frontend). Maqueta visual interactiva de referencia: el artifact "OrquestaGit Control Center" que hizo Claude (pídesela a Iván). Usa `brand.css` como base de estilos.

## Principio
Una sola superficie que **abre con datos de caché** (no vacía) y refresca en 2º plano. El usuario ve estado y actúa; los logs quedan en un cajón plegable, no protagonista.

## 4 niveles
1. **Dashboard global** — franja de contexto + KPIs accionables + alertas.
2. **Lista de repos** — cada repo = una fila con columnas fijas.
3. **Detalle por repo** — panel lateral derecho con pestañas (Resumen · Git · Seguridad · CI/CD).
4. **Herramientas** — Arquitecto, limpieza masiva… solo al actuar.

## Franja de contexto (top)
`[carpeta activa ▾] · [motor local ● actualizado hace 2 min] · ......... · [buscar] [refrescar todo]`
Muestra frescura del dato ("fetch hace 30 s", "leyendo caché"): sube mucho la percepción de calidad.

## KPIs accionables (no decorativos) — cada uno filtra la lista al pulsarlo
Repos · Vuln. altas · CI fallando · Sin subir · Ramas muertas · Sin upstream.

## Fila de repo (columnas fijas)
| Zona | Contenido |
|------|-----------|
| Izquierda | Nombre · stack detectado · ruta corta |
| Git | rama · último commit · ahead/behind · dirty files |
| Estado | chips: `limpio` `CI ✕` `sin upstream` `N vuln` `↓N` `↑N` |
| Acciones | abrir carpeta · abrir en GitHub · auditar · limpiar · sync |

Fila clicable → abre el panel de detalle (nivel 3).

## Panel de detalle (derecha, colapsable)
Pestañas cortas: **Resumen · Git · Seguridad · CI/CD**.
- Resumen: salud, seguridad, git, último escaneo + acción recomendada.
- Seguridad: findings ordenados por gravedad (severidad · paquete+rango · aviso · versión que corrige) + comando de arreglo copiable + botón "Arreglar" **con confirmación**.
- Git: rama, ahead/behind, dirty, sync fast-forward seguro, reflog.
- CI/CD: último workflow, estado, logs, generar workflow.

## Reglas de diseño (críticas)
- **Color = estado, nunca decoración**: verde=limpio, ámbar=aviso, rojo=problema, gris=sin configurar.
- **Chips idénticos en toda la app**: "sin upstream" se ve igual en Dashboard, Radar y Auditor.
- **Nunca consola vacía por defecto**: si no hay datos, tarjeta "último análisis no disponible" + acción.
- **Consola** = drawer inferior plegable, solo para depurar.

## Automatización segura (no humo)
- Auto-fetch: todos, cada X min.
- Auto-pull: SOLO si limpio + fast-forward posible.
- Auto-auditoría: al abrir y al detectar commit nuevo.
- Limpieza / fix: sugerir → confirmar. Nunca destructivo en silencio.

## Consolidar a 6 módulos
Repositorios (estado) · Seguridad · CI/CD · Higiene · Git local · Arquitecto — todos alimentando el mismo dashboard.

## Reparto
- **Frontend (este layout)**: Antigravity — `index.html`, `style.css`, `main.js`.
- **Backend / lógica / motor SecOps**: Claude, si Iván lo pide (contrato JSON en el worklog).
- Base de estilos: `brand.css` / `brand.js` (kit de marca ya extraído).

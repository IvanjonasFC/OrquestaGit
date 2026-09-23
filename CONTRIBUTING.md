# Contribuir a OrquestaGit

¡Gracias por tu interés en OrquestaGit! Estas notas te ayudan a contribuir de
forma efectiva.

## Requisitos de desarrollo

- Node.js 18+ y npm
- Rust (estable) + toolchain de [Tauri 2](https://tauri.app)
- Python 3.10+ (sidecar de IA/orquestación)
- (Opcional) [Ollama](https://ollama.com) para el motor de IA local

## Puesta en marcha

```bash
npm install
npm run tauri dev     # desarrollo con recarga en caliente
npm run tauri build   # binarios de producción
```

## Estilo de commits

Seguimos [Conventional Commits](https://www.conventionalcommits.org):
`feat:`, `fix:`, `chore:`, `docs:`, `refactor:`, `style:`, `test:`.

## Antes de abrir un Pull Request

1. Asegúrate de que el proyecto compila (`npm run tauri build`).
2. No subas secretos: `.env`, claves o tokens quedan fuera (ver `.gitignore`).
3. Describe el cambio y el motivo en la descripción del PR.

## Reporte de fallos

Abre una incidencia con los pasos para reproducir, el sistema operativo y,
si aplica, el log de la consola.

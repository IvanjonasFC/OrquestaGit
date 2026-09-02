# Contributing to OrquestaGit

Thanks for your interest! These notes help you contribute effectively.

## Development requirements

- Node.js 18+ and npm
- Rust (stable) and the [Tauri 2](https://tauri.app) toolchain
- Python 3.10+ (the AI / orchestration sidecar)
- (Optional) [Ollama](https://ollama.com) for the local AI engine

## Getting started

```bash
npm install
npm run tauri dev     # development, hot reload
npm run tauri build   # production binaries
```

Run the app with `npm run tauri dev`, **not** `npm run dev`: the latter opens
the plain browser, where Tauri's `invoke` bridge is unavailable.

## Commit style

We follow [Conventional Commits](https://www.conventionalcommits.org):
`feat:`, `fix:`, `chore:`, `docs:`, `refactor:`, `style:`, `test:`.

## The orchestration contract

The Python engine prints a **single JSON line** per action and never crashes the
output (everything is wrapped in `try/except`). If you add an action, keep this
contract and document it in the relevant spec.

## Before you open a pull request

1. Make sure the project builds (`npm run tauri build`).
2. Do not commit secrets: `.env`, keys and tokens stay out (see `.gitignore`).
3. Describe the change and its motivation in the pull request description.

## Reporting bugs

Open an issue with steps to reproduce, your operating system, and the console
log if relevant.

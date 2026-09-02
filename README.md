<p align="center">
  <a href="https://tauri.app"><img src="https://img.shields.io/badge/Tauri-2-24C8DB?logo=tauri&logoColor=white" alt="Tauri 2"></a>
  <img src="https://img.shields.io/badge/JavaScript-vanilla-F7DF1E?logo=javascript&logoColor=black" alt="JavaScript">
  <img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/IA-Ollama%20local-ff6b00" alt="Ollama">
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License: MIT"></a>
  <img src="https://img.shields.io/badge/Plataforma-Windows-0078D6?logo=windows&logoColor=white" alt="Windows">
</p>

# OrquestaGit (Asistente DevOps Senior IA)
> "Quiero algo mejor que me haga todo de manera senior lo mas profesional posible cuando vaya a hacer un proyecto... que sea robusto, con seguro anti env y que no me suba basura." - Iván

## 🌟 La Visión del Proyecto
**OrquestaGit** no es un cliente de Git tradicional como GitHub Desktop. Es un **"Tech Lead IA"** (Un DevOps Senior local) que se sienta en tu barra de tareas. Su objetivo es eliminar la burocracia técnica, estructurar proyectos como un profesional, automatizar CI/CD y actuar como una aduana de código estricta antes de subir a producción.

## 🏗️ Arquitectura del Sistema
El sistema seguirá la exitosa arquitectura de *AutoSubs Pro*:
- **Frontend (Tauri + HTML/JS/CSS):** Interfaz ultra-rápida, moderna (Glassmorphism) y ligera.
- **Backend (Python Sidecar):** Gestor de scripts de IA, orquestación de comandos `git`, análisis estático y hooks.
- **Motor Híbrido IA:**
  - **Local:** `Ollama` (Llama 3 / Qwen) para privacidad total (Enterprise).
  - **Cloud:** API de OpenAI/Anthropic como *fallback* para ordenadores de bajos recursos.

## 🚀 Módulos Principales (El Roadmap)

### 1. El Arquitecto (Inicio y Clonado)
- **Proyectos desde cero:** Genera esqueletos de proyectos profesionales con patrones de diseño (MVC, Hexagonal), inicializando entornos virtuales y `.gitignore` perfectos.
- **Onboarding de Proyectos Existentes:** Clona repositorios corporativos y genera un `README.md` explicativo local de cómo funciona el código heredado para no ir perdido.

### 2. El Inspector (Aduana Pre-Commit)
- **Secret Scanner (Seguro Anti-Leaks):** Hook bloqueante que analiza el `git diff`. Si detecta `.env`, `API_KEYS`, o contraseñas quemadas en el código, cancela el commit y alerta al usuario.
- **Code Reviewer (Clean Code):** La IA revisa los cambios introducidos. Si detecta código basura (`console.log`, bucles ineficientes o código comentado inutilizado), exige limpiarlo.

### 3. El Maestro CI/CD (Automatización)
- Generación automática de flujos de trabajo `.github/workflows/` (YAML) adaptados al lenguaje detectado en el repositorio (ej. compilar binarios Tauri en Windows/Mac/Linux).
- Autogeneración de mensajes de commit profesionales siguiendo la convención *Conventional Commits* (`feat:`, `fix:`, `chore:`).

### 4. Gestor de Releases
- Compila automáticamente el Changelog leyendo el historial de commits.
- Gestiona los `git tags` y automatiza las subidas a *GitHub Releases*.

---

## 🛠️ Próximos Pasos para Iniciar el Desarrollo
1. Inicializar el esqueleto de Tauri y el Sidecar de Python en este directorio.
2. Crear la integración básica con la CLI de `git` mediante Python `subprocess`.
3. Integrar la conexión puente con Ollama para los análisis de diff.

---

## 🔧 Compilar

```bash
npm install
npm run tauri dev     # desarrollo con recarga en caliente
npm run tauri build   # binarios de producción
```

## 🤝 Contribuir

Lee [`CONTRIBUTING.md`](CONTRIBUTING.md) y el [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md).
Para temas de seguridad, consulta [`SECURITY.md`](SECURITY.md).

## 📄 Licencia

Distribuido bajo licencia **MIT**. Ver [`LICENSE`](LICENSE).

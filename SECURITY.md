# Security Policy

## Supported versions

Security fixes are provided for the latest released version of OrquestaGit.

## Reporting a vulnerability

**Please do not open a public issue for security problems.** Report them
privately through GitHub's **Security tab → "Report a vulnerability"** on this
repository, or by contacting the maintainer directly.

Please include, where possible:

- A description of the issue and its impact.
- Steps to reproduce.
- The affected version and your operating system.

We aim to review reports promptly and keep you informed of progress.

## Data and privacy

OrquestaGit is designed to run locally. The default AI engine is **Ollama
(local)**; cloud APIs are optional, require a user-supplied key, and that key is
never stored in the repository. OrquestaGit reads your repositories to report
their state and never transmits source code when running in local mode.

# Dev Pulse

Live engineering news dashboard for software developers. Auto-updated every 6 hours via GitHub Actions.

**Live site:** https://kadamhemant.github.io/dev-pulse/

## Categories

- **AI Coding** — GitHub Copilot, Claude Code, Cursor, Windsurf, Codeium
- **Testing & QA** — Playwright, Selenium, Cypress, AI test automation
- **Microservices** — Service mesh, API gateways, OpenTelemetry, distributed systems
- **Fintech** — Stripe, Mastercard, Visa, payments rails, PCI/security
- **Dev Productivity** — Platform engineering, Backstage, DORA metrics, CI/CD
- **Security** — Supply chain attacks, CVEs, secrets management, AI security

## Stack

- Static HTML/CSS/JS frontend
- Python script fetches news from NewsAPI
- GitHub Actions runs the script every 6 hours
- GitHub Pages hosts the site

## Setup

1. Add `NEWS_API_KEY` to repo secrets (get free key at https://newsapi.org/register)
2. Enable GitHub Pages → Source: GitHub Actions
3. Push to `main` to trigger first deploy

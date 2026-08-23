# GÉANTS — openclaw/openclaw

Source: https://github.com/openclaw/openclaw (main branch)
Fetched: 2026-08-22
Type: TypeScript monorepo (pnpm workspaces)
Domain: AI agent orchestration (closest to ramai's domain)

## Arborescence (niveaux 1 et 2)

```
openclaw/
├── .agents/                # configurations d'agents
├── .claude/                # CLAUDE.md (compat Claude Code)
├── .github/                # CI workflows + PR templates
├── .vscode/                # editor config
├── apps/                   # applications clients
│   ├── android/            # build Android natif
│   ├── ios/                # build iOS natif
│   ├── linux/              # build Linux
│   ├── macos/              # build macOS (avec mlx-tts subfolder)
│   ├── shared/             # code commun aux apps
│   └── swabble/            # app compagnon
├── config/                 # configurations statiques
├── custodian-skills/       # skills (concept-clé du projet)
├── deploy/                 # manifests de déploiement
├── docs/                   # documentation (35+ fichiers .md)
│   ├── .generated/         # docs auto-générées
│   ├── announcements/      # changelog public
│   ├── assets/             # images, logos
│   ├── automation/         # guides automation
│   ├── channels/           # docs par canal (WhatsApp, Telegram, etc.)
│   ├── clawhub/            # marketplace de plugins
│   ├── cli/                # référence CLI
│   └── concepts/           # concepts fondamentaux
├── examples/               # exemples d'utilisation
├── extensions/             # extensions (système de plugins)
├── git-hooks/              # hooks git locaux
├── packages/               # bibliothèques internes (24 packages)
│   ├── agent-core/         # cœur de l'agent
│   ├── ai/                 # abstraction AI providers
│   ├── llm-core/           # LLM bas-niveau
│   ├── markdown-core/      # parsing markdown
│   ├── media-core/         # médias
│   ├── memory-host-sdk/   # mémoire persistante
│   ├── model-catalog-core/# catalogue de modèles
│   ├── net-policy/         # politiques réseau
│   ├── normalization-core/# normalisation
│   ├── plugin-package-contract/ # contrat plugins
│   └── ... (14 autres)
├── patches/                # patches de dépendances
├── qa/                     # tests qualité
├── scripts/                # 490+ scripts utilitaires
├── security/               # politiques sécurité
├── skills/                 # skills publics
├── src/                    # code source principal (107+ dossiers/fichiers)
│   ├── acp/                # agent control protocol
│   ├── agents/             # implémentation agents
│   ├── audit/              # audit log
│   ├── auto-reply/         # réponses auto
│   ├── bindings/           # bindings natifs
│   ├── boards/             # kanban boards
│   ├── bootstrap/          # initialisation
│   ├── canvas/             # canvas UI
│   ├── channels/           # canaux de communication
│   ├── chat/               # chat UI
│   ├── claws/              # système de "claws" (caractéristique projet)
│   ├── cli/                # CLI entry point
│   └── commands/           # commandes CLI
├── test/                   # tests (76+ fichiers)
│   └── e2e/                # tests end-to-end
├── ui/                     # interface web
├── AGENTS.md               # 64KB — guide pour agents IA
├── CHANGELOG.md            # 3.3MB (!)
├── CONTRIBUTING.md         # 14KB
├── Dockerfile              # 22KB
├── LICENSE                 # MIT
├── README.md               # 111KB (!)
├── SECURITY.md             # 36KB
├── THIRD_PARTY_NOTICES.md  # 1.5KB
├── VISION.md               # 6.8KB — vision du projet
├── package.json            # 124KB (!)
├── pnpm-workspace.yaml     # monorepo
├── taxonomy.yaml           # 707KB — taxonomie skills
├── tsconfig.json           # 14KB
└── vitest.config.ts        # config tests
```

## Structure du README (sections dans l'ordre)

1. **Title + tagline** — "# OpenClaw 🦞 — Your assistant, on your devices, in your chats"
2. **Banner image** (HTML <picture> + dark/light variants)
3. **Badges** — CI status, npm version, Node version, license MIT, Discord
4. **One-paragraph pitch** — "OpenClaw is a personal AI assistant that runs on your devices..."
5. **Quick links** — Website, Docs, Getting started, Showcase, FAQ, Vision, DeepWiki
6. **## Install** — curl one-liner macOS/Linux/WSL2, PowerShell Windows, npm alt
7. **## Quick start** — onboarding command, gateway status, dashboard
8. **## How it fits together** — Gateway, Control UI, Channels, Companion apps (architecture)
9. **## Security** — "Treat inbound messages as untrusted input" (avertissement)
10. **## Documentation** — liens vers docs.openclaw.ai
11. **## Development** — pnpm install, pnpm build, pnpm test
12. **## Community** — Discord, X/Twitter
13. **## Sponsors**
14. **## Contributors** — grille de photos
15. **## License** — MIT

## CONTRIBUTING.md (sections)

1. **## Quick Links** — GitHub, Vision, Discord, X
2. **## Maintainers** — lien page people
3. **## How to Contribute** — 5 règles claires (bugs/features/refactors/tests/questions)
4. **## Issue, PR, and Contact Routing** — table de décision (6 cas)
5. **## PR Limits** — hard cap 20 open PRs/author
6. **## Before You PR** — checklist (Node version, tests, takeover-ready, CHANGELOG, extensions)
7. **## Review Conversations Are Author-Owned** — politique de propriété des reviews
8. **## Control UI Decorators** — règles spécifiques UI
9. **## AI/Vibe-Coded PRs Welcome! 🤖** — politique IA: acceptées si disclosure
10. **## Current Focus & Roadmap 🗺** — priorités actuelles
11. **## Maintainers** (répété)
12. **## Report a Vulnerability** — channel privé

## Points communs avec les autres géants (invariants)

- README commence par un paragraphe de pitch (pas une liste)
- Badges CI + version + licence en haut du README
- CONTRIBUTING.md séparé et détaillé
- LICENSE en MIT
- SECURITY.md dédié (pas dans CONTRIBUTING)
- Documentation dans docs/ avec sa propre arborescence
- Tests dans test/ + tests e2e séparés
- AGENTS.md (spécifique agents IA, sera l'invariant du futur)
- CI visible via badges

## Différences avec notre STANDARD

Notre standard actuel (observé dans ramai):
- README commence par titre + description longue + "7 problèmes résolus"
- Pas de CONTRIBUTING.md
- Pas de SECURITY.md
- Pas de badges CI
- Pas de VISION.md
- Pas d'AGENTS.md
- docs/ non structuré (juste notebooks/ et README)
- Tests dans tests/ sans séparation e2e
- Pas de CHANGELOG.md
- Pas de scripts/ riche (juste train_champion.py et make_sheet.py)

## 3 décisions concrètes pour nos repos

1. **Ajouter CONTRIBUTING.md** à ramai — modèle openclaw, sections How to Contribute + PR Limits + Before You PR. Cité par l'admissions officer comme preuve de maturité.
2. **Ajouter badges CI** en haut du README ramai — GitHub Actions workflow qui lance pytest sur chaque push. Rendre les 149 tests visibles publiquement.
3. **Séparer tests/ en tests/unit/ et tests/e2e/** — openclaw le fait, ça clarifie ce qui est rapide vs lent. Pour ramai: unit pour cards/engine/config/AI, e2e pour le protocole complet.

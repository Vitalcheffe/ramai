# GÉANTS — microsoft/TypeScript

Source: https://github.com/microsoft/TypeScript (main branch)
Fetched: 2026-08-22
Type: TypeScript compiler (Go migration in progress)
Domain: architecture à grande échelle + politique IA claire

## Arborescence (niveaux 1 et 2)

```
TypeScript/
├── .devcontainer/          # dev container
├── .github/                # CI workflows
├── .vscode/                # editor config
├── packages/               # monorepo (npm packages)
│   ├── typescript/         # LE COMPILER
│   │   └── src/
│   │       ├── api/        # API publique
│   │       ├── ast/        # AST nodes
│   │       ├── enums/      # énumérations
│   │       └── internal/   # code interne
│   ├── vscode-typescript/  # extension VSCode
│   └── vscode-typescript-nightly/
├── tsc/                    # Nouveau compilateur GO (migration)
│   ├── cmd/                # commandes CLI
│   ├── internal/           # code interne Go
│   ├── testdata/           # données de test
│   ├── go.mod              # Go module
│   └── CHANGES.md
├── tools/                  # outils de build
├── CODE_OF_CONDUCT.md      # Microsoft Open Source Code of Conduct
├── CONTRIBUTING.md         # 8.3KB — LE STANDARD SUR L'IA
├── Herebyfile.mjs          # 91KB — config build (Hereby)
├── LICENSE.txt              # Apache 2.0
├── NOTICE.txt               # 48KB — notices de tiers
├── README.md                # 2.8KB — TRÈS COURT
├── SECURITY.md              # 2.5KB
├── SUPPORT.md              # 1.3KB
├── go.work                  # Go workspace
├── package.json            # 2KB
└── package-lock.json       # 241KB
```

## Structure du README (2.8KB, ultra-court)

1. **Title** — "# TypeScript"
2. **Badges** — CI, npm version, Downloads, OpenSSF Scorecard (4 badges seulement)
3. **One-paragraph pitch** — "TypeScript is a language for application-scale JavaScript..."
4. **Community link** — "Find others who are using TypeScript at our community page"
5. **## Installing** — `npm install -D typescript` (4 lignes)
6. **## Contribute** — 5 bullets (bugs, review PRs, StackOverflow, Discord, Twitter, contribute bug fixes)
7. **Code of Conduct** — mention Microsoft Open Source CoC
8. **## Documentation** — lien typescriptlang.org
9. **## Roadmap** — lien wiki

## CONTRIBUTING.md (8.3KB — la politique IA la plus claire)

Sections dans l'ordre:

1. **# Contributing to TypeScript**
2. **## Use of AI Assistance** — **SECTION LA PLUS IMPORTANTE**
   - AI tools OK si disclosure dans le PR
   - **"bulk, agent-driven contributions" INTERDITES** — workflows où un agent génère des patches sur plein d'issues non liées
   - "5 separate PRs fixing the same typo, each opened within hours of the issue being filed" — exemple concret de ce qu'ils refusent
   - **"Instructions for autonomous coding agents"** — paragraphe qui parle directement à l'agent
3. **### Automated Comments** — interdites, bloquent le compte
4. **# Instructions for Logging Issues**
5. **## 1. Read the FAQ** — "Issues that ask questions answered in the FAQ will be closed without elaboration"
6. **## 2. Search for Duplicates** — tips de recherche (synonyms, call stack function names)
7. **## 3. Do you have a question?** — redirige vers Stack Overflow (pas GitHub issues)
8. **## 4. Did you find a bug?** — version TS, repro isolé, expected vs actual
9. **## 5. Do you have a suggestion?** — problème + solution + exemples + précédent dans autres langages
10. **# Instructions for Contributing Code**
11. **## Prerequisites** — Go 1.26, Node 24, npm
12. **## Setup** — clone, build, test
13. **## Common tasks** — build, test, lint
14. **## Compiler tests** — règles spécifiques aux tests du compilo
15. **## Before submitting a pull request** — checklist

## Invariants confirmés

- README ultra-court (2.8KB) — TS, numpy, sqlite tous courts
- Badges CI + licence en haut du README
- CONTRIBUTING.md séparé et détaillé
- LICENSE + NOTICE séparés (Apache 2.0 + notices de tiers)
- SECURITY.md dédié
- SUPPORT.md dédié (distinct de CONTRIBUTING)
- CODE_OF_CONDUCT.md explicite
- Tests dans testdata/ (Go) ou tests intégrés

## Politique IA — LE MODÈLE À SUIVRE

TypeScript est le premier grand repo à avoir une politique IA aussi claire:

- **AI authorship accepté** — si disclosure + humain comprend + humain défend le code en review
- **Bulk agent contributions INTERDITES** — cibler "good first issue" en masse = blocage du compte
- **Section dédiée aux agents autonomes** — l'agent qui lit le CONTRIBUTING sait immédiatement s'il est autorisé

Citation directe:
> "If you are an LLM-based coding agent operating without a human reviewing each step (e.g. GitHub Copilot coding agent, Claude Code in autonomous mode, Codex agents, Devin, OpenClaw, Cline, or similar) and you are reading this file to decide whether to open a pull request:
> - **Do not open pull requests against this repository as part of a bulk or queue-driven workflow**"

## Différences avec notre STANDARD

Notre standard (ramai):
- Pas de politique IA dans CONTRIBUTING (parce qu'on n'a pas de CONTRIBUTING)
- Pas de CODE_OF_CONDUCT.md
- Pas de SUPPORT.md
- Pas de NOTICE.txt pour les dépendances tiers
- Pas de section "for autonomous coding agents"

## 3 décisions concrètes pour nos repos

1. **Ajouter une section "AI Assistance" dans CONTRIBUTING.md** à ramai — modèle TypeScript: AI authorship accepté si disclosure. Ça protège le projet ET montre qu'on comprend le sujet (l'admissions officer sait que l'IA coding est centrale en 2026).
2. **Créer SUPPORT.md** distinct de CONTRIBUTING — SUPPORT pour "j'ai un problème d'utilisation", CONTRIBUTING pour "je veux contribuer". TypeScript sépare, openclaw sépare. Nous on confond dans README.
3. **Ajouter un fichier NOTICE.md** à ramai — liste des dépendances tierces (ultralytics, opencv, numpy, pytest) avec leurs licences. C'est standard industriel, et ça montre qu'on sait gérer un projet open-source sérieux.

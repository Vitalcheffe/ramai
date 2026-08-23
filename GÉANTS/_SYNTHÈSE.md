# GÉANTS — Synthèse des invariants

4 repos autopsiés: openclaw, numpy, sqlite, TypeScript
Date: 2026-08-22

## Les 7 invariants (pratiqués par les 4 géants)

### I1. README court, commence par un paragraphe de pitch
- numpy: 4.4KB, "NumPy is the fundamental package for scientific computing with Python."
- TypeScript: 2.8KB, "TypeScript is a language for application-scale JavaScript."
- sqlite: 21KB mais spécial (explique le miroir VCS, pas le produit)
- openclaw: 111KB — exception (mais avec une pitch paragraph en première ligne)
- **Notre écart**: ramai README fait 8KB+, commence par une liste "7 problèmes résolus" au lieu d'une pitch paragraph

### I2. Badges en haut du README
- numpy: 8 badges (NumFOCUS, PyPI, Conda, StackOverflow, DOI, LFX, OpenSSF, Typing)
- TypeScript: 4 badges (CI, npm, Downloads, OpenSSF)
- openclaw: 5 badges (CI, npm, Node, license, Discord)
- sqlite: 0 badges (exception — public domain, pas de CI GitHub)
- **Notre écart**: 0 badges sur ramai

### I3. CONTRIBUTING.md séparé et détaillé
- openclaw: 14KB, 12 sections, table de décision pour le routing
- TypeScript: 8.3KB, **section IA dédiée avec instructions aux agents autonomes**
- numpy: 826 bytes (très court, redirige vers numpy.org/devdocs)
- sqlite: pas de CONTRIBUTING.md (exception — pas de PR acceptées)
- **Notre écart**: pas de CONTRIBUTING.md dans ramai

### I4. LICENSE dans un fichier séparé
- numpy: LICENSE.txt (BSD 3-Clause)
- TypeScript: LICENSE.txt (Apache 2.0) + NOTICE.txt (48KB notices tiers)
- sqlite: LICENSE.md (public domain)
- openclaw: LICENSE (MIT)
- **Notre écart**: corrigé aujourd'hui (LICENSE ajouté à ramai)

### I5. Tests dans test/ séparé + tests e2e
- openclaw: test/ + test/e2e/ (76+ fichiers)
- numpy: tests/ dans le module + test/ racine pour e2e
- TypeScript: testdata/ + tests intégrés
- sqlite: test/ (gigantesque)
- **Notre écart**: tests/ unique dans ramai, pas de séparation unit/e2e

### I6. Documentation dans docs/ avec sa propre arborescence
- openclaw: docs/ avec 35+ fichiers, sous-dossiers par concept
- numpy: doc/ avec HOWTO_DOCUMENT.rst, C_STYLE_GUIDE.rst, RELEASE_WALKTHROUGH.rst
- TypeScript: doc dans typescriptlang.org (séparé du repo)
- sqlite: doc/ dans le repo
- **Notre écart**: pas de docs/ dans ramai, juste notebooks/ + README

### I7. SECURITY.md dédié
- openclaw: 36KB (!)
- TypeScript: 2.5KB
- numpy: politique dans numpy.org/security
- sqlite: section dans README
- **Notre écart**: pas de SECURITY.md dans ramai

## Les invariants secondaires (3 sur 4)

### I8. CHANGELOG.md
- openclaw: 3.3MB (!)
- TypeScript: tsc/CHANGES.md
- numpy: doc/changelog/
- sqlite: pas de CHANGELOG (utilise Fossil timeline)
- **Notre écart**: pas de CHANGELOG dans ramai

### I9. SUPPORT.md distinct de CONTRIBUTING
- TypeScript: SUPPORT.md (1.3KB) séparé
- openclaw: routing table dans CONTRIBUTING
- numpy: mailing list dédiée
- sqlite: forum dédié
- **Notre écart**: pas de SUPPORT.md

### I10. CITATION.bib pour usage académique
- numpy: CITATION.bib (896 bytes)
- TypeScript: pas de citation (pas académique)
- sqlite: pas de citation
- openclaw: pas de citation
- **Notre écart**: pas de CITATION.bib

## Les invariants spécifiques (1 géant unique)

### I11. AGENTS.md (spécifique openclaw + sqlite)
- openclaw: 64KB AGENTS.md (guide pour agents IA)
- sqlite: 5KB AGENTS.md
- TypeScript: section dans CONTRIBUTING (pas de fichier dédié)
- numpy: rien
- **Notre écart**: pas d'AGENTS.md — mais c'est l'invariant du futur

### I12. VISION.md (spécifique openclaw)
- openclaw: 6.8KB VISION.md (la vision du projet)
- numpy, sqlite, TypeScript: pas de VISION.md
- **Notre écart**: pas de VISION.md (mais c'est rare dans les géants)

### I13. Politique IA explicite (spécifique TypeScript)
- TypeScript: section "Use of AI Assistance" + "Instructions for autonomous coding agents"
- openclaw: section "AI/Vibe-Coded PRs Welcome! 🤖"
- numpy, sqlite: pas de politique IA
- **Notre écart**: pas de politique IA

## Différences avec notre STANDARD actuel

| Écart | Notre standard | Standard des géants | Action |
|-------|----------------|----------------------|--------|
| README long | 8KB+ avec table "7 problèmes" | 4KB max, pitch paragraph | Raccourcir |
| Pas de badges | 0 | 4-8 (CI, license, downloads) | Ajouter |
| Pas de CONTRIBUTING | absent | 8-14KB détaillé | Créer |
| Pas de SECURITY.md | absent | 2-36KB dédié | Créer |
| Pas de SUPPORT.md | absent | 1-2KB | Créer |
| Pas de CHANGELOG | absent | présent | Créer |
| Pas de CITATION.bib | absent | pour numpy | Créer |
| Tests non séparés | tests/ unique | tests/ + tests/e2e/ | Séparer |
| Pas de docs/ | juste notebooks/ | docs/ structuré | Créer |
| Pas de NOTICE.md | absent | 48KB chez TS | Créer |
| Pas de politique IA | absent | section dédiée | Créer |

## 10 décisions concrètes pour nos repos

### Priorité 1 (cette semaine)
1. **Raccourcir le README ramai** — 8KB → 4KB. Pitch paragraph en première ligne. Déplacer "7 problèmes" dans docs/. Modèle numpy.
2. **Ajouter CONTRIBUTING.md** — modèle TypeScript avec section "Use of AI Assistance" + "Instructions for autonomous coding agents". 8KB cible.
3. **Ajouter badges CI** — workflow GitHub Actions + badge pytest + badge license. Rendre les 149 tests visibles.

### Priorité 2 (semaine prochaine)
4. **Ajouter SECURITY.md** — modèle TypeScript (policy de report de vulnérabilités).
5. **Séparer tests/ en tests/unit/ et tests/e2e/** — modèle openclaw.
6. **Créer docs/** avec la structure détaillée des 7 problèmes + le protocole croupier.

### Priorité 3 (à terme)
7. **Ajouter CITATION.bib** — pour usage académique (numpy le fait, c'est standard recherche).
8. **Ajouter CHANGELOG.md** — modèle openclaw (garder simple au début).
9. **Ajouter NOTICE.md** — liste des dépendances et licences (ultralytics AGPL-3.0! à vérifier).
10. **Ajouter SUPPORT.md** — séparé de CONTRIBUTING, pour les questions d'utilisation.

## L'invariant le plus surprenant

**Le README est court.** C'est l'invariant le plus contre-intuitif.

On pourrait croire qu'un repo sérieux a un README détaillé. C'est l'inverse: les géants ont des READMEs COURTS (2.8KB TypeScript, 4.4KB numpy) parce que:
- Le README est une porte d'entrée, pas un manuel
- Les détails vont dans docs/ ou CONTRIBUTING.md
- Une pitch paragraph vaut mieux qu'une table de fonctionnalités

Notre README ramai (8KB+) est un signe d'immaturité. À corriger en premier.

## L'invariant le plus important stratégiquement

**La politique IA de TypeScript.** En 2026, tout repo open-source sérieux doit avoir une politique IA explicite. TypeScript l'a fait avec une section dédiée + des instructions directes aux agents autonomes. C'est l'invariant que les repos de 2027 auront TOUS.

ramai doit l'adopter maintenant. C'est un avantage compétitif: un admissions officer qui voit une politique IA claire sait que l'auteur comprend l'écosystème 2026.

## Ce que les géants ne font PAS (et qu'on fait nous)

- **Tables markdown de "problèmes résolus"** — aucun géant ne fait ça. C'est un signe de projet-élève, pas de projet-maturité.
- **Benchmarks dans le README** — numpy les met dans benchmarks/ séparé. Nous on met le 76.5% dans le README.
- **Logs de tests dans le README** — "131 passed in 7.18s" est un output CI, pas du contenu README. À déplacer dans le badge.
- **Liste exhaustive de fonctionnalités** — les géants listent 3-4 choses que le package fournit, pas 12.

## Conclusion de l'autopsie

Notre standard était déduit de principes (clarté, transparence, anti-fiction). Le standard des géants est forgé par des millions d'utilisateurs pendant des années.

Quand les deux sont d'accord (LICENSE MIT, tests/, README avec pitch) → règle confirmée.
Quand ils diffèrent (README long vs court, CONTRIBUTING absent vs détaillé) → le géant a raison.

On met à jour notre STANDARD.

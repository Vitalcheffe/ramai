# GÉANTS — 5 issues openclaw accessibles pour une première PR

Source: https://github.com/openclaw/openclaw/issues
Fetched: 2026-08-22
Note: openclaw n'utilise pas les labels "good first issue" ou "help wanted".
      On cherche les issues "docs" + "bug" à faible complexité.

## Sélection — 5 issues accessibles

### Issue #122372 — [Docs Bug]: update node pairing storage ownership wording
- **URL**: https://github.com/openclaw/openclaw/issues/122372
- **Created**: 2026-08-12
- **Author**: vincentkoc
- **Labels**: bug, docs, maintainer, P3, clawsweeper:no-new-fix-pr
- **Comments**: 1
- **What it asks**: 
  `docs/gateway/operator-scopes.md` et `docs/nodes/index.md` décrivent encore `node.pair.*` comme utilisant un stockage séparé Gateway-owned. Le code sur `main` stocke désormais les surfaces pending/approved sur l'enregistrement canonical paired-device. Il faut mettre à jour la doc pour refléter ça.
- **Difficulty**: XS — 2 fichiers markdown à éditer
- **Why it's accessible**: 
  - Pas de code à toucher (juste .md)
  - Diff claire entre doc et code actuel
  - `clawsweeper:no-new-fix-pr` = un humain peut le faire, pas besoin d'attendre
  - P3 = priorité basse, pas de pression
- **What to do**: ouvrir PR avec `Closes #122372`, éditer les 2 fichiers markdown pour aligner wording avec le code sur main

### Issue #122598 — [Docs Bug]: clarify that MiniMax M2.x ignores disabled thinking
- **URL**: https://github.com/openclaw/openclaw/issues/122598
- **Created**: 2026-08-12
- **Author**: vincentkoc
- **Labels**: bug, docs, maintainer, extensions: minimax, P3
- **Comments**: 2
- **What it asks**:
  La doc MiniMax décrit M2.x thinking comme "disabled/off" par défaut et prétend qu'injecter `thinking: { type: "disabled" }` empêche le reasoning output. L'API Anthropic-compatible officielle de MiniMax dit que M2.x thinking ne peut PAS être désactivé. La doc est en contradiction avec le contrat API.
- **Difficulty**: XS — éditer docs/providers/minimax.md (ou similaire) pour refléter que thinking est toujours on pour M2.x
- **Why it's accessible**:
  - Doc-only
  - Contradiction factuelle facile à corriger (l'auteur a déjà la preuve)
  - P3 = pas urgent
- **What to do**: vérifier le contrat API MiniMax actuel, éditer la doc pour dire "M2.x thinking is always on; the disabled flag is ignored", PR avec `Closes #122598`

### Issue #121635 — [Docs Bug]: Poolside provider and ACPX alias are undocumented
- **URL**: https://github.com/openclaw/openclaw/issues/121635
- **Created**: 2026-08-10
- **Author**: amypoolside (Poolside employé)
- **Labels**: bug, docs, P3, clawsweeper:needs-live-repro, issue-rating: 🐚 platinum hermit
- **Comments**: 1
- **What it asks**:
  OpenClaw ne documente pas son intégration provider Poolside ni l'alias ACPX `pool` inclus dans la pinned ACPX dependency. Files à mettre à jour: docs/providers/index.md, docs/tools/acp-agents.md, docs/tools/acp-agents/pool.md (à créer).
- **Difficulty**: S — créer 1 nouveau fichier .md + éditer 2 existants
- **Why it's accessible**:
  - L'auteur est de Poolside (source officielle d'info)
  - `clawsweeper:needs-live-repro` = le bot demande une démo, mais l'auteur peut fournir la doc officielle
  - P3
- **What to do**: demander à l'auteur les infos provider officielles (modèles supportés, auth, endpoints), créer docs/tools/acp-agents/pool.md, ajouter entry dans docs/providers/index.md

### Issue #121083 — [Docs Bug]: SecretRef `provider: "default"` is an implicit built-in alias
- **URL**: https://github.com/openclaw/openclaw/issues/121083
- **Created**: 2026-08-09
- **Author**: fujixm5
- **Labels**: bug, docs, P2, clawsweeper:no-new-fix-pr, clawsweeper:source-repro
- **Comments**: 5
- **What it asks**:
  L'exemple officiel utilise `provider: "default"` dans un SecretRef, mais aucune doc user-facing ne dit que `"default"` est un alias built-in qui ne nécessite pas de `secrets.providers.default` registration. Les lecteurs qui mirror un provider id (e.g. `anthropic` → `default`) tombent sur des erreurs.
- **Difficulty**: S — éditer docs/secrets/index.md (ou similaire) pour documenter l'alias `default`
- **Why it's accessible**:
  - 5 commentaires = discussion claire sur ce qu'il faut faire
  - `clawsweeper:source-repro` = source reproductible, le bug est confirmé
  - P2 = priorité moyenne, plus visible qu'un P3
- **What to do**: lire les 5 commentaires, écrire la section qui documente `provider: "default"` comme alias built-in, PR avec `Closes #121083`

### Issue #127923 — [Bug] SSRF custom lookup can surface unhandled socket errors
- **URL**: https://github.com/openclaw/openclaw/issues/127923
- **Created**: 2026-08-22
- **Author**: aniruddhaadak80
- **Labels**: (pas encore trié — only 1 comment)
- **Comments**: 1
- **What it asks**:
  Quand la résolution DNS/socket côté provider échoue dans les chemins fetch protégés par SSRF, le custom lookup flow peut faire remonter des erreurs socket unhandled au lieu de les convertir en erreurs network déterministes.
- **Difficulty**: M — code TypeScript (probablement dans src/net-policy/ ou packages/net-policy/)
- **Why it's accessible**:
  - Pas trié (pas de label maintainer) = encore du temps pour prendre le lead
  - 1 commentaire seulement = pas de bataille de priorité
  - Récent (2026-08-22) = mainteneurs encore attentifs
  - Le domaine (SSRF/network) est pointu mais bien circonscrit
- **What to do**: 
  1. Lire le CONTRIBUTING.md d'openclaw (section AI Assistance incluse)
  2. Reproduire le bug (setup local)
  3. Identifier le fichier source du custom lookup
  4. Proposer un fix qui convertit les socket errors en erreurs déterministes
  5. PR avec `Closes #127923` + disclosure AI si applicable

## Stratégie de contribution

L'ordre recommandé:

1. **Issue #122372** (XS, doc-only) — la plus accessible pour première PR
   - Scope: 2 fichiers .md
   - Pas de code
   - Confirmation visuelle simple
   
2. **Issue #122598** (XS, doc-only) — contradiction API
   - Scope: 1 fichier .md
   - Source: contrat API officiel MiniMax
   - Confirmation: comparer doc actuelle vs contrat API

3. **Issue #121083** (S, doc-only) — alias built-in
   - Scope: 1-2 fichiers .md
   - Discussion déjà riche (5 commentaires)
   - P2 = plus visible

4. **Issue #121635** (S, doc + new file) — Poolside provider
   - Scope: créer 1 fichier + éditer 2
   - Nécessite interaction avec l'auteur (Poolside)
   - Plus long mais contribution plus valorisée

5. **Issue #127923** (M, code) — fix SSRF
   - Scope: code TypeScript
   - Nécessite reproduction + debug
   - Plus difficile mais plus impressionnante

## Pré-requis avant la première PR

1. **Lire CONTRIBUTING.md d'openclaw** en entier — sections "How to Contribute" + "PR Limits" + "Before You PR"
2. **Setup local** — clone, pnpm install, pnpm build (cf. CONTRIBUTING section "Before You PR")
3. **Disclosure AI** — si Claude/agent aide à écrire le fix, le dire dans le PR description (section "AI/Vibe-Coded PRs Welcome")
4. **Branch takeover-ready** — ouvrir PR depuis une branch où les mainteneurs peuvent push
5. **Allow edits by maintainers** — laisser activé pour fork PRs
6. **Ne pas éditer CHANGELOG.md** — les mainteneurs s'en chargent
7. **Tests locaux** — `pnpm build && pnpm check && pnpm test`

## Cible secondaire: numpy documentation issues

```bash
# Commande à exécuter pour lister les issues numpy "documentation"
curl -s "https://api.github.com/search/issues?q=repo:numpy/numpy+is:issue+is:open+label:%2224.+Documentation%22&per_page=10"
```

numpy utilise des labels numérotés (cf. issue tracker). Les issues "24. Documentation" sont les plus accessibles pour un débutant.

## Plan d'exécution

Cette semaine:
- Lundi-Mardi: setup local openclaw + lire CONTRIBUTING + choisir 1 des 5 issues
- Mercredi-Jeudi: implémenter le fix + tests locaux
- Vendredi: ouvrir la PR avec disclosure complète

L'objectif: **UNE pull request acceptée dans openclaw**. Une seule suffit à transformer le profil de "builder solo" à "membre d'écosystème".

Le repo ramai reste la vitrine technique. Un commit accepté dans openclaw est la preuve sociale que le code tient devant des mainteneurs externes.

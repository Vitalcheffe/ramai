# GÉANTS — sqlite/sqlite

Source: https://github.com/sqlite/sqlite (master branch — Fossil mirror)
Fetched: 2026-08-22
Type: C library, single-file distribution model
Domain: ingénierie logicielle absolue — qualité de commentaires légendaire

## Arborescence (niveaux 1 et 2)

```
sqlite/
├── .fossil-settings/       # config Fossil (VCS original)
├── art/                    # assets artistiques
├── autoconf/               # scripts autoconf pour distributions
├── autosetup/              # autosetup (remplaçant autoconf)
├── contrib/                # contributions externes
├── doc/                    # documentation markdown
├── ext/                    # extensions (FTS, JSON, R-Tree, etc.)
├── mptest/                 # multi-process tests
├── src/                    # CODE SOURCE — 154 fichiers C
│   ├── alter.c             # 100KB
│   ├── analyze.c           # 70KB
│   ├── btree.c             # 407KB (!!) — le b-tree légendaire
│   ├── btree.h
│   ├── btreeInt.h          # header interne (privé)
│   ├── build.c             # 196KB
│   ├── expr.c              # 272KB
│   ├── hash.c              # table de hash
│   ├── insert.c
│   ├── main.c              # entry point
│   ├── os_unix.c           # portabilité OS
│   ├── os_win.c
│   ├── parse.c             # généré depuis parse.y
│   ├── parse.y             # grammaire LALR
│   ├── pragma.c            # commandes PRAGMA
│   ├── prepare.c           # compilation SQL
│   ├── select.c            # 233KB — moteur SELECT
│   ├── sqlite3.h          # header public (API officielle)
│   ├── sqlite3ext.h       # header extensions
│   ├── tokenize.c          # tokenizer SQL
│   ├── update.c
│   ├── vacuum.c
│   ├── vdbe.c              # 271KB — Virtual Database Engine (!)
│   ├── vdbe.h
│   ├── vdbeapi.c
│   ├── vdbeaux.c
│   ├── vdbemem.c           # mémoire VDBE
│   ├── vdbesort.c          # sorter VDBE
│   ├── vdbetrace.c         # tracing
│   ├── where.c             # 270KB — optimiseur WHERE
│   └── ... (120 autres fichiers C)
├── test/                   # tests (gigantesque)
├── tool/                   # outils de build/codegen
├── AGENTS.md               # 5KB — guide pour agents
├── LICENSE.md              # public domain
├── Makefile.in
├── Makefile.msc            # 93KB Makefile Windows!
├── README.md               # 21KB
├── VERSION                 # 1 ligne (version courante)
├── auto.def                # autosetup config
├── main.mk                 # 83KB — makefile principal
└── manifest.uuid           # hash Fossil (VCS original)
```

## Structure du README (21KB)

1. **Title** — "SQLite Source Repository"
2. **What this repo contains** — "complete source code... going back to 2000-05-29"
3. **## Version Control** — EXPLIQUE que ce GitHub est un miroir, le vrai VCS est Fossil. Inclut la directive: "Always use the official name, not the Git-name, when communicating about an SQLite check-in."
4. **## Contacting The SQLite Developers** — SQLite Forum + bugs forum + email privé
5. **## Public Domain** — **CRITICAL**: "we do not normally accept pull requests, because if we did take a pull request, the changes in that pull request might carry a copyright and the SQLite source code would then no longer be fully in the public domain."
6. **## Obtaining The SQLite Source Code** — tarballs, ZIP, Fossil clone
7. **## Verifying Code Authenticity** — comment vérifier l'intégrité
8. **## Building SQLite** — instructions de compilation

## Le style de commentaires légendaire

Extrait de `src/btree.c` (le b-tree, 407KB):

```c
/*
** 2004 April 6
**
** The author disclaims copyright to this source code.  In place of
** a legal notice, here is a blessing:
**
**    May you do good and not evil.
**    May you find forgiveness for yourself and forgive others.
**    May you share freely, never taking more than you give.
**
*************************************************************************
** This file implements an external (disk-based) database using BTrees.
** See the header comment on "btreeInt.h" for additional information.
** Including a description of file format and an overview of operation.
*/
```

Règles observées dans le code SQLite:
1. **En-tête de fichier avec date + blessing** — pas de copyright, mais un "blessing" (philosophie du projet)
2. **Commentaire AVANT chaque fonction** — décrit le POURQUOI, pas le WHAT
3. **Commentaires multi-lignes en `**`** (pas `*`) — style SQLite unique
4. **Référence à header "Int"** pour les détails internes — btree.c cite btreeInt.h pour le format fichier
5. **Macros documentées** — chaque macro a un commentaire avec exemple d'usage
6. **Pas de TODOs laissés** — le code est complet ou n'existe pas

Exemple de commentaire pour une fonction simple:
```c
/*
** Extract a 2-byte big-endian integer from an array of unsigned bytes.
** But if the value is zero, make it 65536.
**
** This routine is used to extract the "offset to cell content area" value
** from the header of a btree page.  If the page size is 65536 and the page
** is empty, the offset should be 65536, but the 2-byte value stores zero.
** This routine makes the necessary adjustment to 65536.
*/
#define get2byteNotZero(X)  (((((int)get2byte(X))-1)&0xffff)+1)
```

## Invariants confirmés

- LICENSE dans un fichier séparé (pas juste mention dans README)
- README explique le VCS utilisé (transparence sur l'origine du code)
- Code source a des commentaires qui expliquent le POURQUOI
- Tests dans test/ séparé de src/
- VERSION est un fichier texte simple (pas dans pyproject.toml ou package.json)
- Pas de pull requests acceptées — modèle exceptionnel (public domain)

## Différences avec notre STANDARD

Notre standard (ramai):
- Pas de commentaire "blessing" ou équivalent philosophique
- Commentaires décrivent souvent le WHAT ("# Loop over cards") au lieu du POURQUOI
- VERSION dans pyproject.toml ou __init__.py, pas dans un fichier VERSION dédié
- Pas de miroir VCS expliqué

## 3 décisions concrètes pour nos repos

1. **Adopter le style de commentaire "pourquoi"** dans ramai/engine.py et ramai/game.py — chaque fonction explique pourquoi elle existe, pas ce qu'elle fait ligne par ligne. Le WHAT est dans le code, le POURQUOI est dans le commentaire.
2. **Ajouter un fichier VERSION** à la racine de ramai — 1 ligne, la version courante. Permet à un script de connaître la version sans parser pyproject.toml. SQLite le fait depuis 2000.
3. **Documenter le format de fichier** — comme SQLite documente le format btree dans btreeInt.h, ramai devrait documenter le format de `models/champion_weights.json` (les 16 features, l'ordre, le format JSON) dans un header dédié. Sans ça, les poids sont illisibles pour quiconque veut les réutiliser.

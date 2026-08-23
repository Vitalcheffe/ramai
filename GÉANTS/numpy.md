# GÉANTS — numpy/numpy

Source: https://github.com/numpy/numpy (main branch)
Fetched: 2026-08-22
Type: Python scientific computing library
Domain: mathématique + performance (le pendant mathématique de ramai)

## Arborescence (niveaux 1 et 2)

```
numpy/
├── .circleci/              # CI config (CircleCI, pas GH Actions!)
├── .devcontainer/          # dev container config
├── .github/                # GH workflows
├── .spin/                  # spin (build tool)
├── benchmarks/             # benchmarks (ASV -airspeed velocity-)
│   ├── benchmarks/         # bench scripts
│   ├── asv.conf.json       # config ASV
│   └── README.rst
├── branding/               # logos + assets
├── doc/                    # documentation source
│   ├── changelog/          # changelogs par version
│   ├── BRANCH_WALKTHROUGH.rst
│   ├── C_STYLE_GUIDE.rst   # guide de style C (très numpy)
│   ├── EXAMPLE_DOCSTRING.rst
│   ├── HOWTO_DOCUMENT.rst
│   ├── HOWTO_RELEASE.rst
│   ├── RELEASE_WALKTHROUGH.rst
│   ├── TESTS.rst
│   └── conftest.py
├── meson_cpu/              # build Meson (remplace setup.py)
├── numpy/                  # source code
│   ├── _build_utils/
│   ├── _core/              # cœur nouvelle API (post-2.0)
│   ├── _pyinstaller/       # hooks PyInstaller
│   ├── _typing/
│   ├── _utils/
│   ├── char/               # strings char
│   ├── core/               # ancien cœur (legacy)
│   ├── ctypeslib/
│   ├── doc/                # docstrings intégrés
│   ├── f2py/               # Fortran to Python
│   ├── fft/                # FFT
│   ├── lib/                # utilitaires
│   ├── linalg/             # algèbre linéaire
│   ├── ma/                 # masked arrays
│   ├── matrixlib/
│   ├── polynomial/
│   ├── random/             # générateurs aléatoires
│   ├── rec/
│   ├── strings/            # API strings moderne
│   ├── testing/
│   ├── tests/              # tests intégrés au module
│   ├── typing/
│   ├── __init__.py          # 25KB entry point
│   ├── __init__.pyi         # 380KB type stubs (!)
│   ├── conftest.py          # config pytest locale
│   ├── meson.build          # build par module
│   └── py.typed             # marker PEP 561
├── pixi-packages/
├── requirements/            # requirements par env
├── tools/                   # scripts build/dev
├── vendored-meson/          # Meson vendored
├── CITATION.bib             # citation académique
├── CONTRIBUTING.rst         # très court (826 bytes!)
├── INSTALL.rst
├── LICENSE.txt              # BSD 3-Clause
├── README.md                # 4.4KB (très court)
├── THANKS.txt               # remerciements
├── building_with_meson.md
├── environment.yml
├── meson.build              # build root
├── meson.options
├── pyproject.toml           # 12KB config Python
├── pytest.ini
└── ruff.toml                # linter
```

## Structure du README

Le README de numpy est volontairement COURT (4.4KB, 91 lignes):

1. **Logo centré** (HTML <h1 align="center">)
2. **Badges** — NumFOCUS, PyPI downloads, Conda downloads, Stack Overflow, Nature Paper DOI, LFX Health Score, OpenSSF Scorecard, Typing
3. **One-sentence pitch** — "NumPy is the fundamental package for scientific computing with Python."
4. **Bullet links** — Website, Documentation, Mailing list, Source code, Contributing, Bug reports, Security
5. **What it provides** — 4 bullets (N-dimensional array, broadcasting, C/C++/Fortran integration, linear algebra/FFT/random)
6. **Testing** — commande pytest
7. **Code of Conduct** — lien
8. **Call for Contributions** — façons non-code de contribuer (review, triage, tutorials, design, translation, outreach, grants)

## CONTRIBUTING.rst (volontairement court)

826 bytes seulement! Redirige vers https://www.numpy.org/devdocs/dev/index.html
Philosophie: CONTRIBUTING dans le repo est une porte, pas un manuel. Le manuel vit dans doc/.

## Points communs (invariants)

- README court (4KB) — numpy, sqlite, TypeScript tous courts
- Badges en haut du README (visibilité immédiate)
- LICENSE séparé (LICENSE.txt pour numpy, LICENSE.md pour sqlite, LICENSE pour TS)
- Tests intégrés dans le module source (numpy/tests/) ET séparés (test/ racine pour e2e)
- CITATION.bib — pour usage académique (l'admissions officer peut citer!)
- THANKS.txt — reconnaissance des contributeurs
- doc/ avec HOWTO_DOCUMENT, C_STYLE_GUIDE — guides internes

## Différences avec notre STANDARD

Notre standard (ramai):
- README long (8KB+) avec "7 problèmes résolus" en tableau
- Pas de CITATION.bib
- Pas de THANKS.txt
- Pas de benchmarks/ séparé
- Pas de guides internes (HOWTO_DOCUMENT)
- Tests dans tests/ unique

## 3 décisions concrètes pour nos repos

1. **Raccourcir le README ramai** — modèle numpy: 1 phrase pitch, 4 bullets "what it provides", liens. Déplacer le détail (7 problèmes, benchmark 1000 parties) dans docs/ ou README_long.md. L'admissions officer lit 91 lignes, pas 200.
2. **Ajouter CITATION.bib** à ramai — pour permettre la citation académique. Un admissions officer au MIT qui voit un BIB sait que l'auteur comprend la recherche.
3. **Séparer benchmarks/ de tests/** — numpy a benchmarks/ (ASV) dédié. Pour ramai: benchmarks/ pour RMSE sweeps + win-rate curves, tests/ pour la correction. Ça distingue "preuve de qualité" (tests) de "preuve de performance" (benchmarks).

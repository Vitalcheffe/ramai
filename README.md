# Rami-AI

Le premier système open-source qui joue au **Rami marocain** contre un humain en regardant les cartes sur la table avec une caméra.

Le Rami est joué par des centaines de millions de personnes à travers le monde. Les grandes IA ont conquis les échecs, le Go, le poker. Personne n'avait construit une IA qui joue au Rami avec ses yeux. C'est chose faite.

## Les 7 problèmes résolus par le protocole

Le défi n'est pas la vision — c'est le **protocole d'échange** entre l'humain et la machine à travers une table et un paquet de cartes.

| # | Problème | Solution |
|---|----------|----------|
| P1 | **Rami 51** : pas de prise défausse avant seuil | `block_discard_before_threshold` dans `RamiConfig` |
| P2 | **Extensions de melds** : poser 4♥ sur suite 5-6-7♥ | `find_meld_extensions()` dans `rami/extensions.py` |
| P3 | **Jokers** : dire quelle carte le joker remplace | `designate_jokers()` — ex. `★ → 6♥` |
| P4 | **Card counting** : déduire main adverse par arithmétique | `CardCountingState` dans `rami/counting.py` |
| P5 | **Photo défausse obligatoire** à chaque fin de tour | `ProtocolStep.PHOTO_DISCARD_*` bloque le protocole |
| P6 | **Calibration caméra** : cadre vert si angle OK | `calibrate_camera()` dans `rami/vision/calibration.py` |
| P7 | **Détection défausse** : refuse si pas exactement 1 carte | `detect_discard_pile()` — fiabilité > 0.7 requise |

Bonus : **Main humaine saisie manuellement** (grille cliquable) — l'iPad voit le dos de tes cartes, pas la caméra.

## Pourquoi ce projet existe

- Le Rami est un jeu d'**information partielle** + **mémorisation** + **probabilité**. Plus difficile que les échecs sur certains aspects.
- La vision par ordinateur (YOLOv8) permet de jouer sur une vraie table, pas sur un écran.
- Un seul notebook Colab, gratuit, sans installation.

## Démarrage rapide (Google Colab)

1. Ouvre le notebook `notebooks/ramai.ipynb` dans Google Colab (GPU gratuit).
2. Exécute les cellules dans l'ordre (11 cellules numérotées + bonus).
3. Pose ton iPad au-dessus de la table, autorise la caméra, joue.

## Les trois niveaux d'IA

| Niveau | Description | Force |
|--------|-------------|-------|
| **Découverte** | Règles pures, aucun comptage | Débutant |
| **Stratégie** | Comptage parfait + probabilités | Intermédiaire |
| **Champion** | RL self-play TD(0), 6000 parties | Avancé |

Le Champion a été entraîné par **TD(0) self-play** avec une fonction de valeur linéaire sur 16 features.

## Résultats mesurés (réels, reproductibles)

### Tests unitaires
```
$ cd /home/z/my-project/ramai-ai && python3 -m pytest tests/
119 passed in 4.79s
```

Répartition : 79 tests d'origine (cards, engine, config, 3 IA) + **40 tests sur les 7 problèmes du protocole** (Rami 51, meld extensions, joker designation, card counting, mandatory discard photo, calibration, discard detection).

### Benchmark : Champion vs Discovery sur 1000 parties
```
$ python scripts/benchmark_batched.py --batches 5 --batch-size 200 --opponent discovery
Champion:    364 victoires (36.4%)
Discovery:   112 victoires (11.2%)
Stalemates:  524 (52.4%)
Victoires décisives: 76.5%  (364 / (364 + 112))
Durée moyenne: 59.3 coups par partie
Score moyen: +53.3 pts (Champion - Discovery)
```

Le taux de stalemates élevé (52%) reflète un problème réel : avec un seuil de première pose à 30 points et un stock de 80 cartes, les deux IA peinent à vider leur main. Les 476 parties **décisives** montrent que le Champion bat clairement Discovery (76.5% de victoires).

### Courbe d'apprentissage du Champion (TD error)

L'erreur TD reste autour de 0.5 sur 6000 parties — la fonction de valeur linéaire converge lentement. Le Champion joue néanmoins mieux que Discovery (76.5% de victoires décisives), ce qui suggère que les features captent suffisamment le signal pour améliorer la politique même si V(s) reste imprécis. Aller au-delà nécessiterait un réseau neuronal (PyTorch) à la place de la fonction linéaire.

### Modèle de vision (YOLOv8)

⚠ **Le modèle YOLO n'est pas pré-entraîné dans ce repo** — il doit être fine-tuné dans Colab à partir du dataset Kaggle "playing cards object detection" (76 classes). Le script `scripts/train_yolo.py` est fourni et produit un `models/yolo_cards.pt` + un mAP50 mesuré.

```
!pip install ultralytics
!python scripts/train_yolo.py --data /content/cards.yaml --epochs 50
```

Aucun chiffre mAP n'est annoncé ici parce que le modèle n'a pas été entraîné sur la machine de développement (pas de GPU). L'utilisateur l'entraîne dans Colab et obtient son propre mAP50 (objectif : > 0.90).

## Architecture

```
rami/
├── config.py          # RamiConfig — toutes les variantes + Rami 51 (P1)
├── cards.py           # Card, Hand, Deck
├── engine.py          # valid_melds, valid_laydowns, deadwood_score
├── game.py            # GameState, Move, apply_move, score_terminal
├── extensions.py      # P2 (meld extensions) + P3 (joker designation)
├── counting.py        # P4 (card counting adversaire)
├── protocol.py        # P5 (protocole tour-par-tour + photo défausse)
├── ai/
│   ├── base.py
│   ├── discovery.py
│   ├── strategy.py
│   └── champion.py
└── vision/
    ├── detector.py
    └── calibration.py # P6 (calibration caméra) + P7 (discard detection)
scripts/
├── train_champion.py
├── train_yolo.py
├── benchmark.py
└── benchmark_batched.py
tests/                 # 119 tests, pytest
notebooks/
└── ramai.ipynb        # 25 cellules : 11 numérotées + bonus
models/                # poids entraînés
data/                  # courbes, benchmarks
```

## Règles implémentées

Le moteur est **paramétrable** via `RamiConfig`. Toutes les variantes dans un seul dataclass :

- `num_decks`, `num_jokers_per_deck`, `hand_size`, `num_players`
- `min_meld_size`, `allow_duplicate_suits_in_groups`, `max_jokers_per_meld`
- `aces_low`, `aces_high`, `allow_wraparound`
- `first_meld_threshold` (0, 30, 51)
- `stalemate_turns` (limite anti-boucle infinie)

**Variantes pré-définies :**
```python
RamiConfig.classic_moroccan()   # 2 decks × 54, 4 jokers, seuil 30
RamiConfig.threshold_51()       # seuil à 51 points
RamiConfig.no_threshold()       # sans seuil
RamiConfig.no_jokers()          # sans jokers
```

## Comment contribuer

1. Fork + clone
2. `pip install -e .` + `pip install pytest`
3. `python -m pytest tests/`
4. Ouvrez une issue pour discuter d'une amélioration avant une PR.

**Idées d'amélioration :**
- Remplacer le linear value function du Champion par un petit réseau neuronal (PyTorch)
- Implémenter les variantes régionales (Rami à 3 joueurs, Rami indien, etc.)
- Améliorer le détecteur YOLO avec des augmentations spécifiques au Rami
- Réduire le taux de stalemates en améliorant l'exploration du Discovery

## Auteur

**Amine Harch El Korane** — 16 ans, Casablanca, Maroc  
Construit dans le cadre d'un portfolio pour admission MIT.

## Licence

MIT — voir `LICENSE`. Tu peux l'utiliser, le modifier, le distribuer, le commercialiser. Mention de l'auteur appréciée mais non requise.

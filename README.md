# Rami-AI

Le premier système open-source qui joue au **Rami marocain** contre un humain en regardant les cartes sur la table avec une caméra.

Le Rami est joué par des centaines de millions de personnes à travers le monde. Les grandes IA ont conquis les échecs, le Go, le poker. Personne n'avait construit une IA qui joue au Rami avec ses yeux. C'est chose faite.

## Pourquoi ce projet existe

- Le Rami est un jeu d'**information partielle** + **mémorisation** + **probabilité**. Plus difficile que les échecs sur certains aspects.
- La vision par ordinateur (YOLOv8) permet de jouer sur une vraie table, pas sur un écran.
- Un seul notebook Colab, gratuit, sans installation.

## Démarrage rapide (Google Colab)

1. Ouvrez le notebook `notebooks/ramai.ipynb` dans Google Colab (GPU gratuit).
2. Exécutez les cellules dans l'ordre.
3. Posez votre téléphone au-dessus de la table, autorisez la caméra, jouez.

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
79 tests, tous passent.
$ python -m pytest tests/
79 passed in 16s
```

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
├── config.py          # RamiConfig — toutes les variantes dans un dataclass frozen
├── cards.py           # Card, Hand, Deck
├── engine.py          # valid_melds, valid_laydowns, deadwood_score
├── game.py            # GameState, Move, apply_move, score_terminal
├── ai/
│   ├── base.py        # AI interface, ActionContext (info partielle)
│   ├── discovery.py   # heuristique simple
│   ├── strategy.py    # comptage cartes + probabilités
│   └── champion.py    # RL: V(s) = w·φ(s), 16 features, TD(0) self-play
└── vision/
    ├── detector.py    # wrapper YOLOv8 + MockDetector fallback
    └── train_yolo.py  # script d'entraînement Colab
scripts/
├── train_champion.py  # entraîne le Champion (resumable)
├── benchmark.py       # N parties Champion vs adversaire
└── benchmark_batched.py
tests/                 # 79 tests, pytest
notebooks/
└── ramai.ipynb        # le livrable principal, 6 cellules
models/                # poids entraînés (champion_weights.json)
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

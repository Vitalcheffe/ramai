# ramai

The first system that plays **Moroccan Rami** against a human by looking at the cards on the table with a camera. The AI sees the discard pile, the melds, and the cards it has shown you. Your hand stays in your hand.

Rami is played by hundreds of millions of people worldwide. Chess, Go, Poker have been solved by AI. Nobody had built an AI that plays Rami by looking at real cards. This is it.

## Quick start (Google Colab)

1. Open `notebooks/ramai.ipynb` in Colab (GPU runtime optional but recommended).
2. Run cells in order. The camera popup is requested in Cell 1.
3. On **iPad Safari**, if the popup doesn't appear (Safari blocks `getUserMedia` in iframes), the notebook automatically falls back to the native camera app via `<input type=file capture=environment>`. Each capture opens the iPad Camera app, you take a photo, the photo comes back to the notebook.
4. Calibrate (Cell 4), enter your hand (Cell 5), play.

The notebook downloads YOLO weights automatically from this repo's GitHub release:
- Release `v0.1.0-vision-bootstrap`: YOLOv8n COCO backbone (bootstrap)
- Release `v0.2.0-cards` (future): cards-specific fine-tuned model

To produce `v0.2.0-cards`, run `notebooks/train_yolo.ipynb` in Colab (~30 min on free T4 GPU). Report the mAP50 in this README.

## The 7 problems solved by the protocol

The challenge isn't vision — it's the **exchange protocol** between the human and the machine through a table and a deck of cards.

| # | Problem | Solution |
|---|---------|----------|
| P1 | **Rami 51**: no discard draw before threshold | `block_discard_before_threshold` in `RamiConfig` |
| P2 | **Meld extensions**: lay 4♥ onto existing 5♥-6♥-7♥ | `find_meld_extensions()` in `rami/extensions.py` |
| P3 | **Jokers**: declare which card the joker represents | `designate_jokers()` — e.g. `★ → 6♥` |
| P4 | **Card counting**: deduce opponent's hand by arithmetic | `CardCountingState` in `rami/counting.py` |
| P5 | **Mandatory discard photo** at end of every turn | `ProtocolStep.PHOTO_DISCARD_*` blocks the protocol |
| P6 | **Camera calibration**: green frame when angle is OK | `calibrate_camera()` in `rami/vision/calibration.py` |
| P7 | **Discard detection**: refuse if not exactly 1 card | `detect_discard_pile()` — confidence > 0.7 required |

Bonus: **Human hand entered manually** via clickable grid (camera can't see your hand).

## The three AI levels

| Level | Description | Strength |
|-------|-------------|----------|
| **Discovery** | Rules only, no card counting | Beginner |
| **Strategy** | Perfect card counting + probabilities | Intermediate |
| **Champion** | RL self-play TD(0), 6000 games | Advanced |

The Champion was trained by **TD(0) self-play** with a linear value function over 16 features.

## Measured results (real, reproducible)

### Unit tests
```
$ python -m pytest tests/
131 passed in 7.18s
```

Breakdown: 79 original tests (cards, engine, config, 3 AIs) + 40 tests on the 7 protocol problems + 12 tests on camera + MANUAL mode.

### Benchmark: Champion vs Discovery, 1000 games
```
$ python scripts/benchmark_batched.py --batches 5 --batch-size 200 --opponent discovery
Champion:    364 wins (36.4%)
Discovery:   112 wins (11.2%)
Stalemates:  524 (52.4%)
Decisive win rate: 76.5%  (364 / (364 + 112))
Avg game length: 59.3 moves
Avg score delta: +53.3 pts (Champion - Discovery)
```

### Champion learning curve (TD error)

The TD error stays around 0.5 over 6000 games — the linear value function converges slowly. The Champion still beats Discovery (76.5% decisive wins), suggesting the features capture enough signal to improve policy even if V(s) remains imprecise. Going further requires a neural network (PyTorch) instead of the linear function.

### Vision model (YOLOv8)

The current release (`v0.1.0-vision-bootstrap`) ships the YOLOv8n COCO backbone as a bootstrap. It can detect generic objects but NOT playing cards yet — its job is to be the starting point for fine-tuning.

To get a cards-specific model:
1. Open `notebooks/train_yolo.ipynb` in Colab (GPU runtime)
2. Run it (~30 min on free T4)
3. It reports `mAP50` on the validation set
4. Upload the resulting `best.pt` to a new release `v0.2.0-cards`
5. Update `DOWNLOAD_URL` in `rami/vision/pretrained.py`

**mAP50 on the cards dataset: not yet measured** (training happens in Colab, not on this dev machine). Run the training notebook and report the number here once it's done.

## Architecture

```
rami/
├── config.py          # RamiConfig — all variants + Rami 51 (P1)
├── cards.py           # Card, Hand, Deck
├── engine.py          # valid_melds, valid_laydowns, deadwood_score
├── game.py            # GameState, Move, apply_move, score_terminal
├── extensions.py      # P2 (meld extensions) + P3 (joker designation)
├── counting.py        # P4 (card counting adversary)
├── protocol.py        # P5 (turn-by-turn protocol + discard photo)
├── ai/
│   ├── base.py
│   ├── discovery.py
│   ├── strategy.py
│   └── champion.py
└── vision/
    ├── detector.py
    ├── camera.py      # prewarm_camera() + iPad Safari file-input fallback
    ├── pretrained.py  # try_download_pretrained() — downloads from GitHub release
    └── calibration.py # P6 (calibration) + P7 (discard detection)
scripts/
├── train_champion.py
├── train_yolo.py
├── benchmark.py
└── benchmark_batched.py
tests/                 # 131 tests, pytest
notebooks/
├── ramai.ipynb        # Main notebook, 12 cells (English)
└── train_yolo.ipynb   # Training notebook (run in Colab to produce v0.2.0-cards)
models/                # downloaded weights (yolov8n.pt, champion_weights.json)
data/                  # learning curves, benchmarks
```

## Rules implemented

The engine is **configurable** via `RamiConfig`. All variants in a single frozen dataclass:

- `num_decks`, `num_jokers_per_deck`, `hand_size`, `num_players`
- `min_meld_size`, `allow_duplicate_suits_in_groups`, `max_jokers_per_meld`
- `aces_low`, `aces_high`, `allow_wraparound`
- `first_meld_threshold` (0, 30, 51)
- `block_discard_before_threshold` (Rami 51 rule, P1)
- `stalemate_turns` (anti-infinite-loop protection)

**Presets:**
```python
RamiConfig.classic_moroccan()   # 2 decks × 54, 4 jokers, threshold 30
RamiConfig.threshold_51()       # threshold 51 + no discard draw before threshold
RamiConfig.no_threshold()       # no threshold
RamiConfig.no_jokers()          # no jokers
```

## How to contribute

1. Fork + clone
2. `pip install -e .` + `pip install pytest`
3. `python -m pytest tests/`
4. Open an issue to discuss before a PR.

## Author

**Amine Harch El Korane** — 16, Casablanca, Morocco. Built as part of an MIT admission portfolio.

## License

MIT — see `LICENSE`.

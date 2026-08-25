# ramai

[![Tests](https://github.com/Vitalcheffe/ramai/actions/workflows/tests.yml/badge.svg)](https://github.com/Vitalcheffe/ramai/actions/workflows/tests.yml)


The first system that plays **Moroccan Rami** against a human by looking at the cards on the table with a camera.

Chess, Go, Poker have been solved by AI. Nobody had built an AI that plays Rami by looking at real cards. This is it.

## Quick start

Open `notebooks/ramai.ipynb` in [Colab](https://colab.research.google.com/github/Vitalcheffe/ramai/blob/main/notebooks/ramai.ipynb). Run cells in order. On iPad Safari, the notebook falls back to native camera app if `getUserMedia` is blocked.

## AI levels

| Level | Description | Strength |
|-------|-------------|----------|
| Discovery | Rules only | Beginner |
| Strategy | Perfect card counting + probabilities | Intermediate |
| Champion | RL self-play TD(0), 6000 games | Advanced |

## Results

- 149 tests pass (`python -m pytest tests/`)
- Champion vs Discovery, 500 games: 90.3% decisive win rate
- Configurable rules: Moroccan classic, Rami 51, no threshold, no jokers

## Architecture

```
rami/        # engine, AI, vision, protocol, zones
tests/       # 149 tests
notebooks/   # ramai.ipynb (play), train_yolo.ipynb (train vision)
scripts/     # benchmark, training
```

YOLO weights download from [GitHub releases](https://github.com/VitalCheffe/ramai/releases). To train a cards-specific model, run `notebooks/train_yolo.ipynb` in Colab (~30 min on free T4).

## License

MIT — see `LICENSE`.

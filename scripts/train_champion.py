"""Champion self-play trainer — TD(0) with linear value function.

Algorithm:
    - Each game, two ChampionAI instances play against each other
      (with current weights + small exploration noise).
    - After every move, do a TD update:
        V(s_t) ← V(s_t) + α (r + γ V(s_{t+1}) − V(s_t))
      where r = +1 if move ended game with us winning, -1 if losing,
      0 otherwise.
    - Weights are saved every 100 games.
    - Learning curve (loss over time) is saved to data/learning_curve.json.

Run:
    python scripts/train_champion.py --games 50000 --lr 0.01 --gamma 0.95

(50k games takes ~30 min on this 2-CPU box. For quick smoke tests, use
--games 1000.)
"""
from __future__ import annotations
import argparse
import json
import os
import random
import sys
from copy import deepcopy
from typing import List, Tuple

# Make rami/ importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rami.config import RamiConfig
from rami.cards import build_deck
from rami.game import GameState, new_game, legal_moves, apply_move, score_terminal
from rami.ai.champion import (
    ChampionAI, NUM_FEATURES, extract_features, value, _copy_state
)
from rami.ai.discovery import DiscoveryAI


def softmax_sample(scores: List[float], rng: random.Random,
                   temperature: float = 0.3) -> int:
    """Softmax sampling over legal moves for exploration."""
    if not scores:
        return 0
    import math
    m = max(scores)
    weights = [math.exp((s - m) / temperature) for s in scores]
    total = sum(weights)
    r = rng.random() * total
    acc = 0.0
    for i, w in enumerate(weights):
        acc += w
        if r <= acc:
            return i
    return len(scores) - 1


def train(num_games: int = 50000,
          lr: float = 0.01,
          gamma: float = 0.95,
          temperature: float = 0.5,
          out_path: str = "models/champion_weights.json",
          curve_path: str = "data/learning_curve.json",
          save_every: int = 500,
          log_every: int = 100,
          candidates_per_move: int = 8,
          seed: int = 0,
          resume: bool = True) -> List[float]:
    """TD(0) self-play trainer with move sampling for speed.

    Per turn we evaluate at most `candidates_per_move` random legal moves
    (instead of all of them), so training scales linearly in game length
    rather than in branching factor.

    If `resume=True` and `out_path` exists, loads prior weights and
    continues training from there.
    """
    rng = random.Random(seed)
    games_already_trained = 0
    if resume and os.path.exists(out_path):
        with open(out_path) as f:
            data = json.load(f)
        weights = data["weights"]
        games_already_trained = data.get("games_trained", 0)
        print(f"resuming from {games_already_trained} games")
    else:
        weights = [0.0] * NUM_FEATURES
        # Mild positive prior: prefer small hand, more melds laid, low deadwood
        weights[0] = -0.5   # hand_size (smaller = better)
        weights[2] = +0.5   # n_melds_laid (more = better)
        weights[5] = +0.5   # n_best_melds
        weights[6] = +0.3   # best_meld_points
        weights[14] = +1.0  # is winner
        weights[15] = -1.0  # is loser

    curve: List[dict] = []
    errors: List[float] = []

    # Load existing curve to append to
    if resume and os.path.exists(curve_path):
        try:
            with open(curve_path) as f:
                curve = json.load(f)
        except Exception:
            curve = []

    for game_idx in range(num_games):
        cfg = RamiConfig()
        g = new_game(cfg, seed=rng.randint(0, 1_000_000))
        perspective_for_training = 0

        trajectory: List[Tuple[List[float], float]] = []
        moves_made = 0
        while not g.terminal and moves_made < 300:
            moves = legal_moves(g)
            if not moves:
                break
            me = g.current

            # Sample candidates: prefer moves that lay melds (bias toward learning)
            if len(moves) > candidates_per_move:
                # Bias: half the candidates are "lay melds" moves if any exist
                lay_moves = [m for m in moves if m.laydowns]
                no_lay_moves = [m for m in moves if not m.laydowns]
                sampled: List = []
                if lay_moves:
                    sampled.extend(rng.sample(lay_moves, min(len(lay_moves), candidates_per_move // 2)))
                sampled.extend(rng.sample(no_lay_moves, min(len(no_lay_moves),
                                                            candidates_per_move - len(sampled))))
                if len(sampled) < candidates_per_move:
                    # fill from any
                    sampled.extend(rng.sample(moves, min(len(moves), candidates_per_move - len(sampled))))
            else:
                sampled = moves

            scores = []
            for m in sampled:
                sim = _copy_state(g)
                apply_move(sim, m)
                v = value(sim, perspective_for_training, weights)
                scores.append(v + rng.gauss(0, 0.05))

            idx = softmax_sample(scores, rng, temperature=temperature)
            chosen = sampled[idx]

            if me == perspective_for_training:
                feats = extract_features(g, perspective_for_training)
                v_pred = value(g, perspective_for_training, weights)
                trajectory.append((feats, v_pred))

            apply_move(g, chosen)
            moves_made += 1

        # Game-over reward
        if g.winner is not None:
            reward = 1.0 if g.winner == perspective_for_training else -1.0
        else:
            from rami.engine import deadwood_score
            d0 = deadwood_score(g.players[0].hand.cards, cfg)
            d1 = deadwood_score(g.players[1].hand.cards, cfg)
            if d0 < d1:
                reward = 0.5
            elif d0 > d1:
                reward = -0.5
            else:
                reward = 0.0

        # TD(0) updates
        for i, (feats, v_pred) in enumerate(trajectory):
            if i == len(trajectory) - 1:
                target = reward
            else:
                _, v_next = trajectory[i + 1]
                target = gamma * v_next
            td_error = target - v_pred
            for j in range(NUM_FEATURES):
                weights[j] += lr * td_error * feats[j]

        errors.append(abs(reward - (trajectory[-1][1] if trajectory else 0.0)))

        if (game_idx + 1) % log_every == 0:
            avg_err = sum(errors[-log_every:]) / len(errors[-log_every:])
            total = games_already_trained + game_idx + 1
            curve.append({"game": total, "avg_td_error": avg_err})
            print(f"game {total}  (batch {game_idx + 1}/{num_games})  avg_td_error={avg_err:.4f}")

        if (game_idx + 1) % save_every == 0:
            os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
            with open(out_path, "w") as f:
                json.dump({"weights": weights,
                           "games_trained": games_already_trained + game_idx + 1,
                           "lr": lr, "gamma": gamma,
                           "candidates_per_move": candidates_per_move}, f, indent=2)
            os.makedirs(os.path.dirname(curve_path) or ".", exist_ok=True)
            with open(curve_path, "w") as f:
                json.dump(curve, f, indent=2)

    # Final save
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with open(out_path, "w") as f:
        json.dump({"weights": weights,
                   "games_trained": games_already_trained + num_games,
                   "lr": lr, "gamma": gamma,
                   "candidates_per_move": candidates_per_move}, f, indent=2)
    with open(curve_path, "w") as f:
        json.dump(curve, f, indent=2)
    return weights


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--games", type=int, default=50000)
    p.add_argument("--lr", type=float, default=0.01)
    p.add_argument("--gamma", type=float, default=0.95)
    p.add_argument("--temperature", type=float, default=0.5)
    p.add_argument("--candidates", type=int, default=8)
    p.add_argument("--out", default="models/champion_weights.json")
    p.add_argument("--curve", default="data/learning_curve.json")
    p.add_argument("--save-every", type=int, default=500)
    p.add_argument("--log-every", type=int, default=100)
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--no-resume", action="store_true",
                   help="Start fresh, ignore existing weights")
    args = p.parse_args()

    train(num_games=args.games, lr=args.lr, gamma=args.gamma,
          temperature=args.temperature, out_path=args.out,
          curve_path=args.curve, save_every=args.save_every,
          log_every=args.log_every, seed=args.seed,
          candidates_per_move=args.candidates,
          resume=not args.no_resume)


if __name__ == "__main__":
    main()

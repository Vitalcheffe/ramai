"""Batched benchmark runner — runs N batches of M games each, accumulates.

Useful when each batch must fit in a tool timeout but the total benchmark
needs many games for statistical significance.
"""
from __future__ import annotations
import argparse
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rami.config import RamiConfig
from rami.game import new_game, legal_moves, apply_move, score_terminal
from rami.ai.champion import ChampionAI
from rami.ai.discovery import DiscoveryAI
from rami.ai.strategy import StrategyAI

from scripts.benchmark import play_one_game


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--batches", type=int, default=5)
    p.add_argument("--batch-size", type=int, default=200)
    p.add_argument("--champion-weights", default="models/champion_weights.json")
    p.add_argument("--opponent", choices=["discovery", "strategy"], default="discovery")
    p.add_argument("--out", default=None)
    p.add_argument("--seed", type=int, default=42)
    args = p.parse_args()

    champion = ChampionAI(weights_path=args.champion_weights, seed=0)
    if args.opponent == "discovery":
        opponent = DiscoveryAI(seed=1)
    else:
        opponent = StrategyAI(seed=1)

    out_path = args.out or f"data/benchmark_{args.opponent}_{args.batches * args.batch_size}.json"
    # Resume from existing file if present
    cumulative = {
        "champion_wins": 0, "opponent_wins": 0, "stalemates": 0,
        "move_counts": [], "score_deltas": []
    }
    games_already = 0
    if os.path.exists(out_path):
        try:
            with open(out_path) as f:
                prior = json.load(f)
            cumulative["champion_wins"] = prior.get("champion_wins", 0)
            cumulative["opponent_wins"] = prior.get("opponent_wins", 0)
            cumulative["stalemates"] = prior.get("stalemates", 0)
            games_already = prior.get("games", 0)
            print(f"resuming from {games_already} games "
                  f"(champ={cumulative['champion_wins']} "
                  f"opp={cumulative['opponent_wins']} "
                  f"stale={cumulative['stalemates']})")
        except Exception as e:
            print(f"could not load prior results: {e}")

    total_games = games_already
    t0 = time.time()
    # Adjust the seed offset so resumed games use different seeds
    for batch in range(args.batches):
        bt0 = time.time()
        for i in range(args.batch_size):
            game_idx = games_already + batch * args.batch_size + i
            champion_starts = (game_idx % 2 == 0)
            result = play_one_game(champion, opponent, seed=args.seed + game_idx,
                                    champion_starts=champion_starts)
            if result["champion_won"]:
                cumulative["champion_wins"] += 1
            elif result["winner"] is not None:
                cumulative["opponent_wins"] += 1
            else:
                cumulative["stalemates"] += 1
            cumulative["move_counts"].append(result["moves"])
            champ_idx = result["champ_idx"]
            opp_idx = 1 - champ_idx
            cumulative["score_deltas"].append(
                result["scores"][champ_idx] - result["scores"][opp_idx])
            total_games += 1
        bt = time.time() - bt0
        total = time.time() - t0
        cw = cumulative["champion_wins"]
        ow = cumulative["opponent_wins"]
        sw = cumulative["stalemates"]
        print(f"batch {batch+1}/{args.batches} done in {bt:.1f}s "
              f"(total {total_games} games: champ={cw} opp={ow} stale={sw})")

        # Save after every batch (resumable)
        summary = {
            "games": total_games,
            "opponent": args.opponent,
            "champion_wins": cw,
            "opponent_wins": ow,
            "stalemates": sw,
            "champion_win_rate": cw / total_games,
            "opponent_win_rate": ow / total_games,
            "stalemate_rate": sw / total_games,
            "decisive_win_rate": cw / max(1, cw + ow),
            "avg_game_length": sum(cumulative["move_counts"]) / len(cumulative["move_counts"]),
            "avg_score_delta": sum(cumulative["score_deltas"]) / len(cumulative["score_deltas"]),
            "elapsed_seconds": total,
            "champion_weights": args.champion_weights,
        }
        os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
        with open(out_path, "w") as f:
            json.dump(summary, f, indent=2)

    print("\n=== FINAL BENCHMARK ===")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()

"""Benchmark: Champion vs Discovery on N games.

Each game: Champion plays P0, Discovery plays P1. They alternate
start player every other game (to control for first-player advantage).

Output: data/benchmark_{N}.json with win counts, avg game length,
and per-game scores. Raw numbers, no fabrication.
"""
from __future__ import annotations
import argparse
import json
import os
import sys
import time
from typing import List

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rami.config import RamiConfig
from rami.game import new_game, legal_moves, apply_move, score_terminal
from rami.ai.champion import ChampionAI
from rami.ai.discovery import DiscoveryAI
from rami.ai.strategy import StrategyAI


def play_one_game(champion, opponent, seed: int, champion_starts: bool):
    cfg = RamiConfig()
    g = new_game(cfg, seed=seed)
    # Map: player 0 = champion if champion_starts else opponent
    players = [champion, opponent] if champion_starts else [opponent, champion]
    n = 0
    while not g.terminal and n < 500:
        ai = players[g.current]
        m = ai.decide(g)
        apply_move(g, m)
        n += 1
    scores = score_terminal(g)
    # Return from champion's perspective
    champ_idx = 0 if champion_starts else 1
    return {
        "winner": g.winner,
        "champion_won": g.winner == champ_idx,
        "champ_idx": champ_idx,
        "scores": scores,
        "moves": n,
        "terminal": g.terminal,
        "stalemate": g.winner is None and g.terminal,
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--games", type=int, default=1000)
    p.add_argument("--champion-weights", default="models/champion_weights.json")
    p.add_argument("--opponent", choices=["discovery", "strategy"], default="discovery")
    p.add_argument("--out", default=None,
                   help="output json path; default data/benchmark_{N}.json")
    p.add_argument("--seed", type=int, default=42)
    args = p.parse_args()

    if not os.path.exists(args.champion_weights):
        print(f"ERROR: champion weights not found: {args.champion_weights}")
        print("Run: python scripts/train_champion.py --games N")
        sys.exit(1)

    champion = ChampionAI(weights_path=args.champion_weights, seed=0)
    if args.opponent == "discovery":
        opponent = DiscoveryAI(seed=1)
    else:
        opponent = StrategyAI(seed=1)

    out_path = args.out or f"data/benchmark_{args.opponent}_{args.games}.json"

    champ_wins = 0
    opp_wins = 0
    stalemates = 0
    move_counts: List[int] = []
    score_deltas: List[int] = []
    t0 = time.time()

    for i in range(args.games):
        champion_starts = (i % 2 == 0)
        result = play_one_game(champion, opponent, seed=args.seed + i,
                                champion_starts=champion_starts)
        if result["champion_won"]:
            champ_wins += 1
        elif result["winner"] is not None:
            opp_wins += 1
        else:
            stalemates += 1
        move_counts.append(result["moves"])
        champ_idx = result["champ_idx"]
        opp_idx = 1 - champ_idx
        score_deltas.append(result["scores"][champ_idx] - result["scores"][opp_idx])

        if (i + 1) % 100 == 0:
            elapsed = time.time() - t0
            print(f"  game {i+1}/{args.games}  champ={champ_wins}  opp={opp_wins}  "
                  f"stale={stalemates}  [{elapsed:.1f}s]")

    elapsed = time.time() - t0
    summary = {
        "games": args.games,
        "opponent": args.opponent,
        "champion_wins": champ_wins,
        "opponent_wins": opp_wins,
        "stalemates": stalemates,
        "champion_win_rate": champ_wins / args.games,
        "opponent_win_rate": opp_wins / args.games,
        "avg_game_length": sum(move_counts) / len(move_counts),
        "avg_score_delta": sum(score_deltas) / len(score_deltas),
        "elapsed_seconds": elapsed,
        "champion_weights": args.champion_weights,
    }
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(summary, f, indent=2)

    print("\n=== BENCHMARK RESULTS ===")
    print(f"Champion vs {args.opponent} ({args.games} games)")
    print(f"  Champion wins:    {champ_wins} ({champ_wins/args.games*100:.1f}%)")
    print(f"  Opponent wins:    {opp_wins} ({opp_wins/args.games*100:.1f}%)")
    print(f"  Stalemates:       {stalemates} ({stalemates/args.games*100:.1f}%)")
    print(f"  Avg game length:  {sum(move_counts)/len(move_counts):.1f} moves")
    print(f"  Avg score delta:  {sum(score_deltas)/len(score_deltas):+.1f} (champ - opp)")
    print(f"  Elapsed:          {elapsed:.1f}s")
    print(f"  Saved to:         {out_path}")


if __name__ == "__main__":
    main()

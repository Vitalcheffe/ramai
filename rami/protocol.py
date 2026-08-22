"""The Protocol — how the human and the machine exchange moves through
a physical table and a deck of cards.

This module defines the SEQUENCE OF EVENTS for one turn of the game.
It is the contract between the notebook (UI) and the engine (rules).

The protocol is driven by `ProtocolStep` enums. The notebook calls
`next_step(state, counting, last_action)` to know what to ask the user
for next. Each step has:
  - a prompt (what to display to the human)
  - an expected input type (photo, click, none)
  - a handler that processes the input and updates the state

KEY INVARIANT: the discard pile MUST be photographed at the end of every
turn. If the photo is missing or fails recognition, the protocol refuses
to proceed. This is the single point of failure for card counting.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Callable, List, Optional, Tuple

from .cards import Card
from .config import RamiConfig
from .game import GameState, Move
from .counting import CardCountingState


class ProtocolStep(Enum):
    """The discrete steps of one turn of the protocol."""
    # --- Human's turn ---
    ASK_HUMAN_DRAW = auto()           # "Pioche ou prends la défausse ?"
    PHOTO_DISCARD_AFTER_HUMAN_DRAW = auto()  # photo of discard if human took it
    UPDATE_HUMAN_HAND = auto()         # human selects cards via grid
    ASK_HUMAN_LAYDOWN = auto()         # "Quelle meld veux-tu poser ?"
    ASK_HUMAN_DISCARD = auto()         # "Quelle carte jettes-tu ?"
    PHOTO_DISCARD_AFTER_HUMAN = auto() # MANDATORY photo of the new discard

    # --- AI's turn ---
    AI_ANNOUNCE_DECISION = auto()       # "RAMAI décide: ..."
    HUMAN_EXECUTE_AI_DRAW = auto()      # human draws for AI (shows card if from discard)
    PHOTO_AI_DRAWN_CARD = auto()       # if AI drew from discard, photo of the card
    HUMAN_EXECUTE_AI_LAYDOWN = auto()   # human lays AI's melds physically
    PHOTO_AI_LAYDOWN = auto()           # verification photo
    PHOTO_AI_DISCARD = auto()          # photo of AI's discard (mandatory)

    # --- End of turn ---
    CHECK_END_OF_GAME = auto()         # card-counting check
    NEXT_TURN = auto()                  # advance to next player


@dataclass
class ProtocolPrompt:
    """What the notebook should display + collect for a given step."""
    step: ProtocolStep
    message: str                       # what to tell the human
    input_type: str                    # "none" | "photo" | "card_select" | "card_grid"
    expected: Optional[str] = None    # e.g. "discard_pile" or "ai_hand"
    warning: Optional[str] = None      # e.g. "triche" warning if showing AI hand


@dataclass
class TurnContext:
    """Tracks where we are in the current turn's protocol."""
    cfg: RamiConfig
    state: GameState
    counting: CardCountingState
    ai_player_idx: int = 1              # AI is P1 by convention
    current_step: ProtocolStep = ProtocolStep.ASK_HUMAN_DRAW
    pending_move: Optional[Move] = None
    photo_taken: bool = False
    step_index: int = 0


def next_step(ctx: TurnContext, last_input_ok: bool = True) -> ProtocolPrompt:
    """Advance the protocol one step. Returns the prompt for the next step.

    `last_input_ok` is False if the previous input (e.g. photo) failed
    recognition. In that case the protocol loops back to the same step
    with a warning.
    """
    if not last_input_ok:
        # Loop on same step with a warning
        return _prompt_for(ctx.current_step, ctx, warning="Réessaie, la photo n'est pas claire.")

    step = ctx.current_step
    ai_idx = ctx.ai_player_idx
    human_idx = 1 - ai_idx

    # Advance based on current step
    if step == ProtocolStep.ASK_HUMAN_DRAW:
        ctx.current_step = ProtocolStep.UPDATE_HUMAN_HAND
        return _prompt_for(ctx.current_step, ctx)

    if step == ProtocolStep.UPDATE_HUMAN_HAND:
        ctx.current_step = ProtocolStep.ASK_HUMAN_LAYDOWN
        return _prompt_for(ctx.current_step, ctx)

    if step == ProtocolStep.ASK_HUMAN_LAYDOWN:
        ctx.current_step = ProtocolStep.ASK_HUMAN_DISCARD
        return _prompt_for(ctx.current_step, ctx)

    if step == ProtocolStep.ASK_HUMAN_DISCARD:
        # MANDATORY photo of the new discard
        ctx.current_step = ProtocolStep.PHOTO_DISCARD_AFTER_HUMAN
        ctx.photo_taken = False
        return _prompt_for(ctx.current_step, ctx)

    if step == ProtocolStep.PHOTO_DISCARD_AFTER_HUMAN:
        if not ctx.photo_taken:
            # Refuse to advance — loop on same step
            return _prompt_for(ctx.current_step, ctx,
                              warning="Photo de la défausse OBLIGATOIRE. "
                                     "Montre la défausse à la caméra.")
        ctx.current_step = ProtocolStep.CHECK_END_OF_GAME
        return _prompt_for(ctx.current_step, ctx)

    if step == ProtocolStep.CHECK_END_OF_GAME:
        # Check if opponent's hand count is 0 (by arithmetic)
        if ctx.counting.is_opponent_empty(human_idx):
            ctx.state.winner = human_idx
            ctx.state.terminal = True
            return _prompt_for(ProtocolStep.NEXT_TURN, ctx)
        if ctx.counting.is_opponent_empty(ai_idx):
            ctx.state.winner = ai_idx
            ctx.state.terminal = True
            return _prompt_for(ProtocolStep.NEXT_TURN, ctx)
        # Hand off to AI
        ctx.current_step = ProtocolStep.AI_ANNOUNCE_DECISION
        return _prompt_for(ctx.current_step, ctx)

    if step == ProtocolStep.AI_ANNOUNCE_DECISION:
        # AI decides its move (the notebook will call ai.decide(state))
        ctx.current_step = ProtocolStep.HUMAN_EXECUTE_AI_DRAW
        return _prompt_for(ctx.current_step, ctx)

    if step == ProtocolStep.HUMAN_EXECUTE_AI_DRAW:
        # If AI drew from discard, need a photo of the card to confirm
        if ctx.pending_move and ctx.pending_move.draw_source == "discard":
            ctx.current_step = ProtocolStep.PHOTO_AI_DRAWN_CARD
        else:
            ctx.current_step = ProtocolStep.HUMAN_EXECUTE_AI_LAYDOWN
        return _prompt_for(ctx.current_step, ctx)

    if step == ProtocolStep.PHOTO_AI_DRAWN_CARD:
        ctx.current_step = ProtocolStep.HUMAN_EXECUTE_AI_LAYDOWN
        return _prompt_for(ctx.current_step, ctx)

    if step == ProtocolStep.HUMAN_EXECUTE_AI_LAYDOWN:
        if ctx.pending_move and ctx.pending_move.laydowns:
            ctx.current_step = ProtocolStep.PHOTO_AI_LAYDOWN
        else:
            ctx.current_step = ProtocolStep.PHOTO_AI_DISCARD
        return _prompt_for(ctx.current_step, ctx)

    if step == ProtocolStep.PHOTO_AI_LAYDOWN:
        ctx.current_step = ProtocolStep.PHOTO_AI_DISCARD
        return _prompt_for(ctx.current_step, ctx)

    if step == ProtocolStep.PHOTO_AI_DISCARD:
        if not ctx.photo_taken:
            return _prompt_for(ctx.current_step, ctx,
                              warning="Photo de la défausse OBLIGATOIRE. "
                                     "L'IA vient de jeter, montre la défausse.")
        # End of AI's turn — check end of game
        ctx.current_step = ProtocolStep.CHECK_END_OF_GAME
        return _prompt_for(ctx.current_step, ctx)

    if step == ProtocolStep.NEXT_TURN:
        # Should not be called directly — notebook should check state.terminal
        return _prompt_for(ProtocolStep.CHECK_END_OF_GAME, ctx)

    # Fallback
    return _prompt_for(ProtocolStep.ASK_HUMAN_DRAW, ctx)


def _prompt_for(step: ProtocolStep, ctx: TurnContext,
                warning: Optional[str] = None) -> ProtocolPrompt:
    """Generate the prompt for a step."""
    ai_idx = ctx.ai_player_idx
    human_idx = 1 - ai_idx

    if step == ProtocolStep.ASK_HUMAN_DRAW:
        return ProtocolPrompt(
            step=step,
            message=f"À toi de jouer. Pioche dans le talon OU prends la défausse "
                    f"({ctx.state.top_discard.name if ctx.state.top_discard else '—'}). "
                    f"Dis au notebook ce que tu as fait.",
            input_type="card_select",
            expected="draw_source",
            warning=warning,
        )

    if step == ProtocolStep.UPDATE_HUMAN_HAND:
        return ProtocolPrompt(
            step=step,
            message="Clique sur les cartes que tu as en main (grille ci-dessous).",
            input_type="card_grid",
            expected="human_hand",
            warning=warning,
        )

    if step == ProtocolStep.ASK_HUMAN_LAYDOWN:
        return ProtocolPrompt(
            step=step,
            message="Veux-tu poser une meld ? Si oui, sélectionne les cartes. Sinon, continue.",
            input_type="card_select",
            expected="laydown",
            warning=warning,
        )

    if step == ProtocolStep.ASK_HUMAN_DISCARD:
        return ProtocolPrompt(
            step=step,
            message="Quelle carte jettes-tu ? Clique sur la carte dans ta main.",
            input_type="card_select",
            expected="discard",
            warning=warning,
        )

    if step == ProtocolStep.PHOTO_DISCARD_AFTER_HUMAN:
        return ProtocolPrompt(
            step=step,
            message=f"📸 OBLIGATOIRE : photographie la défausse "
                    f"(carte visible : {ctx.state.top_discard.name if ctx.state.top_discard else '—'}).",
            input_type="photo",
            expected="discard_pile",
            warning=warning or "Sans cette photo, le comptage de cartes tombe.",
        )

    if step == ProtocolStep.CHECK_END_OF_GAME:
        opp_count = ctx.counting.hand_count(human_idx)
        ai_count = ctx.counting.hand_count(ai_idx)
        return ProtocolPrompt(
            step=step,
            message=f"Vérification fin de partie : "
                    f"main humaine ≈ {opp_count} cartes, "
                    f"main IA ≈ {ai_count} cartes.",
            input_type="none",
            warning=warning,
        )

    if step == ProtocolStep.AI_ANNOUNCE_DECISION:
        return ProtocolPrompt(
            step=step,
            message="RAMAI réfléchit...",
            input_type="none",
            warning=warning,
        )

    if step == ProtocolStep.HUMAN_EXECUTE_AI_DRAW:
        if ctx.pending_move and ctx.pending_move.draw_source == "discard":
            return ProtocolPrompt(
                step=step,
                message=f"RAMAI prend la défausse ({ctx.state.top_discard.name if ctx.state.top_discard else '—'}). "
                        f"Prends-la et mets-la dans la main de RAMAI.",
                input_type="none",
                warning=warning,
            )
        return ProtocolPrompt(
            step=step,
            message="RAMAI pioche dans le talon. Prends la carte du dessus, "
                    "montre-la face caméra brièvement, puis mets-la dans la main de RAMAI.",
            input_type="none",
            warning=warning,
        )

    if step == ProtocolStep.PHOTO_AI_DRAWN_CARD:
        return ProtocolPrompt(
            step=step,
            message="📸 RAMAI a pioché dans le talon. Montre la carte face caméra "
                    "pour qu'elle la reconnaisse et la compte.",
            input_type="photo",
            expected="ai_drawn_card",
            warning=warning,
        )

    if step == ProtocolStep.HUMAN_EXECUTE_AI_LAYDOWN:
        if not ctx.pending_move or not ctx.pending_move.laydowns:
            return ProtocolPrompt(
                step=step,
                message="RAMAI ne pose aucune meld ce tour.",
                input_type="none",
                warning=warning,
            )
        n_melds = len(ctx.pending_move.laydowns)
        cards = [c for meld in ctx.pending_move.laydowns for c in meld]
        return ProtocolPrompt(
            step=step,
            message=f"RAMAI pose {len(cards)} cartes en {n_melds} meld(s). "
                    f"Sors ces cartes de sa main et pose-les sur la table.",
            input_type="none",
            warning=warning,
        )

    if step == ProtocolStep.PHOTO_AI_LAYDOWN:
        return ProtocolPrompt(
            step=step,
            message="📸 Vérification : photographie les melds que tu viens de poser.",
            input_type="photo",
            expected="ai_laydown",
            warning=warning,
        )

    if step == ProtocolStep.PHOTO_AI_DISCARD:
        return ProtocolPrompt(
            step=step,
            message=f"📸 OBLIGATOIRE : RAMAI jette {ctx.pending_move.discard.name if ctx.pending_move else '?'}. "
                    f"Pose la carte sur la défausse et photographie-la.",
            input_type="photo",
            expected="ai_discard",
            warning=warning or "Sans cette photo, le comptage de cartes tombe.",
        )

    if step == ProtocolStep.NEXT_TURN:
        return ProtocolPrompt(
            step=step,
            message="Tour suivant.",
            input_type="none",
            warning=warning,
        )

    return ProtocolPrompt(step=step, message="?", input_type="none")


# ---------- Visibility policy for AI hand ----------

def should_show_ai_hand(ai_level: str) -> bool:
    """Whether the notebook should display RAMAI's hand by default.

    Discovery: yes (pedagogical).
    Strategy: no.
    Champion: no.
    """
    return ai_level == "discovery"


def show_ai_hand_warning() -> str:
    """Warning shown when user clicks 'triche' to reveal AI hand."""
    return ("⚠ Tu vas voir les cartes de RAMAI. "
            "C'est de la triche. Clique à nouveau pour confirmer.")

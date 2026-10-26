"""Bounded cryptographic dice and an explicitly limited check classifier.

No character talents, reroll choices, power legality, or state are inferred here.
"""
from __future__ import annotations

import re
import secrets
from collections.abc import Callable, Sequence

_PATTERN = re.compile(r"([1-9][0-9]{0,2})[dD]([1-9][0-9]{0,6})(?:([+-])([0-9]{1,7}))?\Z")


def _integer(value: object, name: str, minimum: int, maximum: int) -> int:
    if type(value) is not int or not minimum <= value <= maximum:
        raise ValueError(f"{name} must be an integer in {minimum}..{maximum}")
    return value


def roll(expression: str, *, randbelow: Callable[[int], int] = secrets.randbelow) -> dict:
    """Roll NdS[+/-K], using OS-backed randomness unless a test RNG is supplied.

    Limits: 1..100 dice, 2..1,000,000 sides, modifier magnitude <= 1,000,000.
    Whitespace is ignored. No eval, arithmetic nesting, or exploding dice.
    The result identifies injected RNGs rather than claiming they are secure.
    """
    if not isinstance(expression, str) or len(expression) > 80:
        raise ValueError("expression must be a string of at most 80 characters")
    normalized = "".join(expression.split())
    match = _PATTERN.fullmatch(normalized)
    if match is None:
        raise ValueError("expected NdS optionally followed by +K or -K")
    count = _integer(int(match[1]), "dice count", 1, 100)
    sides = _integer(int(match[2]), "sides", 2, 1_000_000)
    modifier = int(match[4] or 0) * (-1 if match[3] == "-" else 1)
    _integer(modifier, "modifier", -1_000_000, 1_000_000)
    dice = []
    for _ in range(count):
        sample = randbelow(sides)
        _integer(sample, "random sample", 0, sides - 1)
        dice.append(sample + 1)
    return {
        "expression": f"{count}d{sides}" + (f"{modifier:+d}" if modifier else ""),
        "dice": dice,
        "modifier": modifier,
        "total": sum(dice) + modifier,
        "randomness": "secrets.randbelow" if randbelow is secrets.randbelow else "injected",
    }


def assess_check(dice: Sequence[int], modifier: int, tc: int, *, tie_policy: str, actor: str = "pc") -> dict:
    """Classify a final 3d6 result, not an entire Strange Heroes rules action.

    Original implementation of the v1.02 p7 degree thresholds. Exact-TC ties
    require an explicit local ruling: p7 describes higher/lower, while p29 uses
    meet/beat for attacks. Confidence/doubt, impossible TCs, degree-changing
    talents and other exceptions must be resolved by the GM BEFORE or AFTER
    this classifier as appropriate. Returned resource awards are proposals;
    this function never applies them to the ledger. Awards apply only to PCs;
    set actor="npc" for non-player checks. Ego is a GM pool, not actor-owned.
    """
    if not isinstance(dice, (list, tuple)) or len(dice) != 3:
        raise ValueError("check requires exactly three final d6 results")
    final_dice = [_integer(d, "die", 1, 6) for d in dice]
    _integer(modifier, "modifier", -1_000_000, 1_000_000)
    _integer(tc, "TC", -1_000_000, 1_000_000)
    if tie_policy not in ("success", "failure"):
        raise ValueError("tie_policy must explicitly be 'success' or 'failure'")
    if actor not in ("pc", "npc"):
        raise ValueError("actor must be 'pc' or 'npc'")
    total = sum(final_dice) + modifier
    margin = total - tc
    success = margin > 0 or (margin == 0 and tie_policy == "success")
    if success:
        if len(set(final_dice)) == 1 and final_dice[0] in (1, 6):
            degree = "perfect_success"
        elif margin >= 6:
            degree = "spectacular_success"
        else:
            degree = "success"
    elif final_dice == [1, 1, 1]:
        degree = "perfect_failure"
    elif margin <= -6:
        degree = "spectacular_failure"
    else:
        degree = "failure"
    return {
        "dice": final_dice,
        "modifier": modifier,
        "tc": tc,
        "total": total,
        "margin": margin,
        "success": success,
        "degree": degree,
        "tie_policy": tie_policy,
        "actor": actor,
        "proposed_frustration": int(actor == "pc" and not success),
        "proposed_gm_ego": int(actor == "pc" and degree in ("perfect_success", "spectacular_success")),
        "source": "Strange Heroes Playtest v1.02, printed pp5,7,12; tie ambiguity p7/p29",
        "limitations": "Final dice only; GM resolves confidence/doubt, impossible TCs, and talent exceptions. Awards require ledger transaction.",
    }

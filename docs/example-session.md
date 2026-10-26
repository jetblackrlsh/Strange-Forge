# Executable fictional session

This is an original toy scene, not a reproduction of a player's campaign or a claim to automate an official talent. Run from the repository root:

```sh
mkdir -p private
python -m strange_forge new private/demo.save.json --name 'Harbor Lights'
python -m strange_forge add-character private/demo.save.json beacon --name Beacon --hp 20 --energy 10
python -m strange_forge propose private/demo.save.json brace-1 examples/brace-proposal.json
python -m strange_forge complete private/demo.save.json brace-1
python -m strange_forge show private/demo.save.json
```

**GM:** A surge strikes the pier. Beacon wants to brace a damaged beam. Our agreed original custom power, *Harbor Brace*, costs 2 energy and 1 action; this safe, uncontested activation needs no roll. This is a house ruling, not an official book talent. Proceed?

**Player:** Yes.

`propose` records the intended cost but leaves energy **10**, actions **3**. `complete` records that activation actually happened: energy **8**, actions **2**, HP **20**, revision **3**. A second completion is rejected without changing the save. The previous revision remains in `.bak`. Narration can now say the beam is held—not that a merely proposed activation already happened.

For an uncertain later action, first look up the applicable rule, explain the stakes, then generate real dice:

```sh
python -m strange_forge roll '3d6+2'
```

Use those actual dice in `check`. For a **fixed test fixture only**, dice 4,3,2 with modifier 2 vs TC11 is an exact tie:

```sh
python -m strange_forge check --dice 4 3 2 --modifier 2 --tc 11 --tie-policy success
```

It classifies success under the disclosed table ruling, not an asserted universal rule. Confidence/doubt and exceptions require the GM. Any failure award or spectacular/perfect Ego award returned by `check` is only a **proposal**: translate an adjudicated outcome into a cited transaction, respect current resources/Nexus, and then complete it. PC spectacular/perfect success awards go to campaign `gm_ego`, not the hero (p5). Use `--actor npc` to suppress PC-only award proposals for NPC checks. The GM handles other rule effects and end-of-session Ego reset.

`tests/test_cli.py::test_end_to_end` actually executes the save, proposal, completion, duplicate-rejection, secure-roll receipt, explicit-tie classification and reload flow. Other ledger tests execute resource changes, negative energy, frustration/Nexus, separate GM Ego, inventory, NPC relationships, clocks, and write-failure protection. These tests are not an LLM gameplay evaluation.

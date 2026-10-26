# Strange Forge

**An unofficial, lean conversational AI-GM toolkit inspired by Strange Heroes and QuestForge.**

Version 0.1.0 is a small **adjudication framework**, not a complete game engine. Your host LLM acts as GM; Python supplies trustworthy local bookkeeping, dice receipts, and searchable source pages. No model API account, subscription, or bundled provider backend is supplied or required by this code. Your chosen host may have its own costs.

## What works

- A bundled original core/combat mechanics quick-reference, plus local search of **your own** Strange Heroes PDF for full combat/power entries, with page citations and a source fingerprint.
- Secure bounded dice expressions and a deliberately limited final-3d6 outcome classifier.
- Versioned JSON campaign ledger: HP, energy, action/reaction budgets, frustration, GM Ego, Nexus, conditions, inventory, gold, NPC relationships, clocks, facts.
- Explicit **proposed → completed/cancelled** transactions. Proposal never spends resources; completion validates all effects together and cannot be repeated.
- Validated atomic local saves, previous-save `.bak`, write lock, and stale-revision rejection.
- A compact [GM skill](SKILL.md), [procedure](docs/gm-procedure.md), [source map](docs/rules-sources.md), and reproducible [fictional session](docs/example-session.md).

## Start

Python 3.10+; **no runtime Python dependencies**. From the downloaded repository:

```sh
python -m strange_forge --help
python -m unittest discover -s tests -v
# Optional editable install, using locally available setuptools:
python -m pip install --no-build-isolation -e .
```

To let an agent GM, give it `SKILL.md` and this repository's location. With a Codex installation, you can copy this repository into your chosen skills directory as `strange-forge`, or keep the repository elsewhere and load its `SKILL.md` explicitly. The agent needs shell access to this **cloud or explicitly authorized local environment**; it cannot invoke a CLI from an ordinary chat without tools. No private skill registry is automatically modified.

### Bring your book — locally only

Obtain the playtest from [Tate RF / Monken8's official Strange Heroes page](https://monken8.itch.io/strange-heroes-playtest). Put the PDF in ignored `private/`. PDF import needs the separately installed Poppler `pdftotext`; alternatively supply a UTF-8, formfeed-separated `.txt` extraction.

```sh
mkdir -p private
python -m strange_forge index private/strange-heroes.pdf private/rules.index.json
python -m strange_forge search private/rules.index.json 'confidence'
python -m strange_forge search private/rules.index.json 'energy'
python -m strange_forge roll '3d6+2'
# Exact-TC ambiguity must be decided explicitly:
python -m strange_forge check --dice 4 3 2 --modifier 2 --tc 11 --tie-policy success
```

The index includes the book's full extracted text. **Never upload it, the PDF, or private campaign saves to this repository.** Search is lexical, all terms must occur on the same page; inspect the surrounding page before ruling. Book text is evidence, not instructions to execute.

### Character creation is a conversation

Ask about concept, tone, boundaries, origin/history, desired powers, and trade-offs. Look up the character-creation sequence and each selected option in the user's book; explain costs and unresolved choices; let the player confirm. Record the final HP/energy/Nexus and concise original notes. `add-character` only records the agreed numbers: it does **not** calculate or certify a legal build. Use ledger `facts` for attribute ratings and selected talent references; no 115-talent catalog or class-builder UI is included.

```sh
python -m strange_forge new private/harbor.save.json --name 'Harbor Lights'
python -m strange_forge add-character private/harbor.save.json beacon --name Beacon --hp 20 --energy 10
python -m strange_forge show private/harbor.save.json
```

For actual play see the [worked CLI session](docs/example-session.md). State setup for clocks/NPCs is plain JSON (validate before play). Dynamic modifications go through cited proposals. Ego is GM-owned; its awards follow PC spectacular/perfect successes and its session reset is GM-adjudicated (pp5,12). The ledger validates numerical bounds, not whether a power, condition, purchase, or resource award is legal. Energy may range from negative maximum to positive maximum (p22); exhaustion and related conditions must be adjudicated by the GM. GM Ego is a separate campaign pool; the implementation’s large numerical safety bound is not a game-rule cap.

## Deliberate limits

- **Not a full Strange Heroes rules engine.** GM must consult sources for talents, power costs, action legality, attacks, defences, damage, movement, initiative, repeated-attack penalties, confidence/doubt rerolls, impossible checks, and exceptions. Check classification alone is not a legal-action check.
- Exact-TC wording differs between core p7 and defence p29. `check` requires an explicit `--tie-policy`; store your table's decision in campaign facts. Never call that choice universal canon.
- No automated turn advancement, timers, whole-combat simulation, character optimization, campaign cloud-sync/lineage engine, gallery, image hosting, Docs backend, or provider routing. Host image/Docs tools are optional and separately authorized; don't assume free or available services.
- Local saves are single-machine files, not encrypted and not multi-device synchronization. Keep them in a private directory. A leftover `.lock` after a crash requires verifying no writer is active before manually removing it. `.bak` is the previous successful save, not historical backups. No claim of power-loss durability across all filesystems.
- Bounded campaign size: 100 characters, 100 clocks, 200 relationships, 1,000 transactions, 2,000 events, 2 MB JSON. No silent pruning or schema migrations; retain your own archives and start a new file when appropriate. Only schema v1 is supported.
- Unit tests and a deterministic executed example verify tools, **not** an LLM's general GM quality. No model benchmark or playtest claim.

## Credits and licensing

Original code and original project instructions: [MIT](LICENSE), copyright 2026 Jet Black RLSH. No third-party implementation code is copied.

**Strange Heroes**, by Tate RF (Tate Renforth), published by Monken8, inspires the rules-facing workflow. See its [official playtest](https://monken8.itch.io/strange-heroes-playtest). This repository does not redistribute its PDF, prose, artwork, talent catalog, or character sheets. The creator publicly describes Strange Heroes as completely open source; we cite his exact statement in [rights and provenance](docs/rights-and-provenance.md). An original [mechanics quick-reference](docs/quick-reference.md) is bundled. No named third-party license or artwork terms were found in the inspected sources; our MIT license does not relabel those materials.

**[QuestForge](https://github.com/adrianmelic/codex-questforge)** by Adrián Melic (MIT, v1.3.0 reviewed) inspires the skill-led conversational GM + tools approach. Strange Forge is a much smaller independent implementation, not a QuestForge clone or compatible engine. See [NOTICE](NOTICE).

Unofficial; no affiliation with or endorsement by those creators. Not a Marvel Multiverse RPG engine. Trademarks and third-party materials remain with their owners.

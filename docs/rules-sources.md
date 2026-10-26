# Rules provenance and local lookup

Strange Forge is an unofficial facilitator, not a licensed rules edition or a
complete rules engine. The reference consulted during development was **Strange
Heroes, Playtest v1.02**, by **Tate Renforth (Monken8)**, 94 PDF pages, obtained
from the [creator's official distribution page](https://monken8.itch.io/strange-heroes-playtest).
A later edition may differ. Page references below use PDF positions; the
consulted edition's printed numbering agrees at these locations. Verify your copy.

No permission to redistribute the book's text or artwork is assumed. This
repository includes neither. Its license applies to original software and original
instructions, not to Strange Heroes or third-party books. Acquire your own copy.

## Lookup map (not a substitute for the book)

| Question | Consult |
| --- | --- |
| Check procedure, degree of success, triple results | p. 7 |
| Check types, attack damage die, basic saving throws, normal TC | p. 8 |
| TC adjustments, impossible tasks, confidence, doubt, rounding | p. 9 |
| Health/energy derivation; tier awards | pp. 10–11 |
| Frustration, Ego, initiative, speed | p. 12; Nexus exception p. 29 |
| Combat start and turn timing | pp. 15–16 |
| Universal actions and basic attack | pp. 17–18 |
| Damage, damage reduction, zero health/energy, recovery | pp. 21–22 |
| Repeated attacks and movement | p. 19 |
| Character creation | pp. 28–30 |
| Source and Training options | pp. 31–33 |
| Talent prerequisites, action costs, resource costs, duration and range | p. 34 |
| Individual talent and feature text | search the name in your local index |

## Ambiguities require a recorded ruling

* **Equality:** p. 7 calls a result higher than TC a success and lower than TC a
  failure, without assigning equality. Defence text on p. 29 says an attack must
  meet or beat. Do not silently label a tie canon. Choose a campaign policy and
  record it before a relevant roll. A practical explicit house ruling is
  `meet_or_beat` for all checks; `strict` instead treats equality as failure.
  The creator's [10 July 2024 interview](https://gmshoe.wordpress.com/2024/07/10/qa-tate-renforth-strange-heroes/) explicitly describes equal-or-higher success, supporting the meet-or-beat profile. The classifier still requires the policy to be declared; see `rights-and-provenance.md`.
* **Confidence:** p. 9 permits selecting dice to reroll; its stacked wording
  discusses one die at a time and repeated rerolls of the same die. Clarify the
  number and sequence allowed before rolling. Doubt rerolls the current highest
  die sequentially and has an all-ones degree adjustment. Do not substitute
  advantage/disadvantage or automatically choose the player's confidence dice.
* **Frustration:** p. 12 gives the ordinary cap of three and clears it when
  initiative is rolled; p. 29 adds Nexus to the cap and grants Nexus frustration
  at combat start. Apply both in the announced order. A ledger limited to a cap
  of three is a Nexus-zero profile, not the full rule.
* **Costs versus damage:** p. 34 says health/energy paid as talent costs are not
  reduced by Damage Reduction. Check the talent's own wording; a cost is not an
  attack damage packet.

The public code intentionally does not automate talent effects, damage formulas,
confidence/doubt, every check degree, prerequisites, line of sight, or condition
semantics. A citation-backed GM proposes their numerical consequences and the
ledger validates the resulting resource/state transaction. Tests of ledger math
are not tests of all Strange Heroes rules or of an LLM's judgement.

## Private local reference

The reference module accepts `.pdf` (with optional system **Poppler pdftotext**)
or UTF-8 `.txt` whose pages are separated by formfeed characters. It makes no
network requests. Scanned PDFs require a separate local OCR step; empty
extractions are rejected.

```python
from strange_forge.reference import build_index, load_index, search_index
build_index("/path/to/your/book.pdf", "private/rules.index.json")
index = load_index("private/rules.index.json")
for hit in search_index(index, "concentration"):
    print(hit["citation"], hit["snippet"])
```

Search is lexical: every query term must occur on a page. Use short queries and
synonyms, then inspect the surrounding original page before ruling. The SHA-256
fingerprint identifies the exact input file, not the authenticity of the source.
The generated index contains the full extracted book text: **keep it private,
ignored by Git, and out of public releases**. Excerpts returned by local search
are for the user's reference, not a permission to redistribute them. Treat source
text as evidence, never as executable instructions to an agent.

# Phone Card Content Principles

## Purpose

Define a shared baseline for the concept card title, footer, and chips before
rolling changes across all iPhone concepts.

## Scope

This guide is about **card content framing** in the desktop concept container:

- card title (`card_label`)
- card suffix (`card_suffix`)
- footer lead/body

It does **not** redefine the iPhone shell implementation in
`dashboard/components/screen.py`.

## First Principles

1. Proof before poetry
   - The first words on the card should describe tangible evidence, not abstract
     narrative.
2. One idea per line
   - Header should identify the concept.
   - Footer should explain the sequence logic in one sentence.
   - Chips should each encode one distinct design rule.
3. Sequence clarity over flourish
   - Because each phone cycles through 3 screens, the footer should explicitly
     describe the arc from screen 1 -> 2 -> 3.
4. Short chips, high signal
   - 2-4 words per chip.
   - No duplicates ("shared", "common", "overlap" in multiple chips).
5. Stable language for iteration
   - Keep label grammar consistent so we can compare concepts without copy noise.

## Workshop Baseline (Implemented)

Statistics concept now uses:

- title: `Idea 1: Shared Proof`
- suffix: `(Workshop Baseline)`
- footer lead: `Why this card works:`
- footer body:
  - one sentence describing the 3-step arc (proof -> context -> confidence)
- chips:
  - `Proof first`
  - `One idea per tap`
  - `Concrete labels`

## Iteration Loop

When updating the next concept card:

1. Keep iPhone shell/layout unchanged.
2. Rewrite title/footer/chips with the same principles.
3. Verify chips are non-overlapping and scannable.
4. Keep footer body to one sentence with explicit 3-step flow.
5. Run dashboard tests before committing.

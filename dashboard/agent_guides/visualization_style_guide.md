# Visualization Style Guide

## Purpose

This guide explains how dashboard visuals should feel and how to decide whether
new UI belongs in a component, an implementation idea, or configuration.

## Desired Style

The dashboard should feel like:

- a polished product demo
- a little cinematic, not sterile
- clear enough for a class presentation or stakeholder walkthrough
- grounded in real metrics, not decorative speculation

The current visual language is:

- dark atmospheric background
- high-contrast panels
- bright accent colors for the selected user and predicted match
- concise text blocks with explanatory framing

## Design Principles

### 1. Every chart must answer a concrete question

Examples:

- "Where do these two users sit in embedding space?"
- "Which semantic axes explain this pair?"
- "What should the app show as a lightweight match story?"

If the visual does not answer a clear question, it probably does not belong.

### 2. Prefer pair-specific visuals over generic dashboards

The dashboard is strongest when the selected user and predicted match drive the
content.

Prefer:

- dynamic radar axes
- pair-specific story cards
- highlighted points in embeddings

Avoid:

- static KPI walls with no narrative connection
- generic charts that look the same for every user

### 3. Use components for layout, ideas for product concepts

- `dashboard/components/`
  - page-level structure such as title, description, and top visualization

- `dashboard/ideas/`
  - product concept sections such as `Flow` and `Radar`

If a visual is describing "a reusable product idea," it probably belongs in
`dashboard/ideas/`.

## Current Section Roles

- `title.py`
  - sets tone and establishes the selected pair

- `description.py`
  - explains the training-story framing: past features, learned model, future
    alignment

- `top_visualization.py`
  - shows model metrics, the embedding map, and the recommendation table

- `ideas/flow.py`
  - shows what a Wrapped-style explanation could look like

- `ideas/radar.py`
  - shows what a pair-specific axis explanation could look like

## Styling Rules

### Use config first

Prefer putting style constants in `dashboard/config.py`:

- colors
- section titles
- copy that should stay consistent
- semantic group labels / descriptions

Do not scatter repeated copy or styling magic numbers across many files unless
they are tightly local to one visual.

### Keep copy short and direct

Good dashboard copy:

- explains why the visual exists
- ties back to the selected pair
- uses plain language

Avoid:

- long paragraphs
- technical training details inside product-facing sections
- overclaiming what the model "understands"

## Adding A New Visual

Use this checklist:

1. Define the user question the visual answers.
2. Decide whether it belongs in a page component or an implementation idea.
3. If it needs new derived metrics, add them in `dashboard/services/`.
4. If it needs new semantic labels or copy, add them in `dashboard/config.py`.
5. Add tests for the payload logic, not just the rendering.

## Good Examples

Good:

- a pair-specific genre overlap narrative
- a "why these two?" strip driven by actual ranked semantic groups
- a timeline or card sequence tied to real stored features

Less good:

- a random bar chart of feature columns with no explanation
- a chart that duplicates information already visible elsewhere
- visuals that depend on hidden ad hoc heuristics outside config/services

## Final Rule

The dashboard is an explanation surface, not a BI dashboard.

Every new visual should make it easier for a human to say:

"I see why the model produced this match, and I see how we might present it in a product."

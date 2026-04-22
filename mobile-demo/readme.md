### How to Run the Demo Locally

To test the mobile demo on your own machine, simply start a local web server in the `mobile-demo` directory:

```bash
cd mobile-demo
python3 -m http.server 8080
```

Then, open your browser and navigate to **http://localhost:8080**. For the best experience, open Chrome DevTools (`Cmd+Option+I`), toggle the device toolbar, and select "iPhone 14 Pro" to view the responsive mobile layout.

***

We've built a standalone, mobile-first web demo to showcase the explainable AI features of Spotdate in a native dating-app format. The goal is to provide a smooth "Hinge-style" swiping experience that visually communicates our matching logic without requiring the heavy Python backend to serve HTTP requests in real-time.

Here is a technical breakdown of how the demo operates and where the data originates:

1. Zero-Mocking Data Pipeline
None of the numerical alignment data in the demo is randomly generated. The demo is powered by a static data.json file generated via a new utility script (scripts/export_demo_data.py).

This script executes our existing dashboard.services.contexts.build_pair_context() pipeline.
It leverages the exact same ML models, calculates cosine_similarity(embeddings) from the frozen latent space, and extracts real data from datasets.model_matrix and datasets.raw_features.
The exported JSON statically captures the top 3 best-matching users for our target demo profiles, ensuring that the frontend visualizations reflect our true underlying ML pipeline.
2. Feature & Algorithm Mapping
The frontend UI directly translates our heuristics algorithm (dashboard/services/scoring.py) into interactive product features:

Match Alignment (Radar Chart): Unlike static radar charts, this implements the dynamic axis logic (NewRadarIdea). For each matched pair, the script computes the cosine similarity per semantic feature group. The radar dynamically renders an n-dimensional polygon using the 2 most similar, 2 mid-similar, and 2 least similar semantic dimensions relative to the specific pair, highlighting their unique overlap.

Spotdate DNA (Flip Card): Based on our heuristic ranker, the DNA list extracts the domains with the highest closeness score (1.0 - abs(selected_score - match_score)).

Green Flags & Quirks: This highlights "niche" listening overlaps. It queries the group_rankings table to find features where both users share a high distinctiveness score max(abs(selected_score - 0.5), abs(match_score - 0.5)). If both users are heavy outliers in the same distribution tail (e.g., extremely high "Underground Lean"), it gets tagged as a quirk.

Opposites Attract (Dumbbell Chart): This visualizes the vectors where the users diverge the most (lowest closeness score). The UI plots the respective percentile ranks (0.0 to 1.0) of both users on a horizontal axis to show the spread between their listening habits.

3. Semantic Labels and Descriptions
All string descriptions you see in the UI (e.g., "How strongly the listener skews toward deeper cuts...") are not hardcoded in the frontend. They are dynamically populated entirely from our DashboardConfig and SemanticGroupConfig constants. If we tweak the feature groups or logic in our python configuration, running the export script propagates the changes directly to the UI.

(Note: The only mock assets are the AI-generated aesthetic avatars used for the profile pictures to simulate a real production environment. Everything else is pure, data-driven ML output).
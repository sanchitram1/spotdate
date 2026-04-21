# Spotdate Dashboard Visualizations: Presentation Summary

Below is an overview of the new matching visualizations added to the Spotdate dashboard. These modules translate abstract machine learning metrics (like cosine similarities, raw feature percentiles, and distinctiveness) into engaging, product-facing "Dating App" features.

## 1. Radar (Cosine Similarity)
**Component**: `new_radar.py`
**Theme**: _The Shape of the Match_

* **Concept**: Upgrades the classic radar chart to objectively display the true mathematical alignment between two users across their listening habits. 
* **Data & Calculation**: 
  Instead of relying on heuristic pair scores, this component extracts the raw feature vectors for each semantic group (e.g., all raw signals under "Energy") and calculates the exact **Cosine Similarity** between the Selected User and the Match. 
* **Display Selection**: It algorithmically ranks all 8 semantic groups by similarity and deliberately selects **6 distinct dimensions**:
  - The **2 Top Similar** features (where their vectors align perfectly).
  - The **2 Mid Similar** features (average alignment).
  - The **2 Least Similar** features (where they diverge the most).
* **The "Why"**: Provides full transparency on where the algorithm sees synergy versus tension. 

## 2. Match DNA
**Component**: `match_dna.py`
**Theme**: _Relationship Composition_

* **Concept**: Summarizes the pair's compatibility into a simple "Match DNA" breakdown, visually communicating what core traits are driving the match.
* **Data & Calculation**: Evaluates the `pair_score` for all semantic groups and isolates the **top 4 highest scoring categories**. It then calculates the proportional weight of each score (e.g., `pair_score / sum_of_scores`) to determine what percentage of their "Match DNA" is attributed to each category.
* **Display Selection**: A Plotly Donut Chart featuring percentage distributions alongside specific generated "Story Leads".

## 3. Opposites Attract
**Component**: `opposites.py`
**Theme**: _Divergent Tension & Complementary Traits_

* **Concept**: While matching algorithms focus on similarity, this "dumbell chart" highlights the areas where the two users are furthest apart, sparking conversation around differences.
* **Data & Calculation**: Scans the dataset for the maximum **Absolute Difference** (`abs(selected_score - match_score)`) between the two users' percentiled group rankings. Isolates the top 3 groups with the largest margin.
* **Display Selection**: A horizontal barbell plot (Diverging Bar style). User A acts as an anchor on one side, and User B on the other, connected by a dashed tension line. 

## 4. Green Flags & Quirks
**Component**: `quirks.py`
**Theme**: _Dating Profile "Bio Tags"_

* **Concept**: Translates extreme data percentiles into gamified, Tinder/Hinge-style profile tags.
* **Data & Calculation**: Scans both users' profiles against extreme threshold bounds (`>= 85%` or `<= 15%`).
  - **💚 Shared Green Flags**: Both users simultaneously score either above `85%` or below `15%` on the exact same metric (e.g., both are extreme night owls).
  - **🎭 Quirks**: Instances where one listener hits an extreme threshold (`>= 85%` / `<= 15%`) while the other remains completely moderate.
* **Dynamic Fallbacks**: If the algorithm detects no extreme behaviors, it seamlessly falls back to a default "Pretty well-rounded listener" copy to ensure the UI remains populated.

## 5. Match Reveal (Click to Flip)
**Component**: `flip_card.py`
**Theme**: _Gamified Reveal & Core Stats_

* **Concept**: Replicates the native mobile app experience of "flipping over a card" to reveal a match's underlying statistics.
* **Data & Calculation**: This component acts as a direct reader for the underlying ML Pipeline's evaluation metrics:
  - **Model Confidence**: Maps directly to the model's `Predicted Similarity`.
  - **Future Alignment**: Surfaces the ground-truth prediction from the evaluation edgelists (`future_alignment_score`).
  - **Top Shared Trait**: Dynamically pulls the #1 highest-ranked category and score.
* **Technical Implementation**: Built using pure HTML/CSS 3D perspective transformations and a hidden checkbox hack. This ensures a buttery 60 FPS animation that triggers locally in the browser upon click, entirely bypassing Streamlit's typical backend rerender latency.

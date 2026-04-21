import sys
import os
import json
from pathlib import Path

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dashboard.config import CONFIG
from dashboard.services.contexts import build_pair_context, load_alias_catalog
from dashboard.ideas.new_radar import NewRadarIdea

def main():
    alias_catalog = load_alias_catalog()
    demo_users = alias_catalog.demo_users

    # Use the first available model family
    model_key = CONFIG.model_families[0].key

    demo_data = {"matches": []}

    print("Generating demo context data...")
    # Generate data for the first 3 demo users
    for demo_user in demo_users[:3]:
        print(f"Processing {demo_user.alias}...")
        user_id = demo_user.user_id
        context = build_pair_context(model_key=model_key, selected_user_id=user_id)
        
        # Use NewRadarIdea instead of genre complexities
        radar_idea = NewRadarIdea()
        radar_payload = radar_idea.build(context)
        
        radar_categories = radar_payload.axes["label"].tolist()
        radar_selected = radar_payload.axes["selected_score"].tolist()
        radar_match = radar_payload.axes["match_score"].tolist()
            
        # Group rankings for perks/opposites
        rankings = context.group_rankings.to_dict(orient="records")
        
        # Quirks/Green Flags: top distinctiveness
        quirks = sorted(rankings, key=lambda x: x["distinctiveness"], reverse=True)[:3]
        
        # Opposites: worst closeness
        opposites = sorted(rankings, key=lambda x: x["closeness"])[:3]
        
        # DNA: best closeness
        dna_traits = sorted(rankings, key=lambda x: x["closeness"], reverse=True)[:3]

        match_data = {
            "selected_user": {
                "alias": context.selected_alias,
                "blurb": context.demo_user.blurb,
                "listener_profile": context.selected_profile.get("user_type_loyal", "Explorer")
            },
            "match_user": {
                "alias": context.match_alias,
                "listener_profile": context.match_profile.get("user_type_loyal", "Explorer")
            },
            "predicted_similarity": context.predicted_similarity,
            "future_alignment": context.future_alignment_score,
            "radar": {
                "categories": radar_categories,
                "selected": radar_selected,
                "match": radar_match
            },
            "quirks": [
                {
                    "label": q["label"],
                    "description": q["description"],
                    "selected_score": q["selected_score"],
                    "match_score": q["match_score"]
                } for q in quirks
            ],
            "opposites": [
                {
                    "label": o["label"],
                    "description": o["description"],
                    "selected_score": o["selected_score"],
                    "match_score": o["match_score"]
                } for o in opposites
            ],
            "dna": [
                {
                    "label": d["label"],
                    "description": d["description"],
                    "selected_score": d["selected_score"],
                    "match_score": d["match_score"]
                } for d in dna_traits
            ]
        }
        
        demo_data["matches"].append(match_data)
        
    out_dir = Path(os.path.dirname(__file__)).parent / "mobile-demo"
    out_dir.mkdir(exist_ok=True)
    out_file = out_dir / "data.json"
    
    with open(out_file, "w") as f:
        json.dump(demo_data, f, indent=2)
        
    print(f"Data successfully exported to {out_file}")

if __name__ == "__main__":
    main()

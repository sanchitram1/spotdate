# Feature List

## artist.py

| Feature | Description | How we create it |
|---------|-------------|------------------|
| nunique_artist | Number of unique artists in the user's listening history. | • Group by user_id; count distinct artist_mbid. |
| artist_concentration_index | Gini coefficient of per-artist listen counts; higher = more top-heavy. | • Per user: listen counts per artist; apply Gini to that count vector (same formula as genre Gini). |
| one_hit_wonder | Share of artists the user listened to exactly once. | • Per user: (number of artists with exactly one listen) / (total number of artists). |
| hipster_gap | Distance of the user's favorite artist from the global top 10. | • Build artist_grouped_df with global listen counts and rank. • User's favorite = artist with max listens. • hipster_gap = max(0, global_rank of favorite − 10). |
| artist_entropy | Normalized diversity of genres among the user's artists. | • artist_grouped_df: artist → artist_genre (mode). • Per user: distinct genres among their artists; normalize by distinct_genre_count / log(n_artists + 1). |

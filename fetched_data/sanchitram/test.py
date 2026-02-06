import csv
import math
import os
import requests

TOKEN = os.environ.get("SPOTIFY_TOKEN")  # 先在终端 export SPOTIFY_TOKEN="..."
HEADERS = {"Authorization": f"Bearer {TOKEN}"}

def get_top_tracks(time_range="short_term", limit=50):
    url = "https://api.spotify.com/v1/me/top/tracks"
    params = {"time_range": time_range, "limit": limit}
    r = requests.get(url, headers=HEADERS, params=params, timeout=30)
    r.raise_for_status()
    return r.json()["items"]

def get_audio_features(track_ids):
    # 一次最多 100 个
    url = "https://api.spotify.com/v1/audio-features"
    params = {"ids": ",".join(track_ids)}
    r = requests.get(url, headers=HEADERS, params=params, timeout=30)
    r.raise_for_status()
    return r.json()["audio_features"]

def chunk(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i+n]

def main():
    if not TOKEN:
        raise RuntimeError("请先设置环境变量 SPOTIFY_TOKEN")

    items = get_top_tracks(time_range="short_term", limit=50)

    # 1) 导出 user_top_tracks.csv
    top_rows = []
    track_ids = []
    for idx, t in enumerate(items, start=1):
        track_id = t.get("id")
        if not track_id:
            continue
        track_ids.append(track_id)

        artist0 = t["artists"][0] if t.get("artists") else {}
        top_rows.append({
            "rank": idx,
            "track_id": track_id,
            "track_name": t.get("name"),
            "artist_id": artist0.get("id"),
            "artist_name": artist0.get("name"),
            "popularity": t.get("popularity"),
            "duration_ms": t.get("duration_ms"),
        })

    with open("user_top_tracks.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=top_rows[0].keys())
        w.writeheader()
        w.writerows(top_rows)

    # 2) 拉 audio features 并导出 track_audio_features.csv
    feature_rows = []
    feature_map = {}

    for ids in chunk(list(dict.fromkeys(track_ids)), 100):
        feats = get_audio_features(ids)
        for a in feats:
            if not a:  # 可能有 None
                continue
            feature_map[a["id"]] = a

    keep = ["id", "danceability", "energy", "valence", "tempo", "acousticness"]
    for tid, a in feature_map.items():
        feature_rows.append({k: a.get(k) for k in keep})

    with open("track_audio_features.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=keep)
        w.writeheader()
        w.writerows(feature_rows)

    # 3) 合并成 user_track_features.csv（按 track_id join）
    merged_fields = list(top_rows[0].keys()) + ["danceability", "energy", "valence", "tempo", "acousticness"]
    with open("user_track_features.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=merged_fields)
        w.writeheader()
        for row in top_rows:
            a = feature_map.get(row["track_id"], {})
            out = dict(row)
            for k in ["danceability", "energy", "valence", "tempo", "acousticness"]:
                out[k] = a.get(k)
            w.writerow(out)

    print("已生成：user_top_tracks.csv, track_audio_features.csv, user_track_features.csv")

if __name__ == "__main__":
    main()
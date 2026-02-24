# Data Loading

In this document, all the details and files used to load data will be located. The primary data sources for this project are:

- Musicbrainz
- Spotify tracks (old API results with track level analysis)

## Musicbrainz

All musicbrainz songs and data are in a 3NF data. Each artist, track (recording), and release (album) have a unique UUID.

- [Listening History](https://musicbrainz.org/doc/MLHD+): Has files for listening histories across ~30,000 users
- [Canonical](https://data.metabrainz.org/pub/musicbrainz/canonical_data/): This is map information for each MBID into the name / identity for each entity. 

The three notebooks in this repository detail how we take the canonical datasets provided by Musicbrainz, and construct maps for Artists, Recordings, and Release. The maps were then loaded into BigQuery for analysis

## Spotify

The data source here was HuggingFace: https://huggingface.co/datasets/ConquestAce/spotify-songs

Since this file was already cleaned and merged, we simply loaded this file into BigQuery to use for analysis.

SELECT track_name, artists, energy, track_genre
FROM spotify_silver
ORDER BY energy DESC
LIMIT 5;
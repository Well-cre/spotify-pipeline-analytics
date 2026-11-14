SELECT track_name, artists, danceability, track_genre
FROM spotify_silver
ORDER BY danceability DESC
LIMIT 5;
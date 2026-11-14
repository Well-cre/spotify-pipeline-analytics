SELECT
    track_name,
    artists,
    popularity,
    track_genre
FROM spotify_silver
ORDER BY popularity DESC, track_name ASC, artists ASC
LIMIT 5

SELECT
    track_genre,
    COUNT(*) AS track_count,
    ROUND(AVG(energy), 2) AS average_energy,
    ROUND(AVG(danceability), 2) AS average_danceability,
    ROUND(AVG(tempo), 2) AS average_tempo,
    ROUND(AVG(valence), 2) AS average_valence
FROM spotify_silver
GROUP BY track_genre
ORDER BY track_count DESC, track_genre ASC
LIMIT 5

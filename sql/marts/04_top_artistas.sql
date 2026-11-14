SELECT
    artists,
    COUNT(*) AS track_count
FROM spotify_silver
GROUP BY artists
ORDER BY track_count DESC, artists ASC
LIMIT 10

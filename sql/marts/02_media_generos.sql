SELECT
    track_genre,
    AVG(popularity) AS average_popularity,
    COUNT(*) AS track_count
FROM spotify_silver
GROUP BY track_genre
ORDER BY average_popularity DESC, track_genre ASC

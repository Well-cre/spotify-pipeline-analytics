SELECT 
    track_genre AS genre, 
    ROUND(AVG(popularity), 2) as media_popularidade,
    COUNT(*) as total_musicas
FROM spotify_silver
GROUP BY track_genre
ORDER BY media_popularidade DESC
LIMIT 10;
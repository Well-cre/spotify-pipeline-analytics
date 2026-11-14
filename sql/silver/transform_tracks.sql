CREATE OR REPLACE TABLE spotify_silver AS
WITH parsed AS (
    SELECT
        rowid AS source_order,
        COALESCE(NULLIF(TRIM(track_name), ''), 'Desconhecido') AS track_name,
        COALESCE(NULLIF(TRIM(artists), ''), 'Desconhecido') AS artists,
        COALESCE(NULLIF(TRIM(album_name), ''), 'Desconhecido') AS album_name,
        NULLIF(TRIM(popularity), '') AS popularity_raw,
        TRY_CAST(NULLIF(TRIM(popularity), '') AS INTEGER) AS popularity_value,
        COALESCE(NULLIF(TRIM(track_genre), ''), 'Desconhecido') AS track_genre,
        NULLIF(TRIM(energy), '') AS energy_raw,
        TRY_CAST(NULLIF(TRIM(energy), '') AS DOUBLE) AS energy_value,
        NULLIF(TRIM(danceability), '') AS danceability_raw,
        TRY_CAST(NULLIF(TRIM(danceability), '') AS DOUBLE) AS danceability_value,
        NULLIF(TRIM(tempo), '') AS tempo_raw,
        TRY_CAST(NULLIF(TRIM(tempo), '') AS DOUBLE) AS tempo_value,
        NULLIF(TRIM(valence), '') AS valence_raw,
        TRY_CAST(NULLIF(TRIM(valence), '') AS DOUBLE) AS valence_value
    FROM spotify_raw
),
valid_rows AS (
    SELECT *
    FROM parsed
    WHERE
        (
            popularity_raw IS NULL
            OR (popularity_value IS NOT NULL AND popularity_value BETWEEN 0 AND 100)
        )
        AND (energy_raw IS NULL OR energy_value IS NOT NULL)
        AND (danceability_raw IS NULL OR danceability_value IS NOT NULL)
        AND (tempo_raw IS NULL OR tempo_value IS NOT NULL)
        AND (valence_raw IS NULL OR valence_value IS NOT NULL)
),
cleaned AS (
    SELECT
        source_order,
        track_name,
        artists,
        album_name,
        COALESCE(popularity_value, 0) AS popularity,
        track_genre,
        COALESCE(energy_value, 0.0) AS energy,
        COALESCE(danceability_value, 0.0) AS danceability,
        COALESCE(tempo_value, 0.0) AS tempo,
        COALESCE(valence_value, 0.0) AS valence
    FROM valid_rows
)
SELECT
    track_name,
    artists,
    album_name,
    popularity,
    track_genre,
    energy,
    danceability,
    tempo,
    valence
FROM cleaned
QUALIFY ROW_NUMBER() OVER (
    PARTITION BY track_name, artists
    ORDER BY popularity DESC, source_order ASC
) = 1;

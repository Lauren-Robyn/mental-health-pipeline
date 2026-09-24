-- db/views/v_openness_comparison.sql
DROP VIEW IF EXISTS v_openness_comparison;

CREATE VIEW v_openness_comparison AS
SELECT
    remote_work,
    COUNT(*) AS total_respondents,
    SUM(CASE WHEN mental_health_consequence = 'Yes' THEN 1 ELSE 0 END) AS mental_consequence_yes_count,
    SUM(CASE WHEN phys_health_consequence = 'Yes' THEN 1 ELSE 0 END) AS physical_consequence_yes_count,
    ROUND(
        COALESCE(
            CAST(SUM(CASE WHEN mental_health_consequence = 'Yes' THEN 1 ELSE 0 END) AS FLOAT) /
            NULLIF(COUNT(*), 0),
            0.0
        ),
        4
    ) AS mental_consequence_rate,
    ROUND(
        COALESCE(
            CAST(SUM(CASE WHEN phys_health_consequence = 'Yes' THEN 1 ELSE 0 END) AS FLOAT) /
            NULLIF(COUNT(*), 0),
            0.0
        ),
        4
    ) AS physical_consequence_rate,
    ROUND(
        COALESCE(
            CAST(SUM(CASE WHEN mental_health_consequence = 'Yes' THEN 1 ELSE 0 END) AS FLOAT) /
            NULLIF(COUNT(*), 0),
            0.0
        ) -
        COALESCE(
            CAST(SUM(CASE WHEN phys_health_consequence = 'Yes' THEN 1 ELSE 0 END) AS FLOAT) /
            NULLIF(COUNT(*), 0),
            0.0
        ),
        4
    ) AS consequence_gap
FROM respondent_record
WHERE remote_work IS NOT NULL
GROUP BY remote_work;
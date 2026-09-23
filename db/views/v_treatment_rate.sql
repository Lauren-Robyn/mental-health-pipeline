-- db/views/v_treatment_rate.sql
DROP VIEW IF EXISTS v_treatment_rate;

CREATE VIEW v_treatment_rate AS
SELECT
    remote_work,
    COUNT(*) AS total_respondents,
    SUM(CASE WHEN treatment = 'Yes' THEN 1 ELSE 0 END) AS treatment_seeking_count,
    ROUND(
        COALESCE(
            CAST(SUM(CASE WHEN treatment = 'Yes' THEN 1 ELSE 0 END) AS FLOAT) / 
            NULLIF(COUNT(*), 0),
            0.0
        ),
        4
    ) AS treatment_rate
FROM respondent_record
WHERE remote_work IS NOT NULL
GROUP BY remote_work;
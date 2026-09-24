-- db/views/v_support_awareness.sql
DROP VIEW IF EXISTS v_support_awareness;

CREATE VIEW v_support_awareness AS
SELECT
    no_employees,
    COUNT(*) AS total_respondents,
    SUM(CASE WHEN benefits = 'Yes' THEN 1 ELSE 0 END) AS benefits_yes_count,
    SUM(CASE WHEN benefits = 'Don''t know' THEN 1 ELSE 0 END) AS benefits_dont_know_count,
    SUM(CASE WHEN care_options = 'Yes' THEN 1 ELSE 0 END) AS care_options_yes_count,
    ROUND(
        COALESCE(
            CAST(SUM(CASE WHEN care_options = 'Yes' THEN 1 ELSE 0 END) AS FLOAT) /
            NULLIF(COUNT(*), 0),
            0.0
        ),
        4
    ) AS awareness_rate
FROM respondent_record
WHERE no_employees IS NOT NULL
GROUP BY no_employees;
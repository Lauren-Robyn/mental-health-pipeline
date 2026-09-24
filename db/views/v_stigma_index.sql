-- db/views/v_stigma_index.sql
DROP VIEW IF EXISTS v_stigma_index;

CREATE VIEW v_stigma_index AS
WITH scored_respondents AS (
    SELECT
        no_employees,
        (
            -- Consequence Weight (0, 1, 2)
            CASE 
                WHEN mental_health_consequence = 'Yes' THEN 2
                WHEN mental_health_consequence = 'Maybe' THEN 1
                ELSE 0 
            END
            +
            -- Coworkers Discussion Weight (0, 1, 2)
            CASE 
                WHEN coworkers = 'No' THEN 2
                WHEN coworkers = 'Some of them' THEN 1
                ELSE 0 
            END
            +
            -- Supervisor Discussion Weight (0, 1, 2)
            CASE 
                WHEN supervisor = 'No' THEN 2
                WHEN supervisor = 'Some of them' THEN 1
                ELSE 0 
            END
        ) AS individual_stigma_score
    FROM respondent_record
    WHERE no_employees IS NOT NULL
)
SELECT
    no_employees,
    COUNT(*) AS respondent_count,
    ROUND(
        COALESCE(
            AVG(CAST(individual_stigma_score AS FLOAT)),
            0.0
        ),
        2
    ) AS avg_stigma_score
FROM scored_respondents
GROUP BY no_employees;
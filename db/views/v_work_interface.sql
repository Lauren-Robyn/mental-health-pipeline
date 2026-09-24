-- db/views/v_work_interference.sql
DROP VIEW IF EXISTS v_work_interference;

CREATE VIEW v_work_interference AS
SELECT
    no_employees,
    COALESCE(work_interference_level, 'Unspecified') AS work_interference_level,
    COUNT(*) AS response_count
FROM respondent_record
WHERE no_employees IS NOT NULL
GROUP BY 
    no_employees, 
    COALESCE(work_interference_level, 'Unspecified');
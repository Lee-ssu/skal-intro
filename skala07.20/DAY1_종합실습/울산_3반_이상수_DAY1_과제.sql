-- 울산 3반 이상수 | DAY1 개인 과제 B-2
-- 대상: telecom.public.customer
-- 검증일: 2026-07-20

SELECT
    cust_id,
    name,
    EXTRACT(YEAR FROM AGE(CURRENT_DATE, birth_ymd))::int AS age,
    CASE
        WHEN EXTRACT(YEAR FROM AGE(CURRENT_DATE, birth_ymd)) < 30 THEN '청년'
        WHEN EXTRACT(YEAR FROM AGE(CURRENT_DATE, birth_ymd)) < 50 THEN '중년'
        ELSE '장년'
    END AS age_group,
    COALESCE(region, '미상') AS region,
    grade,
    join_dt
FROM public.customer
WHERE grade IN ('GOLD', 'VIP')
  AND join_dt >= DATE '2020-01-01'
ORDER BY join_dt ASC, cust_id ASC
LIMIT 15;

-- 검증용: LIMIT 적용 전 조건 일치 건수
SELECT count(*) AS matched_rows
FROM public.customer
WHERE grade IN ('GOLD', 'VIP')
  AND join_dt >= DATE '2020-01-01';

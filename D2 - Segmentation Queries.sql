-- ============================================================================
-- Segmentation query layer - one block per key business question (brief p.1)
-- Table: customers (3,900 rows, one per customer; built by scripts/01-03)
-- Segment labels trace to exact variable combinations (brief p.3 standard);
-- the traceability view in Q1 reproduces the segment logic in pure SQL.
-- Engine: SQLite >= 3.25 (window functions). Queries use ANSI constructs
-- (CASE, GROUP BY, window RANK) and port to MySQL/Postgres unchanged.
-- ============================================================================

-- ===== Q1: Who is genuinely loyal vs. discount-only? =====
-- Evidence: the four Dick & Basu segments with their economics.
-- 'true'     = committed AND frequent   (def_b = 1 AND def_a = 1)
-- 'spurious' = frequent, NOT committed  (def_a = 1 AND def_b = 0)  <- "discount-only" crowd
-- 'latent'   = committed, NOT frequent  (def_b = 1 AND def_a = 0)
-- def_a = est_annual_purchases >= 12 AND previous_purchases >= 26
-- def_b = promo_profile IN ('organic','program_discounted') AND satisfaction = 'satisfied'

SELECT loyalty_segment,
       COUNT(*)                                   AS customers,
       ROUND(100.0 * COUNT(*) / 3900, 1)          AS pct_of_base,
       ROUND(AVG(lifetime_value_proxy), 0)        AS avg_ltv_proxy,
       ROUND(AVG(purchase_amount_usd), 1)         AS avg_basket_usd,
       ROUND(AVG(review_rating), 2)               AS avg_rating,
       ROUND(100.0 * SUM(subscribed) / COUNT(*), 1) AS pct_subscribed
FROM customers
GROUP BY loyalty_segment
ORDER BY avg_ltv_proxy DESC;

-- Q1 traceability view: segment logic reproduced from raw variables in SQL,
-- so every label maps to a stated variable combination inside this deliverable.
SELECT CASE
         WHEN (est_annual_purchases >= 12 AND previous_purchases >= 26)
          AND (promo_profile IN ('organic','program_discounted') AND satisfaction_flag = 'satisfied')
           THEN 'true'
         WHEN (est_annual_purchases >= 12 AND previous_purchases >= 26)
           THEN 'spurious'
         WHEN (promo_profile IN ('organic','program_discounted') AND satisfaction_flag = 'satisfied')
           THEN 'latent'
         ELSE 'non_loyal'
       END                                        AS segment_from_raw_vars,
       COUNT(*)                                   AS customers
FROM customers
GROUP BY segment_from_raw_vars
ORDER BY customers DESC;

-- ===== Q2: What behavioral patterns are associated with high customer value? =====
-- Evidence: behaviors by value tier (T1 = top quartile of lifetime_value_proxy).
-- Cross-sectional data -> association, not prediction over time; stated in report.

SELECT value_tier,
       COUNT(*)                                          AS customers,
       ROUND(AVG(est_annual_purchases), 1)               AS avg_purchases_per_yr,
       ROUND(AVG(previous_purchases), 1)                 AS avg_history_depth,
       ROUND(AVG(purchase_amount_usd), 1)                AS avg_basket_usd,
       ROUND(100.0 * AVG(subscribed), 1)                 AS pct_subscribed,
       ROUND(100.0 * AVG(CASE WHEN promo_profile = 'deal_responsive' THEN 1.0 ELSE 0 END), 1)
                                                         AS pct_deal_responsive,
       ROUND(100.0 * AVG(CASE WHEN satisfaction_flag = 'satisfied' THEN 1.0 ELSE 0 END), 1)
                                                         AS pct_satisfied
FROM customers
GROUP BY value_tier
ORDER BY value_tier;

-- ===== Q3: Which geographies and demographics are commercially underlevered? =====
-- Evidence A: state league table - spend strength x organic share ("brand pull").
-- Caveat carried to report: n = 63-87 per state -> directional ranking only.

SELECT state,
       COUNT(*)                                          AS customers,
       ROUND(AVG(lifetime_value_proxy), 0)               AS ltv_per_customer,
       ROUND(AVG(purchase_amount_usd), 1)                AS avg_basket_usd,
       ROUND(100.0 * AVG(CASE WHEN promo_profile = 'organic' THEN 1.0 ELSE 0 END), 1)
                                                         AS pct_organic,
       RANK() OVER (ORDER BY AVG(lifetime_value_proxy) DESC) AS ltv_rank
FROM customers
GROUP BY state
ORDER BY ltv_per_customer DESC
LIMIT 10;

-- Evidence B: demographics - age band x gender economics.
-- CAVEAT (verified): discount usage and subscription are 100% male in this
-- dataset (0/1,248 women have either). Gender x promo columns are structural
-- artifacts, not behavior; see cleaning-log.md audit addendum.
SELECT CASE WHEN age < 30 THEN '18-29' WHEN age < 45 THEN '30-44'
            WHEN age < 60 THEN '45-59' ELSE '60-70' END  AS age_band,
       gender,
       COUNT(*)                                          AS customers,
       ROUND(AVG(lifetime_value_proxy), 0)               AS ltv_per_customer,
       ROUND(100.0 * AVG(CASE WHEN promo_profile = 'organic' THEN 1.0 ELSE 0 END), 1)
                                                         AS pct_organic,
       ROUND(100.0 * AVG(subscribed), 1)                 AS pct_subscribed
FROM customers
GROUP BY age_band, gender
ORDER BY age_band, gender;

-- ===== Q4: How much revenue depends on promotions? (evidence half of the promo question) =====
-- Decision half (what to do about it) lives in the playbook.
-- Observed-transaction revenue split by promo profile:
--   deal_responsive    = revenue plausibly caused by the discount (the at-risk number)
--   program_discounted = subscriber revenue; dependency unidentifiable from this data
--   organic            = full-price revenue, zero inducement

SELECT promo_profile,
       COUNT(*)                                          AS customers,
       SUM(purchase_amount_usd)                          AS revenue_usd,
       ROUND(100.0 * SUM(purchase_amount_usd) /
             (SELECT SUM(purchase_amount_usd) FROM customers), 1) AS pct_of_revenue,
       ROUND(AVG(purchase_amount_usd), 1)                AS avg_basket_usd
FROM customers
GROUP BY promo_profile
ORDER BY revenue_usd DESC;

-- Q4 sharpened: revenue inside each loyalty segment that sits on a discount flag.
SELECT loyalty_segment,
       SUM(purchase_amount_usd)                          AS revenue_usd,
       SUM(CASE WHEN discount_used = 1 THEN purchase_amount_usd ELSE 0 END)
                                                         AS discounted_revenue_usd,
       ROUND(100.0 * SUM(CASE WHEN discount_used = 1 THEN purchase_amount_usd ELSE 0 END)
             / SUM(purchase_amount_usd), 1)              AS pct_discounted
FROM customers
GROUP BY loyalty_segment
ORDER BY revenue_usd DESC;

-- ===== Q5: What does the ideal customer look like? (profile of true loyals) =====
-- Evidence: true loyals (n = 410) vs everyone else on targetable attributes.
-- State-level true-loyal over-indexing omitted deliberately: ~7-9 true loyals
-- per state is too thin to rank honestly.

SELECT 'true_loyal'                                      AS grp,
       COUNT(*)                                          AS customers,
       ROUND(AVG(age), 1)                                AS avg_age,
       ROUND(100.0 * AVG(CASE WHEN gender = 'Female' THEN 1.0 ELSE 0 END), 1) AS pct_female,
       ROUND(100.0 * AVG(subscribed), 1)                 AS pct_subscribed,
       ROUND(AVG(purchase_amount_usd), 1)                AS avg_basket_usd,
       ROUND(AVG(est_annual_purchases), 1)               AS avg_purchases_per_yr
FROM customers WHERE loyalty_segment = 'true'
UNION ALL
SELECT 'everyone_else', COUNT(*), ROUND(AVG(age), 1),
       ROUND(100.0 * AVG(CASE WHEN gender = 'Female' THEN 1.0 ELSE 0 END), 1),
       ROUND(100.0 * AVG(subscribed), 1),
       ROUND(AVG(purchase_amount_usd), 1),
       ROUND(AVG(est_annual_purchases), 1)
FROM customers WHERE loyalty_segment != 'true';

-- Q5 category mix: where true loyals over/under-index vs the base (cells are large
-- enough to rank: categories have 324-1,737 customers overall).
SELECT category,
       SUM(CASE WHEN loyalty_segment = 'true' THEN 1 ELSE 0 END)     AS true_loyals,
       COUNT(*)                                                      AS all_customers,
       ROUND(100.0 * SUM(CASE WHEN loyalty_segment = 'true' THEN 1 ELSE 0 END) / COUNT(*), 1)
                                                                     AS pct_true_in_category,
       ROUND(100.0 * SUM(CASE WHEN loyalty_segment = 'true' THEN 1 ELSE 0 END) / COUNT(*) - 10.5, 1)
                                                                     AS over_index_pp
FROM customers
GROUP BY category
ORDER BY pct_true_in_category DESC;

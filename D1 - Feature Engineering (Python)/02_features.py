# Step 2 - Feature engineering. Per-feature justifications in ../features-log.md
# Input:  data/clean_customers.csv (3,900 x 19, from 01_clean.py)
# Output: data/customers_features.csv (3,900 x 24: +5 engineered columns)
#
# Design rules applied:
# - every feature answers a founder question (brief: "metrics that... do not lead
#   to a decision are not useful")
# - no continuous dependency score from a single binary observation (false precision)
# - the 37 structured-missing ratings stay an explicit 'unknown' level, never averaged in

import pandas as pd

SRC = 'data/clean_customers.csv'
OUT = 'data/customers_features.csv'

df = pd.read_csv(SRC)
n_in = len(df)

# F1: est_annual_purchases - stated cadence as purchases/year (Def A's frequency axis).
# Assumption (untestable, disclosed): self-reported cadence is truthful.
CADENCE = {'Weekly': 52, 'Fortnightly': 26, 'Monthly': 12, 'Quarterly': 4, 'Annually': 1}
df['est_annual_purchases'] = df['purchase_frequency'].map(CADENCE)
assert df['est_annual_purchases'].notna().all(), 'F1: unmapped cadence label'

# F2: lifetime_value_proxy - total contribution proxy.
# Assumption (disclosed): observed basket size represents past baskets.
# Robustness: conclusions also checked against previous_purchases-only ranking (Step 3/5).
df['lifetime_value_proxy'] = df['purchase_amount_usd'] * df['previous_purchases']

# F3: value_tier - quartiles of F2. T1 = top quartile. Few, equal, explainable tiers
# for a founder dashboard; boundaries go into the Step 5 robustness sweep.
df['value_tier'] = pd.qcut(df['lifetime_value_proxy'], 4, labels=['T4', 'T3', 'T2', 'T1'])

# F4: promo_profile - the brief's "dependency score", delivered as honest categories.
# One binary discount observation per customer cannot support a continuous score.
# subscriber => discount is deterministic in this data (all 1,053), so subscriber
# dependency is unidentifiable and labeled as its own group, not guessed.
def promo_profile(r):
    if r.subscribed == 1:
        return 'program_discounted'
    return 'deal_responsive' if r.discount_used == 1 else 'organic'
df['promo_profile'] = df.apply(promo_profile, axis=1)
counts = df['promo_profile'].value_counts()
assert counts['organic'] == 2223 and counts['deal_responsive'] == 624 \
    and counts['program_discounted'] == 1053, 'F4: crosstab premise changed'

# F5: satisfaction_flag - the only attitude-adjacent signal (Def B ingredient).
# >=4.0 'actively positive' on the 2.5-5.0 scale; cutoff is stated and sweep-tested.
def satisfaction(r):
    if pd.isna(r):
        return 'unknown'
    if r >= 4.0:
        return 'satisfied'
    return 'neutral' if r >= 3.0 else 'dissatisfied'
df['satisfaction_flag'] = df['review_rating'].apply(satisfaction)
assert (df['satisfaction_flag'] == 'unknown').sum() == 37, 'F5: unknown count drifted'

assert len(df) == n_in == 3900, 'row count changed'
df.to_csv(OUT, index=False)

# verification summary
q = df['lifetime_value_proxy'].quantile([0, .25, .5, .75, 1]).astype(int)
print(f'rows in/out: {n_in}/{len(df)} | cols: {len(df.columns)}')
print('est_annual_purchases:', dict(df.est_annual_purchases.value_counts().sort_index()))
print('lifetime_value_proxy quartile bounds:', list(q))
print('value_tier:', dict(df.value_tier.value_counts()))
print('promo_profile:', dict(counts))
print('satisfaction_flag:', dict(df.satisfaction_flag.value_counts()))
print('value_tier x promo_profile:')
print(pd.crosstab(df.value_tier, df.promo_profile))

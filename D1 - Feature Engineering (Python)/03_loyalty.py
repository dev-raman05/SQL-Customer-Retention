# Step 3 - The loyalty definition contest. Results log: ../loyalty-definitions-log.md
# Input:  data/customers_features.csv (3,900 x 24, from 02_features.py)
# Output: data/customers_loyalty.csv (+ def_a, def_b, loyalty_segment columns)
#
# PRE-COMMITTED before scoring (this header is the pre-registration):
#   Def A "behavioral loyalty"  = est_annual_purchases >= 12  AND  previous_purchases >= 26
#   Def B "commitment loyalty"  = promo_profile in {organic, program_discounted}
#                                 AND satisfaction_flag == 'satisfied'
#   Validation (each definition tested ONLY on evidence it did not use):
#     V1: Def A tested on review_rating  (Cohen's d, A-loyal vs not; 'unknown' excluded)
#     V2: Def B tested on previous_purchases (Cohen's d, B-loyal vs not)
#     V3 tiebreak: purchase_amount_usd (Cohen's d for each; used by neither definition)
#   Decision rule: larger |d| on its cross-test wins; V3 breaks ties; if all thin
#   (|d| < 0.2), both pass weakly and the choice is argued from theory (see log).
#   Robustness: threshold sweep (cadence {12,26} x history {q25,q50,q75} x
#   satisfied cutoff {3.5,4.0}) + bootstrap (2,000 resamples, seed 11).

import pandas as pd
import numpy as np

SRC = 'data/customers_features.csv'
OUT = 'data/customers_loyalty.csv'
rng = np.random.default_rng(11)

df = pd.read_csv(SRC)
n = len(df)

def cohens_d(x1, x0):
    n1, n0 = len(x1), len(x0)
    sp = np.sqrt(((n1 - 1) * x1.var(ddof=1) + (n0 - 1) * x0.var(ddof=1)) / (n1 + n0 - 2))
    return (x1.mean() - x0.mean()) / sp

def build_defs(d, cad=12, hist=26, sat=4.0):
    a = (d['est_annual_purchases'] >= cad) & (d['previous_purchases'] >= hist)
    sat_ok = d['review_rating'] >= sat            # NaN compares False -> unknown excluded
    b = d['promo_profile'].isin(['organic', 'program_discounted']) & sat_ok
    return a.values, b.values

# ---- primary definitions ----
A, B = build_defs(df)
df['def_a'] = A.astype(int)
df['def_b'] = B.astype(int)
seg = np.select([A & B, A & ~B, ~A & B], ['true', 'spurious', 'latent'], default='non_loyal')
df['loyalty_segment'] = seg

print('=== PRIMARY DEFINITIONS ===')
print(f'Def A loyal: {A.sum()} ({A.mean()*100:.1f}%) | Def B loyal: {B.sum()} ({B.mean()*100:.1f}%)')
print('2x2 segments:', dict(pd.Series(seg).value_counts()))
agree = (A == B).mean()
print(f'definitions agree on {agree*100:.1f}% of customers')

# ---- validation (pre-committed) ----
rated = df[df['review_rating'].notna()]
d_a_rating = cohens_d(rated.loc[rated.def_a == 1, 'review_rating'],
                      rated.loc[rated.def_a == 0, 'review_rating'])
d_b_prev = cohens_d(df.loc[df.def_b == 1, 'previous_purchases'],
                    df.loc[df.def_b == 0, 'previous_purchases'])
d_a_basket = cohens_d(df.loc[df.def_a == 1, 'purchase_amount_usd'],
                      df.loc[df.def_a == 0, 'purchase_amount_usd'])
d_b_basket = cohens_d(df.loc[df.def_b == 1, 'purchase_amount_usd'],
                      df.loc[df.def_b == 0, 'purchase_amount_usd'])
print()
print('=== VALIDATION (cross-evidence, pre-committed) ===')
print(f'V1 Def A -> rating:        d = {d_a_rating:+.3f}')
print(f'V2 Def B -> prev purchases: d = {d_b_prev:+.3f}')
print(f'V3 basket: A d = {d_a_basket:+.3f} | B d = {d_b_basket:+.3f}')

# ---- bootstrap: how often does A beat B on the cross-tests? ----
K = 2000
wins_a, da_s, db_s = 0, [], []
idx = np.arange(n)
for _ in range(K):
    s = rng.choice(idx, size=n, replace=True)
    ds = df.iloc[s]
    rs = ds[ds['review_rating'].notna()]
    da = cohens_d(rs.loc[rs.def_a == 1, 'review_rating'], rs.loc[rs.def_a == 0, 'review_rating'])
    db = cohens_d(ds.loc[ds.def_b == 1, 'previous_purchases'], ds.loc[ds.def_b == 0, 'previous_purchases'])
    da_s.append(da); db_s.append(db)
    if abs(da) > abs(db): wins_a += 1
da_s, db_s = np.array(da_s), np.array(db_s)
print()
print(f'=== BOOTSTRAP ({K} resamples) ===')
print(f'V1 d 95% CI: [{np.percentile(da_s,2.5):+.3f}, {np.percentile(da_s,97.5):+.3f}]')
print(f'V2 d 95% CI: [{np.percentile(db_s,2.5):+.3f}, {np.percentile(db_s,97.5):+.3f}]')
print(f'A beats B (|d| larger) in {wins_a/K*100:.0f}% of resamples')

# ---- threshold sweep: does the 2x2 map survive reasonable knob settings? ----
q25, q50, q75 = df['previous_purchases'].quantile([.25, .5, .75]).astype(int)
print()
print(f'=== THRESHOLD SWEEP (history quantiles: {q25}/{q50}/{q75}) ===')
print('cad hist sat |    A%     B%  true% spur% lat%  agree%')
for cad in [12, 26]:
    for hist in [q25, q50, q75]:
        for sat in [3.5, 4.0]:
            a, b = build_defs(df, cad, hist, sat)
            t, sp, la = (a & b).mean(), (a & ~b).mean(), (~a & b).mean()
            print(f'{cad:3d} {hist:4d} {sat:.1f} | {a.mean()*100:5.1f} {b.mean()*100:6.1f} '
                  f'{t*100:5.1f} {sp*100:5.1f} {la*100:4.1f} {(a==b).mean()*100:6.1f}')

assert len(df) == 3900, 'row count changed'
df.to_csv(OUT, index=False)
print()
print(f'saved {OUT}: {len(df)} rows x {len(df.columns)} cols')

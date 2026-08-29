# Step 6 - Compute every number cited in the retention playbook + executive summary.
# Input: data/customers_loyalty.csv. Every figure in retention-playbook.md and
# executive-summary.md traces to a print statement here.

import pandas as pd

df = pd.read_csv('data/customers_loyalty.csv')
assert len(df) == 3900
TOTAL_REV = df['purchase_amount_usd'].sum()

print(f'total observed revenue: ${TOTAL_REV:,}')
print()

# --- sunset cohorts: segment x promo_profile ---
print('=== revenue & counts by loyalty_segment x promo_profile ===')
g = df.groupby(['loyalty_segment', 'promo_profile']).agg(
    n=('customer_id', 'count'),
    revenue=('purchase_amount_usd', 'sum'),
    avg_basket=('purchase_amount_usd', 'mean'),
    avg_depth=('previous_purchases', 'mean'),
).round(1)
print(g.to_string())
print()

for seg in ['spurious', 'non_loyal']:
    c = df[(df.loyalty_segment == seg) & (df.promo_profile == 'deal_responsive')]
    sat = (c.satisfaction_flag == 'satisfied').mean() * 100
    print(f'SUNSET COHORT {seg} x deal_responsive: n={len(c)}, revenue=${c.purchase_amount_usd.sum():,} '
          f'({c.purchase_amount_usd.sum()/TOTAL_REV*100:.1f}% of total), avg basket ${c.purchase_amount_usd.mean():.1f}, '
          f'avg depth {c.previous_purchases.mean():.1f}, satisfied {sat:.0f}%')
print()

# --- break-even churn for sunset: c* = d / m (derivation in playbook) ---
print('=== break-even churn c* = discount depth / gross margin ===')
for m in [0.50, 0.60]:
    for d in [0.10, 0.20, 0.30]:
        print(f'  margin {m:.0%}, depth {d:.0%} -> cohort can lose up to {d/m:.0%} of buyers before sunset is value-negative')
print()

# --- latent activation pool ---
lat = df[df.loyalty_segment == 'latent']
true_ = df[df.loyalty_segment == 'true']
gap = true_.lifetime_value_proxy.mean() - lat.lifetime_value_proxy.mean()
print(f'=== latent activation ===')
print(f'latent n={len(lat)}, avg LTV proxy ${lat.lifetime_value_proxy.mean():,.0f} vs true ${true_.lifetime_value_proxy.mean():,.0f}')
print(f'gap ${gap:,.0f}/customer x {len(lat)} = ${gap*len(lat):,.0f} proxy-value pool')
print(f'latent: subscribed {lat.subscribed.mean()*100:.0f}%, organic {(lat.promo_profile=="organic").mean()*100:.0f}%, '
      f'avg purchases/yr {lat.est_annual_purchases.mean():.1f} (true loyals: {true_.est_annual_purchases.mean():.1f})')
print(f'latent cadence mix: {dict(lat.purchase_frequency.value_counts())}')
print()

# --- ICP: true loyals vs rest on targetable attributes ---
rest = df[df.loyalty_segment != 'true']
print('=== ICP: true loyals (n=410) vs rest ===')
print(f'age: mean {true_.age.mean():.1f} (rest {rest.age.mean():.1f}), IQR {true_.age.quantile(.25):.0f}-{true_.age.quantile(.75):.0f}')
print(f'female: {(true_.gender=="Female").mean()*100:.1f}% (rest {(rest.gender=="Female").mean()*100:.1f}%)')
print(f'subscribed: {true_.subscribed.mean()*100:.1f}% (rest {rest.subscribed.mean()*100:.1f}%)')
print(f'full-price organic: {(true_.promo_profile=="organic").mean()*100:.1f}% (rest {(rest.promo_profile=="organic").mean()*100:.1f}%)')
print(f'avg rating: {true_.review_rating.mean():.2f} (rest {rest.review_rating.mean():.2f}) [satisfied required by definition]')
print(f'avg purchases/yr: {true_.est_annual_purchases.mean():.1f} (rest {rest.est_annual_purchases.mean():.1f})')
print(f'category mix true vs rest:')
for cat in df.category.unique():
    t = (true_.category == cat).mean() * 100
    r = (rest.category == cat).mean() * 100
    print(f'  {cat}: {t:.1f}% vs {r:.1f}% ({t-r:+.1f}pp)')
print(f'top payment methods (true): {dict(true_.payment_method.value_counts().head(3))}')
print(f'top shipping (true): {dict(true_.shipping_type.value_counts().head(3))}')
print(f'season mix (true): {dict(true_.season.value_counts())}')
print()

# --- discount exposure totals ---
disc_rev = df.loc[df.discount_used == 1, 'purchase_amount_usd'].sum()
print(f'=== discount exposure ===')
print(f'discounted transactions: {df.discount_used.sum()} ({df.discount_used.mean()*100:.0f}%), '
      f'discounted revenue ${disc_rev:,} ({disc_rev/TOTAL_REV*100:.1f}%)')
print(f'  of which subscriber (unidentifiable dependency): ${df.loc[df.subscribed==1, "purchase_amount_usd"].sum():,}')
print(f'  of which deal-responsive non-subscriber: ${df.loc[(df.discount_used==1)&(df.subscribed==0), "purchase_amount_usd"].sum():,}')
print(f'subscriber test cohort sizing: 1,053 subscribers; 10% holdout = {int(1053*0.10)} customers')

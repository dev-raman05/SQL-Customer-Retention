# Step 1 - Data cleaning. Decisions D1-D7 documented in ../cleaning-log.md
# Input:  data/Dataset.csv  (3,900 x 18, one row per customer, verified no duplicates)
# Output: data/clean_customers.csv (3,900 x 18: -1 dropped duplicate col, +1 missing flag,
#         +1 merged frequency; raw frequency label retained for traceability)

import pandas as pd

SRC = 'data/Dataset.csv'
OUT = 'data/clean_customers.csv'

df = pd.read_csv(SRC)
n_in = len(df)

# D2: Promo Code Used is a perfect duplicate of Discount Applied
# (crosstab verified: 2223 No/No, 1677 Yes/Yes, zero off-diagonal). Keep one.
assert (df['Discount Applied'] == df['Promo Code Used']).all(), 'D2 premise violated: columns differ'
df = df.drop(columns=['Promo Code Used'])

# D1: snake_case column names (SQL- and Power BI-friendly)
df = df.rename(columns={
    'Customer ID': 'customer_id', 'Age': 'age', 'Gender': 'gender',
    'Item Purchased': 'item_purchased', 'Category': 'category',
    'Purchase Amount (USD)': 'purchase_amount_usd', 'Location': 'state',
    'Size': 'size', 'Color': 'color', 'Season': 'season',
    'Review Rating': 'review_rating', 'Subscription Status': 'subscription_status',
    'Shipping Type': 'shipping_type', 'Discount Applied': 'discount_applied',
    'Previous Purchases': 'previous_purchases', 'Payment Method': 'payment_method',
    'Frequency of Purchases': 'frequency_raw',
})

# D3: merge synonym labels in purchase cadence (two synonym pairs exist in the raw data:
# Bi-Weekly/Fortnightly and Every 3 Months/Quarterly). Raw label kept in frequency_raw.
FREQ_MERGE = {
    'Weekly': 'Weekly', 'Bi-Weekly': 'Fortnightly', 'Fortnightly': 'Fortnightly',
    'Monthly': 'Monthly', 'Every 3 Months': 'Quarterly', 'Quarterly': 'Quarterly',
    'Annually': 'Annually',
}
df['purchase_frequency'] = df['frequency_raw'].map(FREQ_MERGE)
assert df['purchase_frequency'].notna().all(), 'D3: unmapped frequency label'

# D4: review_rating nulls (37) are kept as nulls + flagged. No imputation:
# missingness is structured (all 37 are discounted customers and all are male),
# so mean/median imputation would inject values into a non-random subgroup.
df['review_rating_missing'] = df['review_rating'].isna().astype(int)

# D7: Yes/No -> 1/0 for the two binary columns (analysis- and SQL-friendly)
df['subscribed'] = (df['subscription_status'] == 'Yes').astype(int)
df['discount_used'] = (df['discount_applied'] == 'Yes').astype(int)
df = df.drop(columns=['subscription_status', 'discount_applied'])

# D6: no row drops, ever (one row = one customer)
assert len(df) == n_in == 3900, 'row count changed'

df.to_csv(OUT, index=False)

# verification summary
print(f'rows in/out: {n_in}/{len(df)} | cols: {len(df.columns)}')
print('columns:', list(df.columns))
print('purchase_frequency:', dict(df.purchase_frequency.value_counts()))
print('rating nulls kept:', int(df.review_rating.isna().sum()),
      '| flag sum:', int(df.review_rating_missing.sum()))
print('subscribed:', int(df.subscribed.sum()), '| discount_used:', int(df.discount_used.sum()))

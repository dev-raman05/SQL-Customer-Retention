# Step 5a - Generate the PBIP semantic model (TMDL) for the founder dashboard.
# File formats verified against:
#   - usman-analyst/powerbi-mcp-northwindv2 (complete PBIP sample, fetched 2026-06-10)
#   - MS Learn projects-dataset docs via Context7 (definition.pbism versions, folder layout)
# Input:  data/customers_loyalty.csv (3,900 x 27)
# Output: dashboard/RetentionDashboard.SemanticModel/ (.platform, definition.pbism,
#         definition/{database,model,tables/customers}.tmdl)
# lineageTags are uuid5 of column names -> stable across reruns (clean git diffs).

import uuid
from pathlib import Path

import pandas as pd

CSV = Path('data/customers_loyalty.csv').resolve()
SM = Path('dashboard/RetentionDashboard.SemanticModel')
NS = uuid.UUID('5f0c7a51-9e1c-4b6e-9d3a-2f6f3a8c1d10')  # project namespace for uuid5

df = pd.read_csv(CSV)
assert len(df) == 3900 and len(df.columns) == 27, 'unexpected input shape'

INT_COLS = {c for c in df.columns if pd.api.types.is_integer_dtype(df[c])}
NUM_COLS = {c for c in df.columns if pd.api.types.is_float_dtype(df[c])}

def tag(name):
    return str(uuid.uuid5(NS, name))

# --- column blocks ---
col_blocks = []
for c in df.columns:
    if c in INT_COLS:
        dtype, extra = 'int64', '\t\tformatString: 0\n'
    elif c in NUM_COLS:
        dtype, extra = 'double', ''
    else:
        dtype, extra = 'string', ''
    summarize = 'sum' if c in INT_COLS | NUM_COLS else 'none'
    if c in {'customer_id', 'age'}:
        summarize = 'none'
    col_blocks.append(
        f'\tcolumn {c}\n'
        f'\t\tdataType: {dtype}\n'
        f'{extra}'
        f'\t\tlineageTag: {tag("col:" + c)}\n'
        f'\t\tsummarizeBy: {summarize}\n'
        f'\t\tsourceColumn: {c}\n\n'
        f'\t\tannotation SummarizationSetBy = Automatic\n'
    )

# --- measures (each answers one dashboard panel question) ---
MEASURES = [
    ('Total Customers', 'COUNTROWS(customers)', '#,0'),
    ('Total Revenue', 'SUM(customers[purchase_amount_usd])', '$#,0'),
    ('Avg Basket', 'AVERAGE(customers[purchase_amount_usd])', '$#,0.0'),
    ('Total LTV Proxy', 'SUM(customers[lifetime_value_proxy])', '$#,0'),
    ('Avg LTV Proxy', 'AVERAGE(customers[lifetime_value_proxy])', '$#,0'),
    ('Avg History Depth', 'AVERAGE(customers[previous_purchases])', '0.0'),
    # share measures: '+ 0' forces structural zeros to display as 0.0% instead of
    # BLANK (CALCULATE over an empty filter returns BLANK, which founders read as
    # missing data; e.g. deal-responsive share inside B-loyal segments is zero by
    # construction)
    ('Organic Share %',
     'DIVIDE(CALCULATE(COUNTROWS(customers), customers[promo_profile] = "organic") + 0, COUNTROWS(customers))',
     '0.0%'),
    ('Deal-Responsive Share %',
     'DIVIDE(CALCULATE(COUNTROWS(customers), customers[promo_profile] = "deal_responsive") + 0, COUNTROWS(customers))',
     '0.0%'),
    ('Deal-Responsive Revenue %',
     'DIVIDE(CALCULATE(SUM(customers[purchase_amount_usd]), customers[promo_profile] = "deal_responsive") + 0, SUM(customers[purchase_amount_usd]))',
     '0.0%'),
    ('True Loyal Share %',
     'DIVIDE(CALCULATE(COUNTROWS(customers), customers[loyalty_segment] = "true") + 0, COUNTROWS(customers))',
     '0.0%'),
]
measure_blocks = []
for name, dax, fmt in MEASURES:
    measure_blocks.append(
        f"\tmeasure '{name}' = {dax}\n"
        f'\t\tformatString: {fmt}\n'
        f'\t\tlineageTag: {tag("measure:" + name)}\n'
    )

# --- M partition: types per column ---
def m_type(c):
    if c in INT_COLS:
        return 'Int64.Type'
    if c in NUM_COLS:
        return 'type number'
    return 'type text'

type_list = ', '.join(f'{{"{c}", {m_type(c)}}}' for c in df.columns)
csv_path_m = str(CSV).replace('\\', '\\\\')
partition = (
    '\tpartition customers = m\n'
    '\t\tmode: import\n'
    '\t\tsource =\n'
    '\t\t\t\tlet\n'
    f'\t\t\t\t    Source = Csv.Document(File.Contents("{csv_path_m}"),'
    f'[Delimiter=",", Columns={len(df.columns)}, Encoding=65001, QuoteStyle=QuoteStyle.Csv]),\n'
    '\t\t\t\t    #"Promoted Headers" = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),\n'
    f'\t\t\t\t    #"Changed Type" = Table.TransformColumnTypes(#"Promoted Headers",{{{type_list}}})\n'
    '\t\t\t\tin\n'
    '\t\t\t\t    #"Changed Type"\n'
)

table_tmdl = (
    f'table customers\n\tlineageTag: {tag("table:customers")}\n\n'
    + '\n'.join(measure_blocks) + '\n'
    + '\n'.join(col_blocks) + '\n'
    + partition + '\n'
    + '\tannotation PBI_ResultType = Table\n'
)

model_tmdl = (
    'model Model\n'
    '\tculture: en-US\n'
    '\tdefaultPowerBIDataSourceVersion: powerBI_V3\n'
    '\tsourceQueryCulture: en-IN\n'
    '\tdataAccessOptions\n'
    '\t\tlegacyRedirects\n'
    '\t\treturnErrorValuesAsNull\n\n'
    'annotation __PBI_TimeIntelligenceEnabled = 0\n\n'
    'annotation PBI_QueryOrder = ["customers"]\n\n'
    'ref table customers\n'
)

platform = (
    '{\n'
    '  "$schema": "https://developer.microsoft.com/json-schemas/fabric/gitIntegration/platformProperties/2.0.0/schema.json",\n'
    '  "metadata": {\n'
    '    "type": "SemanticModel",\n'
    '    "displayName": "RetentionDashboard"\n'
    '  },\n'
    '  "config": {\n'
    '    "version": "2.0",\n'
    f'    "logicalId": "{tag("platform:semanticmodel")}"\n'
    '  }\n'
    '}\n'
)

(SM / 'definition' / 'tables').mkdir(parents=True, exist_ok=True)
(SM / '.platform').write_text(platform, encoding='utf-8')
(SM / 'definition.pbism').write_text('{\n  "version": "4.2",\n  "settings": {}\n}\n', encoding='utf-8')
(SM / 'definition' / 'database.tmdl').write_text('database\n\tcompatibilityLevel: 1600\n', encoding='utf-8')
(SM / 'definition' / 'model.tmdl').write_text(model_tmdl, encoding='utf-8')
(SM / 'definition' / 'tables' / 'customers.tmdl').write_text(table_tmdl, encoding='utf-8')

print(f'semantic model written to {SM}')
print(f'columns: {len(df.columns)} ({len(INT_COLS)} int, {len(NUM_COLS)} float, '
      f'{len(df.columns) - len(INT_COLS) - len(NUM_COLS)} text) | measures: {len(MEASURES)}')
print(f'CSV source path baked into M partition: {CSV}')

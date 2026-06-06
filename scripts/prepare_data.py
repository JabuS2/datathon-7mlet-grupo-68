import pandas as pd
import numpy as np
import os

# Create output directory if it doesn't exist
output_dir = "data/processed"
os.makedirs(output_dir, exist_ok=True)

# Load the training data
print("Loading training data...")
df = pd.read_csv("data/kaggle/train_ver2.csv")

print(f"Original dataset shape: {df.shape[0]} rows, {df.shape[1]} columns")
print(f"Original columns: {df.shape[1]}")

# Apply cleaning based on "When Less is More" Kaggle notebook
print("\nApplying data cleaning transformations...")

# 1. Remove rows where ind_empleado == 'S' (employees)
print("  - Removing employees (ind_empleado == 'S')...")
df = df[df['ind_empleado'] != 'S'].copy()

# 2. Keep only Spain residents (pais_residencia == 'ES')
print("  - Keeping only Spain residents (pais_residencia == 'ES')...")
df = df[df['pais_residencia'] == 'ES'].copy()

# 3. Fill missing ind_nuevo with 0
print("  - Filling missing ind_nuevo with 0...")
df['ind_nuevo'].fillna(0, inplace=True)

# 4. Fill missing indrel with 99
print("  - Filling missing indrel with 99...")
df['indrel'].fillna(99, inplace=True)

# 5. Drop tipodom (constant column)
print("  - Dropping tipodom column...")
df.drop('tipodom', axis=1, inplace=True)

# 6. Drop cod_prov (highly correlated with nomprov)
print("  - Dropping cod_prov column...")
df.drop('cod_prov', axis=1, inplace=True)

# 7. Fill missing ind_actividad_cliente with 0
print("  - Filling missing ind_actividad_cliente with 0...")
df['ind_actividad_cliente'].fillna(0, inplace=True)

# 8. Fill missing renta (income) with median per nomprov
print("  - Filling missing renta with median per nomprov...")
df['renta'] = df.groupby('nomprov')['renta'].transform(
    lambda x: x.fillna(x.median())
)

# 9. Fill missing segmento with most frequent value
print("  - Filling missing segmento with most frequent value...")
most_frequent_segmento = df['segmento'].mode()[0]
df['segmento'].fillna(most_frequent_segmento, inplace=True)

# 10. For the 24 product columns (ind_*_ult1), fill NaN with 0
print("  - Filling product columns (ind_*_ult1) with 0...")
product_cols = [col for col in df.columns if col.startswith('ind_') and col.endswith('_ult1')]
df[product_cols] = df[product_cols].fillna(0)

# 11. Convert fecha_dato to datetime
print("  - Converting fecha_dato to datetime...")
df['fecha_dato'] = pd.to_datetime(df['fecha_dato'], format='%Y-%m-%d')

# 12. Take 10% random sample (random_state=42)
print("  - Taking 10% random sample...")
df_sample = df.sample(frac=0.1, random_state=42)

# Save the sample
print(f"\nSample dataset shape: {df_sample.shape[0]} rows, {df_sample.shape[1]} columns")
print(f"Sample columns: {df_sample.shape[1]}")

output_path = os.path.join(output_dir, "train_sample_10pct.csv")
df_sample.to_csv(output_path, index=False)
print(f"\nSample saved to: {output_path}")

# Print summary
print("\n" + "="*60)
print("SUMMARY")
print("="*60)
print(f"Original dataset: {df.shape[0]} rows, {df.shape[1]} columns")
print(f"Sample dataset:   {df_sample.shape[0]} rows, {df_sample.shape[1]} columns")
print(f"Sample file: {output_path}")
print("="*60)

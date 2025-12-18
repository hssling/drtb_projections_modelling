import pandas as pd

# Test CSV reading
df = pd.read_csv('fresh_meta_extraction_clean_2025.csv')
print("Columns:", df.columns.tolist())
print("Shape:", df.shape)
print("\nFirst row:")
print(df.iloc[0])
print("\nIncluded column unique values:", df['included'].unique())
print("Country column unique values:", df['country'].unique())
print("n_total dtype:", df['n_total'].dtype)
print("n_resistant dtype:", df['n_resistant'].dtype)
print("Included column head:", df['included'].head())

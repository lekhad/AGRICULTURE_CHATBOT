import pandas as pd

# Load the KCC dataset with memory optimization
file_path = "kcc_dataset.csv"
df = pd.read_csv(file_path, low_memory=False)

# Ensure columns are stripped of spaces and normalized to lowercase
df.columns = df.columns.str.strip().str.lower()

# Rename columns to match expected lowercase format
column_mapping = {
    "statename": "statename",
    "districtname": "district",
    "season": "season",
    "sector": "sector",
    "crop": "crop",
    "querytext": "querytext",
    "kccans": "kccans"
}

# Filter and rename columns if they exist
available_columns = {col: column_mapping[col] for col in column_mapping if col in df.columns}
df = df.rename(columns=available_columns)

# Ensure only required columns are kept
required_columns = list(column_mapping.values())
df = df[required_columns]

# Handle missing values by filling with suitable placeholders
for col in df.columns:
    if df[col].dtype == 'object':  # For text columns
        df[col].fillna('unknown', inplace=True)
    else:  # For numeric columns
        df[col].fillna(-1, inplace=True)

# Remove rows where essential text columns contain only numeric data
def is_valid_text(value):
    return isinstance(value, str) and not value.isdigit()

text_columns = ['statename', 'district', 'season', 'sector', 'crop', 'querytext', 'kccans']
for col in text_columns:
    df = df[df[col].apply(is_valid_text)]

# Save the cleaned dataset
output_path = "cleaned_kcc_dataset.csv"
df.to_csv(output_path, index=False)
print(f"Cleaned dataset saved to {output_path}")

print("\nCleaned Dataset Info:\n")
df.info()
print("\nSample Cleaned Data:\n", df.head())

import pandas as pd

# Load dataset with appropriate encoding
df = pd.read_csv("KCC_AP_DATASET.csv", encoding="ISO-8859-1")

# Step 1: Replace numbers in "Crop" column with "Others"
df["Crop"] = df["Crop"].apply(lambda x: "Others" if any(char.isdigit() for char in str(x)) else x)

# Step 2: Replace numbers in "QueryType" column with "Agriculture"
df["QueryType"] = df["QueryType"].apply(lambda x: "Agriculture" if any(char.isdigit() for char in str(x)) else x)

# Step 3: Remove rows where "QueryText" or "KccAns" are empty
df = df.dropna(subset=["QueryText", "KccAns"])

# Save the cleaned dataset
df.to_csv("cleaned_AP_dataset.csv", index=False, encoding="utf-8")

print("Dataset cleaned successfully and saved as 'cleaned_dataset.csv'")

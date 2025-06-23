import pandas as pd
import re

# Load the dataset
df = pd.read_csv("cleaned_Final_AP_dataset.csv", encoding="ISO-8859-1", low_memory=False)


# Define function to clean 'QueryText' column
def clean_query_text(text):
    # Remove specific phrases without deleting the entire sentence
    text = re.sub(r'\bfarmer asked query on\b', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\bfarmer asked query about\b', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\bfarmer asked\b', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\basked about\b', '', text, flags=re.IGNORECASE)

    # Remove extra spaces caused by removal
    text = re.sub(r'\s+', ' ', text).strip()

    return text


# Apply function to 'QueryText' column
df["QueryText"] = df["QueryText"].astype(str).apply(clean_query_text)

# Save the cleaned dataset
df.to_csv("cleaned_AP_dataset.csv", index=False, encoding="ISO-8859-1")

print("Dataset cleaned and saved successfully!")

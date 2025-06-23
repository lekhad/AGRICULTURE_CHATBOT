import pandas as pd
import re

# Load the dataset
df = pd.read_csv("cleaned_AP_dataset.csv", encoding="ISO-8859-1")

# Step 1: Define a function to detect rows with excessive "?" characters
def contains_many_question_marks(text):
    if isinstance(text, str):
        return len(re.findall(r"\?", text)) > 5  # Adjust the threshold if needed
    return False

# Step 2: Filter out rows where "QueryText" contains excessive "?" characters
df = df[~df["KccAns"].apply(contains_many_question_marks)]

# Save the cleaned dataset
df.to_csv("cleaned_Final_AP_dataset.csv", index=False, encoding="utf-8")

print("Rows with excessive '?' characters have been removed. Cleaned dataset saved as 'final_filtered_dataset.csv'.")

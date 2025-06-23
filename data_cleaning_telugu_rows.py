import pandas as pd
import re

# Load the dataset with a safe encoding
df = pd.read_csv("KCC_AP.csv", encoding='ISO-8859-1', on_bad_lines='skip', low_memory=False)

# Function to check if a row contains Chinese characters
def contains_chinese(text):
    chinese_pattern = re.compile(r'[\u4E00-\u9FFF]')  # Unicode range for Chinese characters
    return bool(chinese_pattern.search(str(text)))

# Remove rows containing Chinese text
df = df[~df.apply(lambda row: any(contains_chinese(str(cell)) for cell in row), axis=1)]

# Drop empty rows
df = df.dropna(how='all')

# Save the cleaned dataset
df.to_csv("cleaned_dataset_no_chinese.csv", index=False, encoding='utf-8')

print("Dataset cleaned successfully and saved as 'cleaned_dataset_no_chinese.csv'.")

import pandas as pd

df = pd.read_csv("cleaned_data/Satellite.csv", dtype=str)

print("Blank dates:", df["LaunchedDate"].isna().sum())
print(df[df["LaunchedDate"].isna()][["SatelliteID", "LaunchedDate"]])
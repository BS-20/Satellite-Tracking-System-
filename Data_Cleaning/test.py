import pandas as pd

df = pd.read_csv("cleaned_data/TrackingSession.csv")

print("First Frequency value:", df["Frequency"].iloc[0])
print("Largest Frequency:", df["Frequency"].max())
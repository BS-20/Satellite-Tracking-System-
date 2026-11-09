import pandas as pd

df = pd.read_csv("cleaned_data/TrackingSession.csv")

df = df.drop(columns=["TrackingID"])

df.to_csv("cleaned_data/TrackingSession.csv", index=False)

print("TrackingID column removed successfully!")

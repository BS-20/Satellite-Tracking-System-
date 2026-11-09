import pandas as pd

file = "import_ready/TechnicalSubmission.csv"

df = pd.read_csv(file, dtype=str, keep_default_na=False)

id_columns = ["TAdminID", "SOperatorID", "GOperatorID"]

for col in id_columns:
    df[col] = df[col].apply(
        lambda x: str(int(float(x))) if x.strip() else ""
    )

df.to_csv(file, index=False)

print("TechnicalSubmission.csv IDs corrected!")
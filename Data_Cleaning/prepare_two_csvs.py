"""
Prepare TechnicalSubmission.csv and TrackingSession.csv for SQL Server import.

Removes only identity primary-key columns:
- TechnicalSubmission.SubmissionID
- TrackingSession.TrackingID

Do NOT remove SubmissionID from Satellite.csv or GroundStation.csv. Those are
foreign keys that link each record to its TechnicalSubmission.

Expected input files: cleaned_data/TechnicalSubmission.csv and
cleaned_data/TrackingSession.csv
Output files: import_ready/TechnicalSubmission.csv and
import_ready/TrackingSession.csv

Run: py -m pip install pandas
     py prepare_two_csvs.py
"""
from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
INPUT_DIR = BASE_DIR / "cleaned_data"
OUTPUT_DIR = BASE_DIR / "import_ready"
OUTPUT_DIR.mkdir(exist_ok=True)

FILES_AND_ID_COLUMNS = {
    "TechnicalSubmission.csv": "SubmissionID",
    "TrackingSession.csv": "TrackingID",
}

def main():
    for filename, identity_column in FILES_AND_ID_COLUMNS.items():
        source = INPUT_DIR / filename
        if not source.exists():
            raise FileNotFoundError(f"Could not find {source}")

        df = pd.read_csv(source, dtype=str, keep_default_na=False)
        if identity_column in df.columns:
            df = df.drop(columns=[identity_column])
            print(f"Removed {identity_column} from {filename}")
        else:
            print(f"{identity_column} is already absent from {filename}")

        destination = OUTPUT_DIR / filename
        df.to_csv(destination, index=False, encoding="utf-8-sig")
        print(f"Created {destination}")

    print("\nDone. Import these two files from the import_ready folder.")
    print("Import TechnicalSubmission before Satellite and GroundStation.")

if __name__ == "__main__":
    main()

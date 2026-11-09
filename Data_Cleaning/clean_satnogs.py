"""
SatNOGS CSV cleaner + seed-data generator for the Satellite Tracking System.

Expected folder layout:
Satellite-Tracking-System/
    clean_satnogs.py
    Data/
        satnogs_db_satellites.csv
        satnogs_db_transmitters.csv
        satnogs_network_stations.csv
        satnogs_network_jobs.csv
        satnogs_network_observations.csv

Run:
    py -m pip install pandas
    py clean_satnogs.py

Outputs:
    cleaned_data/*.csv
    cleaned_data/seed_database.sql
"""

from pathlib import Path
import ast
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "Data"
OUT_DIR = BASE_DIR / "cleaned_data"
OUT_DIR.mkdir(exist_ok=True)

IMPORT_DATE = pd.Timestamp.now(tz="UTC").date().isoformat()

REQUIRED_FILES = {
    "satellites": "satnogs_db_satellites.csv",
    "transmitters": "satnogs_db_transmitters.csv",
    "stations": "satnogs_network_stations.csv",
    "jobs": "satnogs_network_jobs.csv",
    "observations": "satnogs_network_observations.csv",
}


def read_source(key):
    path = DATA_DIR / REQUIRED_FILES[key]
    if not path.exists():
        raise FileNotFoundError(
            f"Missing {path}. Put the original SatNOGS CSV files inside the Data folder."
        )
    return pd.read_csv(path, low_memory=False)


def text_value(value):
    """Return cleaned text or None for pandas NaN/blank values."""
    if pd.isna(value):
        return None
    value = str(value).strip()
    if value.lower() in {"", "none", "nan", "null"}:
        return None
    return value


def numeric_series(series):
    return pd.to_numeric(series, errors="coerce")


def nullable_int(series):
    return numeric_series(series).round().astype("Int64")


def utc_parts(series):
    """Convert ISO timestamps to SQL Server UTC date and time strings."""
    dt = pd.to_datetime(series, errors="coerce", utc=True)
    dates = dt.dt.strftime("%Y-%m-%d")
    times = dt.dt.strftime("%H:%M:%S")
    return dates, times


def parse_antenna_list(value):
    if pd.isna(value):
        return []
    try:
        parsed = ast.literal_eval(str(value))
        return parsed if isinstance(parsed, list) else []
    except (ValueError, SyntaxError, TypeError):
        return []


def mhz_string(hz):
    if pd.isna(hz):
        return None
    return f"{float(hz) / 1_000_000:g}"


def clean_satellites(raw):
    df = raw.copy()
    df["SatelliteID"] = df["sat_id"].map(text_value)
    df["SatelliteName"] = df["name"].map(text_value)
    df["NORAD"] = nullable_int(df["norad_cat_id"])
    df["SatelliteStatus"] = df["status"].map(text_value)
    df["AltName"] = df["names"].map(text_value)
    df["CountryofOrigin"] = df["countries"].map(text_value)
    df["LaunchedDate"] = pd.to_datetime(
        df["launched"], errors="coerce", utc=True
    ).dt.strftime("%Y-%m-%d")
    df["SDescription"] = None  # SatNOGS satellite CSV has no general description field.
    df["ExternalOperator"] = df["operator"].map(text_value)
    df["Website"] = df["website"].map(text_value)

    df = df[df["SatelliteID"].notna() & df["SatelliteName"].notna()].copy()
    df = df.drop_duplicates(subset=["SatelliteID"], keep="first").reset_index(drop=True)

    # TechnicalSubmission IDs are assigned deterministically: satellite rows first.
    df["SubmissionID"] = range(1, len(df) + 1)

    cols = [
        "SatelliteID", "SatelliteName", "NORAD", "SatelliteStatus", "AltName",
        "CountryofOrigin", "LaunchedDate", "SDescription", "ExternalOperator",
        "Website",  "SubmissionID"
    ]
    return df[cols]


def clean_transmitters(raw, satellite_ids):
    df = raw.copy()
    df["TransmitterID"] = df["uuid"].map(text_value)
    df["SatelliteID"] = df["sat_id"].map(text_value)

    numeric_fields = [
        "uplink_low", "uplink_high", "uplink_drift", "uplink_drifted",
        "downlink_low", "downlink_high", "downlink_drift", "downlink_drifted",
    ]
    for col in numeric_fields:
        df[col] = numeric_series(df[col])

    # SatNOGS displays Center Frequency as the midpoint of the nominal
    # downlink range. If no downlink is supplied, fall back to the uplink range.
    down_mid = df[["downlink_low", "downlink_high"]].mean(axis=1, skipna=True)
    up_mid = df[["uplink_low", "uplink_high"]].mean(axis=1, skipna=True)
    df["CenterFrequency"] = down_mid.fillna(up_mid)

    df["Mode"] = df["mode"].map(text_value)
    df["UplinkMode"] = df["uplink_mode"].map(text_value)
    df["TService"] = df["service"].map(text_value)
    df["TStatus"] = df["status"].map(text_value)
    df["TDescription"] = df["description"].map(text_value)

    df = df[
        df["TransmitterID"].notna()
        & df["SatelliteID"].isin(satellite_ids)
    ].copy()
    df = df.drop_duplicates(subset=["TransmitterID"], keep="first")

    cols = [
        "TransmitterID", "SatelliteID", "CenterFrequency",
        "DownlinkLow", "DownlinkHigh", "DownlinkDrift", "DownlinkDrifted",
        "UplinkLow", "UplinkHigh", "UplinkDrift", "UplinkDrifted",
        "Mode", "TService", "TStatus", "TDescription"
    ]
    rename = {
        "downlink_low": "DownlinkLow",
        "downlink_high": "DownlinkHigh",
        "downlink_drift": "DownlinkDrift",
        "downlink_drifted": "DownlinkDrifted",
        "uplink_low": "UplinkLow",
        "uplink_high": "UplinkHigh",
        "uplink_drift": "UplinkDrift",
        "uplink_drifted": "UplinkDrifted",
    }
    df = df.rename(columns=rename)
    return df[cols].reset_index(drop=True)


def clean_stations(raw, satellite_count):
    df = raw.copy()
    df["GStationID"] = df["id"].map(text_value)
    df["GStationName"] = df["name"].map(text_value)
    df["Latitude"] = numeric_series(df["lat"])
    df["Longitude"] = numeric_series(df["lng"])
    df["Altitude"] = numeric_series(df["altitude"])
    df["QTHLocator"] = df["qthlocator"].map(text_value)
    df["TotalObservations"] = nullable_int(df["observations"]).fillna(0)
    df["FutureObservations"] = nullable_int(df["future_observations"]).fillna(0)
    df["ExternalOwner"] = df["owner"].map(text_value)
    df["GStatus"] = df["status"].map(text_value)

    def make_location(row):
        bits = []
        if row["QTHLocator"]:
            bits.append(row["QTHLocator"])
        if pd.notna(row["Latitude"]) and pd.notna(row["Longitude"]):
            bits.append(f'{row["Latitude"]:.6f}, {row["Longitude"]:.6f}')
        if pd.notna(row["Altitude"]):
            bits.append(f'{row["Altitude"]:g} m')
        return " | ".join(bits) if bits else None

    df["GLocation"] = df.apply(make_location, axis=1)
    df = df[df["GStationID"].notna() & df["GStationName"].notna()].copy()
    df = df.drop_duplicates(subset=["GStationID"], keep="first").reset_index(drop=True)

    # Satellite submissions occupy IDs 1..N; station submissions follow them.
    df["SubmissionID"] = range(satellite_count + 1, satellite_count + len(df) + 1)

    cols = [
        "GStationID", "GStationName", "GLocation", "Latitude", "Longitude",
        "Altitude", "QTHLocator", "TotalObservations", "FutureObservations",
        "ExternalOwner", "GStatus", "SubmissionID"
    ]
    return df[cols], df


def clean_antennas(stations_raw, valid_station_ids):
    rows = []
    for _, station in stations_raw.iterrows():
        station_id = text_value(station.get("id"))
        if station_id not in valid_station_ids:
            continue

        for antenna in parse_antenna_list(station.get("antenna")):
            if not isinstance(antenna, dict):
                continue

            name = text_value(
                antenna.get("antenna_type_name") or antenna.get("antenna_type")
            )
            band = text_value(antenna.get("band"))
            low = pd.to_numeric(antenna.get("frequency"), errors="coerce")
            high = pd.to_numeric(antenna.get("frequency_max"), errors="coerce")

            if name is None:
                continue

            low_mhz = mhz_string(low)
            high_mhz = mhz_string(high)
            if low_mhz and high_mhz:
                freq_range = f"{low_mhz}-{high_mhz} MHz"
            elif low_mhz:
                freq_range = f"{low_mhz} MHz"
            else:
                freq_range = "Not specified"

            if band:
                freq_range += f" ({band})"

            rows.append({
                "GStationID": station_id,
                "AntennaName": name,
                "FrequencyRange": freq_range
            })

    result = pd.DataFrame(rows, columns=[
        "GStationID", "AntennaName", "FrequencyRange"
    ])
    return result.drop_duplicates().reset_index(drop=True)

def clean_observation_requests(raw, satellite_df, station_df, transmitters_df):
    df = raw.copy()

    df["SourceJobID"] = nullable_int(df["id"])
    df["SatelliteNORAD"] = nullable_int(df["norad_cat_id"])

    norad_mapping = (
        satellite_df.dropna(subset=["NORAD"])
        .set_index("NORAD")["SatelliteID"]
    )

    df["SatelliteID"] = df["SatelliteNORAD"].map(norad_mapping)
    df["GStationID"] = df["ground_station"].map(text_value)

    df["RequestDate"], df["RequestStartTime"] = utc_parts(df["start"])
    _, df["RequestEndTime"] = utc_parts(df["end"])

    # Match a job to a transmitter belonging to its satellite.
    tx_groups = {
        sid: group
        for sid, group in transmitters_df.groupby("SatelliteID")
    }

    def find_transmitter(row):
        candidates = tx_groups.get(row["SatelliteID"])

        if candidates is None or candidates.empty:
            return None

        frequency = pd.to_numeric(row.get("frequency"), errors="coerce")

        # SatNOGS job frequencies may be represented in MHz.
        if pd.notna(frequency) and abs(frequency) < 1_000_000:
            frequency *= 1_000_000

        if pd.notna(frequency):
            low = pd.to_numeric(candidates["DownlinkLow"], errors="coerce")
            high = pd.to_numeric(candidates["DownlinkHigh"], errors="coerce")

            matches = candidates[
                (low <= frequency) & (high >= frequency)
            ]

            if len(matches) == 1:
                return matches.iloc[0]["TransmitterID"]

        # If there is only one transmitter, the association is unambiguous.
        if len(candidates) == 1:
            return candidates.iloc[0]["TransmitterID"]

        return None

    df["TransmitterID"] = df.apply(find_transmitter, axis=1)

    valid_stations = set(station_df["GStationID"])

    df = df[
        df["SourceJobID"].notna()
        & df["SatelliteID"].notna()
        & df["GStationID"].isin(valid_stations)
        & df["TransmitterID"].notna()
    ].copy()

    df = df.drop_duplicates(
        subset=["SourceJobID"], keep="first"
    ).reset_index(drop=True)

    # Synthetic import-service operators, not claimed real operators.
    df["SOperatorID"] = 1
    df["GOperatorID"] = 1
    df["RequestStatus"] = "Imported"

    cols = [
        "RequestStartTime",
        "RequestEndTime",
        "RequestDate",
        "SOperatorID",
        "GOperatorID",
        "RequestStatus",
        "SatelliteID",
        "GStationID",
        "TransmitterID"
    ]

    return df[cols]

def clean_tracking_sessions(raw, satellite_df, station_df):
    df = raw.copy()

    df["SourceObservationID"] = nullable_int(df["id"])
    df["SatelliteID"] = df["sat_id"].map(text_value)
    df["GStationID"] = df["ground_station"].map(text_value)

    df["TSDate"], df["StartTime"] = utc_parts(df["start"])
    _, df["EndTime"] = utc_parts(df["end"])

    observed_frequency = numeric_series(df["observation_frequency"])
    center_frequency = numeric_series(df["center_frequency"])
    df["Frequency"] = observed_frequency.fillna(center_frequency)

    df["Mode"] = df["transmitter_mode"].map(text_value)
    df["Observer"] = df["observer"].map(text_value)

    valid_satellites = set(satellite_df["SatelliteID"])
    valid_stations = set(station_df["GStationID"])

    df = df[
        df["SourceObservationID"].notna()
        & df["SatelliteID"].isin(valid_satellites)
        & df["GStationID"].isin(valid_stations)
    ].copy()

    df = df.drop_duplicates(
        subset=["SourceObservationID"], keep="first"
    ).reset_index(drop=True)

    cols = [
        "Frequency", "Mode", "StartTime", "EndTime", "TSDate",
        "SatelliteID", "GStationID", "Observer"
    ]

    return df[cols]


def build_application_seed(satellite_count, station_count):
    # One clearly labelled import-service account is used only to satisfy the
    # application's mandatory FK relationships for imported legacy records.
    # It is not a real person or a real SatNOGS operator.
    admins = pd.DataFrame([{
        "AdminName": "System Seed Administrator",
        "CNICNumber": None,
        "EmailAddress": "system-admin@example.invalid",
    }])

    users = pd.DataFrame([{
        "UserName": "SatNOGS Dataset Import Service",
        "CNICNumber": None,
        "EmailAddress": "satnogs-import@example.invalid",
    }])

    technical_admins = pd.DataFrame([{
        "TAdminName": "System Import Administrator",
        "CNICNumber": None,
        "EmailAddress": "technical-admin@example.invalid",
        "PhoneNumber": None,
    }])

    affiliation_requests = pd.DataFrame([
        {
            "RequestID": 1, "UserID": 1, "AdminID": 1,
            "RequestedRole": "SatelliteOperator",
            "Organization": "SatNOGS Public Dataset Import",
            "ProofDocuments": "Synthetic seed record for imported public data; not a real user request.",
            "RequestStatus": "Approved",
        },
        {
            "RequestID": 2, "UserID": 1, "AdminID": 1,
            "RequestedRole": "GroundStationOperator",
            "Organization": "SatNOGS Public Dataset Import",
            "ProofDocuments": "Synthetic seed record for imported public data; not a real user request.",
            "RequestStatus": "Approved",
        },
    ])

    satellite_operators = pd.DataFrame([{
        "SOperatorName": "SatNOGS Import Service",
        "RequestID": 1,
    }])

    ground_station_operators = pd.DataFrame([{
        "GOperatorName": "SatNOGS Import Service",
        "RequestID": 2,
    }])

    submissions = []

    for sid in range(1, satellite_count + 1):
        submissions.append({
            "SubmissionType": "SatelliteImport",
            "SubmissionDate": IMPORT_DATE,
            "SStatus": "Imported",
            "TAdminID": 1,
            "SOperatorID": 1,
            "GOperatorID": None,
        })

    for sid in range(satellite_count + 1, satellite_count + station_count + 1):
        submissions.append({
            "SubmissionType": "GroundStationImport",
            "SubmissionDate": IMPORT_DATE,
            "SStatus": "Imported",
            "TAdminID": 1,
            "SOperatorID": None,
            "GOperatorID": 1,
        })

    technical_submissions = pd.DataFrame(submissions)

    return {
        "Admins": admins,
        "Users": users,
        "TechnicalAdmin": technical_admins,
        "AffiliationRequest": affiliation_requests,
        "SatelliteOperator": satellite_operators,
        "GroundStationOperator": ground_station_operators,
        "TechnicalSubmission": technical_submissions,
    }


def save_frame(name, frame):
    path = OUT_DIR / f"{name}.csv"
    frame.to_csv(path, index=False, encoding="utf-8-sig")
    print(f"Created {path.name}: {len(frame):,} rows")


def main():
    print("Reading SatNOGS source CSV files...")
    raw_sat = read_source("satellites")
    raw_tx = read_source("transmitters")
    raw_stations = read_source("stations")
    raw_jobs = read_source("jobs")
    raw_obs = read_source("observations")

    print("Cleaning satellites...")
    satellites = clean_satellites(raw_sat)

    print("Cleaning transmitters...")
    transmitters = clean_transmitters(
        raw_tx, set(satellites["SatelliteID"])
    )

    print("Cleaning ground stations and antennas...")
    ground_stations, stations_with_raw_antenna = clean_stations(
        raw_stations, len(satellites)
    )
    antennas = clean_antennas(
        stations_with_raw_antenna,
        set(ground_stations["GStationID"])
    )

    print("Creating imported observation requests from SatNOGS network jobs...")
    observation_requests = clean_observation_requests(
    raw_jobs, satellites, ground_stations, transmitters
    )
    print("Creating tracking sessions from actual SatNOGS observations...")
    tracking_sessions = clean_tracking_sessions(
        raw_obs, satellites, ground_stations
    )

    print("Generating clearly labelled synthetic application seed records...")
    seed = build_application_seed(
        len(satellites), len(ground_stations)
    )

    # Order matters for the generated SQL script: parent tables before children.
    all_tables = {
        "Admins": seed["Admins"],
        "Users": seed["Users"],
        "TechnicalAdmin": seed["TechnicalAdmin"],
        "AffiliationRequest": seed["AffiliationRequest"],
        "SatelliteOperator": seed["SatelliteOperator"],
        "GroundStationOperator": seed["GroundStationOperator"],
        "TechnicalSubmission": seed["TechnicalSubmission"],
        "Satellite": satellites,
        "SatelliteTransmitter": transmitters,
        "GroundStation": ground_stations,
        "Antennas": antennas,
        "ObservationRequests": observation_requests,
        "TrackingSession": tracking_sessions,
    }

    for name, frame in all_tables.items():
        save_frame(name, frame)

    print("\nFinished.")
    print(f"Satellites: {len(satellites):,}")
    print(f"Transmitters: {len(transmitters):,}")
    print(f"Ground stations: {len(ground_stations):,}")
    print(f"Antennas: {len(antennas):,}")
    print(f"Imported observation requests (network jobs): {len(observation_requests):,}")
    print(f"Tracking sessions (actual observations): {len(tracking_sessions):,}")
    print(f"Output folder: {OUT_DIR}")
    print("Run cleaned_data/seed_database.sql in SSMS after creating empty tables.")


if __name__ == "__main__":
    main()

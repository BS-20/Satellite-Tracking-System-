select * FROM Admins

select * FROM Users

select * from TechnicalAdmin

select * from AffiliationRequest

-- Some cells in TechnicalSubmission.csv has empty strings, which were not being converted into integers directly, so solve this conflict 
-- I first imported data (in string data type) into TechnicalSubmission_Temp
CREATE TABLE TechnicalSubmission_Temp (
    SubmissionType NVARCHAR(50),
    SubmissionDate NVARCHAR(50),
    SStatus NVARCHAR(50),
    TAdminID INT,
    SOperatorID NVARCHAR(50) NULL,
    GOperatorID NVARCHAR(50) NULL
);

select * from TechnicalSubmission_Temp

UPDATE TechnicalSubmission_Temp
SET
    SOperatorID = NULLIF(TRIM(SOperatorID), ''),
    GOperatorID = NULLIF(TRIM(GOperatorID), '');

select * from TechnicalSubmission_Temp

-- Inserting data into Original table; TechnicalSubmission
INSERT INTO TechnicalSubmission (
    SubmissionType, SubmissionDate, SStatus,
    TAdminID, SOperatorID, GOperatorID
)
SELECT
    SubmissionType, SubmissionDate, SStatus,
    TAdminID,
    TRY_CONVERT(INT, SOperatorID),
    TRY_CONVERT(INT, GOperatorID)
FROM TechnicalSubmission_Temp;
select * from TechnicalSubmission_Temp

select * from Satellite

select * from GroundStation

-- Some cells in Satellite.csv has empty strings, which were not being converted into integers directly, so solve this conflict 
-- I first imported data (in string data type) into Satellite_Temp
CREATE TABLE Satellite_Temp (
	SatelliteID NVarchar(24) Primary key,
	SatelliteName NVarchar(40),
	NORAD Integer Unique,
	SatelliteStatus NVarchar(20),
	AltName NVarchar(1000),
	CountryofOrigin NVarchar(100),
	LaunchedDate NVARCHAR(50) NULL,
	SDescription NVARCHAR(MAX),
	ExternalOperator NVarchar(100),
	Website NVarchar(1000),
	SubmissionID Integer NOT NULL UNIQUE,
	
	FOREIGN KEY (SubmissionID) References TechnicalSubmission(SubmissionID)
);

UPDATE Satellite_Temp
SET
    SatelliteName = NULLIF(TRIM(SatelliteName), ''),
    SatelliteStatus = NULLIF(TRIM(SatelliteStatus), ''),
    AltName = NULLIF(TRIM(AltName), ''),
    CountryofOrigin = NULLIF(TRIM(CountryofOrigin), ''),
    LaunchedDate = NULLIF(TRIM(LaunchedDate), ''),
    SDescription = NULLIF(TRIM(SDescription), ''),
    ExternalOperator = NULLIF(TRIM(ExternalOperator), ''),
    Website = NULLIF(TRIM(Website), '');
select * from Satellite_Temp

INSERT INTO Satellite (
    SatelliteID, SatelliteName, NORAD, SatelliteStatus,
    AltName, CountryofOrigin, LaunchedDate, SDescription,
    ExternalOperator, Website, SubmissionID
)
SELECT
    SatelliteID, SatelliteName, NORAD, SatelliteStatus,
    AltName, CountryofOrigin,
    TRY_CONVERT(DATE, NULLIF(LaunchedDate, '')),
    SDescription, ExternalOperator, Website, SubmissionID
FROM Satellite_Temp;

select * from Satellite

select * from SatelliteTransmitter

select * from Antennas

select * from TrackingSession

select * from ObservationRequests



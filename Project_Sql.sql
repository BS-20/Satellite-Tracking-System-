create Table Admins(
	AdminID Integer IDENTITY(1, 1) Primary Key,
	AdminName Varchar(100),
	CNICNumber Varchar(15) UNIQUE,
	EmailAddress Varchar(254) UNIQUE,
);

create Table Users(
	UserID Integer IDENTITY(1, 1) Primary Key,
	UserName Varchar(100),
	CNICNumber Varchar(15) UNIQUE,
	EmailAddress Varchar(254) UNIQUE,
);

create Table AffiliationRequest (
	RequestID Integer IDENTITY(1, 1) Primary Key,
	UserID Integer NOT NULL,
	AdminID Integer,
	RequestedRole Varchar(22),
	Organizarion Varchar(150),
	ProofDocuments text,
	RequestStatus Varchar(9),

	FOREIGN KEY (UserID) References Users(UserID),
	FOREIGN KEY (AdminID) References Admins(AdminID)
);

create Table SatelliteOperator (
	SOperatorID Integer IDENTITY(1, 1) Primary Key,
	SOperatorName Varchar(100),
	RequestID Integer Not NULL UNIQUE,
	
	FOREIGN KEY (RequestID) References AffiliationRequest(RequestID) 
);

create Table GroundStationOperator (
	GOperatorID Integer IDENTITY(1, 1) Primary Key, 
	GOperatorName Varchar(100),
	RequestID Integer Not NULL UNIQUE,
	
	FOREIGN KEY (RequestID) References AffiliationRequest(RequestID) 
);

create Table TechnicalAdmin (
	TAdminID Integer IDENTITY(1, 1) Primary Key,
	TAdminName Varchar(30),
	CNICNumber Varchar(15) UNIQUE,
	EmailAddress Varchar(254) UNIQUE,
	PhoneNumber Varchar(20) UNIQUE
);

create Table TechnicalSubmission (
	SubmissionID Integer IDENTITY(1, 1) Primary Key,
	SubmissionType Varchar(30),
	SubmissionDate Date,
	SStatus Varchar(9),
	TAdminID Integer Unique,
	SOperatorID Integer Unique,
	GOperatorID Integer Unique,

	FOREIGN KEY (TAdminID) References TechnicalAdmin(TAdminID),
	FOREIGN KEY (SOperatorID) References SatelliteOperator(SOperatorID),
	FOREIGN KEY (GOperatorID) References GroundStationOperator(GOperatorID),

	CHECK (
		(SOperatorID IS NULL AND GOperatorID IS NOT NULL)
		OR
		(SOperatorID IS NOT NULL AND GOperatorID IS NULL)
	)
);

create Table Satellite (
	SatelliteID Varchar(24) Primary key,
	SatelliteName Varchar(40) Unique,
	NORAD Integer Unique,
	SatelliteStatus Varchar(20),
	AltName Varchar(40),
	CountryofOrigin Varchar(100),
	LaunchedDate date, 
	SDescription text,
	SubmissionID Integer NOT NULL UNIQUE,
	
	FOREIGN KEY (SubmissionID) References TechnicalSubmission(SubmissionID)
);

create Table SatelliteTransmitter(
	TransmitterID Varchar(30) Primary Key,
	CenterFrequency DECIMAL(12,4),
	Mode Varchar(30),
	TService  Varchar(100),
	TStatus Varchar(10),
	TDescription text,
	SatelliteID Varchar(20) NOT NULL,
	
	FOREIGN KEY (SatelliteID) References Satellite(SatelliteID),
);

create Table GroundStation (
	GStationID Varchar(20) Primary key,
	GStationName Varchar(40) Unique,
	GLocation Varchar(70),
	TotalObservations Integer DEFAULT 0,
	FutureObservations Integer DEFAULT 0,
	SubmissionID Integer NOT NULL UNIQUE,
	
	FOREIGN KEY (SubmissionID) References TechnicalSubmission(SubmissionID)
);

create Table Antennas(
	AntennaName VarChar(50) NOT NULL,
	FrequencyRange Varchar(50),
	GStationID Varchar(20) NOT NULL,
	
	FOREIGN KEY (GStationID) References GroundStation(GStationID),

	Primary Key (AntennaName, GStationID, FrequencyRange)
);

create Table TrackingSession (
	TrackingID Integer IDENTITY(1, 1) Primary Key,
	Frequency DECIMAL(12,4),
	Mode VarChar(4),
	StartTime Time,
	EndTime Time,
	TSDate Date,
	SatelliteID Varchar(20) NOT NULL,
	GStationID Varchar(20) NOT NULL,
	Observer VARCHAR(100)

	FOREIGN KEY (SatelliteID) References Satellite(SatelliteID),
	FOREIGN KEY (GStationID) References GroundStation(GStationID)
);

create Table ObservationRequests (
	ORequestID Integer IDENTITY(1,1) Primary Key,
	RequestStartTime Time,
	RequestEndTime Time,
	RequestDate Date,
	SOperatorID Integer NOT NULL,
	GOperatorID Integer NOT NULL,
	RequestStatus Varchar(9),
	
	FOREIGN KEY (SOperatorID) References SatelliteOperator(SOperatorID),
	FOREIGN KEY (GOperatorID) References GroundStationOperator(GOperatorID),	
);





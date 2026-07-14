-- Trigger Tracker - SQL Server schema
-- Run this once against your database (Windows Authentication or SQL login, both work)

IF NOT EXISTS (SELECT * FROM sys.databases WHERE name = 'TriggerTracker')
BEGIN
    CREATE DATABASE TriggerTracker;
END
GO

USE TriggerTracker;
GO

IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'events')
BEGIN
    CREATE TABLE dbo.events (
        event_id            INT IDENTITY(1,1) PRIMARY KEY,
        created_at          DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
        language            NVARCHAR(5)   NOT NULL DEFAULT 'en',  -- 'en' or 'tr'

        -- Source stage
        source_label        NVARCHAR(200) NOT NULL DEFAULT 'Unreasonable situation',
        raw_description     NVARCHAR(MAX) NULL,

        -- Extract stage: turning the event into fact
        extract_fact                NVARCHAR(MAX) NULL,  -- what happened, observable only
        extract_third_party_version NVARCHAR(MAX) NULL,  -- how would you tell a court/third party
        extract_is_evidence_based   BIT NULL,             -- fact vs. interpretation
        extract_is_recurring_pattern BIT NULL,             -- happened before vs. one-off

        -- Transform stage: separating emotional load
        transform_intensity_score   TINYINT NULL,   -- 1-10
        transform_is_proportional   BIT NULL,       -- intensity matches fact size?
        transform_signal_type       NVARCHAR(20) NULL, -- 'action_needed' or 'needs_processing'
        transform_serves_purpose    BIT NULL,       -- would expressing it now help resolve, or just relieve?

        -- Filter stage: separating from old emotion
        filter_feels_familiar        BIT NULL,   -- recognize this feeling from before?
        filter_reaction_vs_event_size NVARCHAR(20) NULL, -- 'equal' or 'bigger'
        filter_would_react_same_stranger BIT NULL, -- would you react the same to a stranger?
        filter_echoes_childhood      BIT NULL,

        -- Load stage: final destination
        destination_tag      NVARCHAR(20) NOT NULL DEFAULT 'archive', -- 'system' or 'archive'
        destination_note     NVARCHAR(MAX) NULL  -- e.g. "sent to lawyer", "logged for court"
    );
END
GO

IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'destination_tags')
BEGIN
    CREATE TABLE dbo.destination_tags (
        tag_id      NVARCHAR(20) PRIMARY KEY,
        label_en    NVARCHAR(100) NOT NULL,
        label_tr    NVARCHAR(100) NOT NULL
    );
    INSERT INTO dbo.destination_tags (tag_id, label_en, label_tr) VALUES
        ('system',  'System (lawyer, court, record)', 'Sistem (avukat, mahkeme, kayıt)'),
        ('archive', 'Archive (old emotion, quarantined)', 'Arşiv (eski duygu, karantina)');
END
GO

-- How many times triggered, grouped by destination, per week
CREATE OR ALTER VIEW dbo.v_trigger_counts_weekly AS
SELECT
    DATEPART(YEAR, created_at)  AS year,
    DATEPART(WEEK, created_at)  AS week,
    destination_tag,
    COUNT(*) AS trigger_count
FROM dbo.events
GROUP BY DATEPART(YEAR, created_at), DATEPART(WEEK, created_at), destination_tag;
GO

-- Overall totals per destination
CREATE OR ALTER VIEW dbo.v_trigger_counts_total AS
SELECT
    destination_tag,
    COUNT(*) AS trigger_count,
    MIN(created_at) AS first_event,
    MAX(created_at) AS last_event
FROM dbo.events
GROUP BY destination_tag;
GO

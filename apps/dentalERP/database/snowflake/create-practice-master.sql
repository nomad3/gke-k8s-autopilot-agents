-- Practice Master Mapping Table
-- Single source of truth for practice identifiers across all systems

USE DATABASE DENTAL_ERP_DW;
USE SCHEMA GOLD;
USE ROLE ACCOUNTADMIN;

CREATE TABLE IF NOT EXISTS gold.practice_master (
    practice_id VARCHAR(50) PRIMARY KEY,
    practice_display_name VARCHAR(100) NOT NULL,

    -- System-specific identifiers
    operations_code VARCHAR(20),           -- LHD, EFD I, ADS (from Ops Report)
    netsuite_subsidiary_id VARCHAR(50),
    netsuite_subsidiary_name VARCHAR(100), -- SCDP Eastlake, etc.
    pms_location_code VARCHAR(50),         -- eastlake, torrey_pines (from day sheets)
    adp_location_code VARCHAR(50),         -- For future ADP integration
    eaglesoft_practice_id VARCHAR(50),     -- For future Eaglesoft API

    -- Metadata
    is_active BOOLEAN DEFAULT TRUE,
    tenant_id VARCHAR(50) DEFAULT 'silvercreek',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
COMMENT = 'Master practice mapping across all integrated systems (Operations, NetSuite, PMS, ADP)';

-- Insert all 14 practice mappings
INSERT INTO gold.practice_master
(practice_id, practice_display_name, operations_code, netsuite_subsidiary_name, pms_location_code, tenant_id)
VALUES
('lhd', 'Laguna Hills Dental', 'LHD', 'SCDP Laguna Hills', 'laguna_hills', 'silvercreek'),
('efd_i', 'Encinitas Family Dental I', 'EFD I', 'SCDP Encinitas I', 'encinitas_1', 'silvercreek'),
('cvfd', 'Carmel Valley Family Dental', 'CVFD', 'SCDP Carmel Valley', 'carmel_valley', 'silvercreek'),
('dsr', 'Del Sur Dental', 'DSR', 'SCDP Del Sur', 'del_sur', 'silvercreek'),
('ads', 'Advanced Dental Solutions', 'ADS', 'SCDP San Marcos', 'ads', 'silvercreek'),
('ipd', 'Imperial Point Dental', 'IPD', 'SCDP Imperial Point', 'imperial_point', 'silvercreek'),
('efd_ii', 'Encinitas Family Dental II', 'EFD II', 'SCDP Encinitas II', 'encinitas_2', 'silvercreek'),
('rd', 'Rancho Dental', 'RD', 'SCDP Rancho', 'rancho', 'silvercreek'),
('lsd', 'La Senda Dental', 'LSD', 'SCDP La Senda', 'la_senda', 'silvercreek'),
('ucfd', 'University City Family Dental', 'UCFD', 'SCDP University City', 'university_city', 'silvercreek'),
('lcd', 'La Costa Dental', 'LCD', 'SCDP La Costa', 'la_costa', 'silvercreek'),
('eawd', 'East Avenue Dental', 'EAWD', 'SCDP East Avenue', 'east_avenue', 'silvercreek'),
('sed', 'Scripps Eastlake Dental', 'SED', 'SCDP Eastlake', 'eastlake', 'silvercreek'),
('dd', 'Downtown Dental', 'DD', 'SCDP Downtown', 'downtown', 'silvercreek');

SELECT 'Practice master table created with 14 practices' AS status;

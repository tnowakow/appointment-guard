-- Create patients and providers tables with sample data matching your appointments
-- Run this in Supabase SQL Editor: https://supabase.com/dashboard/project/jmkwrxtxfkvydjmlrmya/sql/new

-- Drop existing tables if they exist (safe to run multiple times)
DROP TABLE IF EXISTS patients CASCADE;
DROP TABLE IF EXISTS providers CASCADE;

-- Create patients table
CREATE TABLE patients (
    id UUID PRIMARY KEY,
    patient_name VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    phone VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create providers table  
CREATE TABLE providers (
    id UUID PRIMARY KEY,
    provider_name VARCHAR(255) NOT NULL,
    specialty VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Insert patients matching the patient_ids from your appointments
INSERT INTO patients (id, patient_name, email, phone) VALUES
('8d7b3c5e-4a2f-1b3c-9d4e-5f6a7b8c9d0e', 'John Doe', 'john.doe@email.com', '+15551234567'),
('9e8c4d6f-5b3g-2c4d-0e5f-6g7h8i9j0k1l', 'Jane Smith', 'jane.smith@email.com', '+15559876543'),
('a0f9e5g0-6c4h-3d5e-1f6g-7h8i9j0k1l2m', 'Bob Wilson', 'bob.wilson@email.com', '+15555678901'),
('b1ga0f1-7d5i-4e6f-2g7h-8i9j0k1l2m3n', 'Alice Brown', 'alice.brown@email.com', '+15553456789'),
('c2hb1g2-8e6j-5f7g-3h8i-9j0k1l2m3n4o', 'Charlie Davis', 'charlie.davis@email.com', '+15552345678'),
('d3ic2h3-9f7k-6g8h-4i9j-0k1l2m3n4o5p', 'Diana Evans', 'diana.evans@email.com', '+15554567890'),
('e4jd3i4-0g8l-7h9i-5j0k-1l2m3n4o5p6q', 'Edward Foster', 'edward.foster@email.com', '+15556789012')
ON CONFLICT (id) DO NOTHING;

-- Insert providers matching the provider_ids from your appointments  
INSERT INTO providers (id, provider_name, specialty) VALUES
('1a2b3c4d-5e6f-7a8b-9c0d-1e2f3a4b5c6d', 'Dr. Smith', 'General Dentistry'),
('2b3c4d5e-6f7g-8h9i-0j1k-2l3m4n5o6p7q', 'Dr. Johnson', 'Orthodontics'),
('3c4d5e6f-7g8h-9i0j-1k2l-3m4n5o6p7q8r', 'Dr. Williams', 'Oral Surgery'),
('4d5e6f7g-8h9i-0j1k-2l3m-4n5o6p7q8r9s', 'Dr. Brown', 'Pediatric Dentistry')
ON CONFLICT (id) DO NOTHING;

-- Verify the data was inserted
SELECT 'Patients' as table_name, COUNT(*) as count FROM patients
UNION ALL
SELECT 'Providers' as table_name, COUNT(*) as count FROM providers;

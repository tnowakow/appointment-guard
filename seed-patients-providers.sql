-- Seed patients and providers tables for AppointmentGuard
-- Run this in Supabase SQL Editor

-- Create patients table if not exists
CREATE TABLE IF NOT EXISTS patients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_name VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    phone VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create providers table if not exists  
CREATE TABLE IF NOT EXISTS providers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    provider_name VARCHAR(255) NOT NULL,
    specialty VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Insert sample patients matching the appointment patient_ids
INSERT INTO patients (id, patient_name, email, phone) VALUES
('8d7b3c5e-4a2f-1b3c-9d4e-5f6a7b8c9d0e', 'John Doe', 'john.doe@email.com', '+15551234567'),
('9e8c4d6f-5b3g-2c4d-0e5f-6g7h8i9j0k1l', 'Jane Smith', 'jane.smith@email.com', '+15559876543'),
('a0f9e5g0-6c4h-3d5e-1f6g-7h8i9j0k1l2m', 'Bob Wilson', 'bob.wilson@email.com', '+15555678901'),
('b1ga0f1-7d5i-4e6f-2g7h-8i9j0k1l2m3n', 'Alice Brown', 'alice.brown@email.com', '+15553456789'),
('c2hb1g2-8e6j-5f7g-3h8i-9j0k1l2m3n4o', 'Charlie Davis', 'charlie.davis@email.com', '+15552345678')
ON CONFLICT (id) DO NOTHING;

-- Insert sample providers matching the appointment provider_ids
INSERT INTO providers (id, provider_name, specialty) VALUES
('1a2b3c4d-5e6f-7a8b-9c0d-1e2f3a4b5c6d', 'Dr. Smith', 'General Dentistry'),
('2b3c4d5e-6f7g-8h9i-0j1k-2l3m4n5o6p7q', 'Dr. Johnson', 'Orthodontics'),
('3c4d5e6f-7g8h-9i0j-1k2l-3m4n5o6p7q8r', 'Dr. Williams', 'Oral Surgery')
ON CONFLICT (id) DO NOTHING;

-- Verify the data
SELECT 'Patients' as table_name, COUNT(*) as count FROM patients
UNION ALL
SELECT 'Providers' as table_name, COUNT(*) as count FROM providers;

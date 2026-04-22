-- ============================================
-- SEED TEST DATA FOR APPOINTMENTGUARD
-- Run this in Supabase SQL Editor to add sample appointments
-- ============================================

-- Insert test providers
INSERT INTO providers (provider_name, specialty) VALUES
('Dr. Smith', 'General Practice'),
('Dr. Johnson', 'Dentistry'),
('Dr. Martinez', 'Cardiology')
ON CONFLICT DO NOTHING;

-- Insert test patients
INSERT INTO patients (patient_name, patient_phone, email) VALUES
('John Doe', '+15551234567', 'john.doe@example.com'),
('Jane Smith', '+15559876543', 'jane.smith@example.com'),
('Bob Wilson', '+15555678901', 'bob.wilson@example.com'),
('Alice Brown', '+15553456789', 'alice.brown@example.com')
ON CONFLICT DO NOTHING;

-- Insert test appointments (upcoming)
INSERT INTO appointments (patient_id, provider_id, appointment_date, appointment_time, status)
SELECT 
    p.id as patient_id,
    pr.id as provider_id,
    CURRENT_DATE + INTERVAL '1 day' as appointment_date,
    '14:00:00'::time as appointment_time,
    'scheduled' as status
FROM patients p
JOIN providers pr ON pr.provider_name = 'Dr. Smith'
WHERE p.patient_name = 'John Doe';

INSERT INTO appointments (patient_id, provider_id, appointment_date, appointment_time, status)
SELECT 
    p.id as patient_id,
    pr.id as provider_id,
    CURRENT_DATE + INTERVAL '2 days' as appointment_date,
    '10:30:00'::time as appointment_time,
    'scheduled' as status
FROM patients p
JOIN providers pr ON pr.provider_name = 'Dr. Johnson'
WHERE p.patient_name = 'Jane Smith';

INSERT INTO appointments (patient_id, provider_id, appointment_date, appointment_time, status)
SELECT 
    p.id as patient_id,
    pr.id as provider_id,
    CURRENT_DATE + INTERVAL '3 days' as appointment_date,
    '09:00:00'::time as appointment_time,
    'scheduled' as status
FROM patients p
JOIN providers pr ON pr.provider_name = 'Dr. Smith'
WHERE p.patient_name = 'Bob Wilson';

INSERT INTO appointments (patient_id, provider_id, appointment_date, appointment_time, status)
SELECT 
    p.id as patient_id,
    pr.id as provider_id,
    CURRENT_DATE + INTERVAL '4 days' as appointment_date,
    '15:30:00'::time as appointment_time,
    'scheduled' as status
FROM patients p
JOIN providers pr ON pr.provider_name = 'Dr. Martinez'
WHERE p.patient_name = 'Alice Brown';

-- Verify the data was inserted
SELECT 
    a.id,
    p.patient_name,
    pr.provider_name,
    a.appointment_date,
    a.appointment_time,
    a.status
FROM appointments a
JOIN patients p ON a.patient_id = p.id
JOIN providers pr ON a.provider_id = pr.id
ORDER BY a.appointment_date, a.appointment_time;

-- Test the secure function
SELECT * FROM get_public_appointments();

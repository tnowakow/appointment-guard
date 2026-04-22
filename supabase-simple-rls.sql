-- ============================================
-- SIMPLE RLS SETUP (ALTERNATIVE TO RPC FUNCTION)
-- Allows direct table queries with anon key, but filters sensitive columns via view
-- ============================================

-- Step 1: Enable RLS on all tables
ALTER TABLE appointments ENABLE ROW LEVEL SECURITY;
ALTER TABLE patients ENABLE ROW LEVEL SECURITY;
ALTER TABLE providers ENABLE ROW LEVEL SECURITY;

-- Step 2: Drop existing policies
DROP POLICY IF EXISTS "Allow public read access to appointments" ON appointments;
DROP POLICY IF EXISTS "Backend full access to appointments" ON appointments;
DROP POLICY IF EXISTS "Allow public read access to patients" ON patients;
DROP POLICY IF EXISTS "Backend full access to patients" ON patients;
DROP POLICY IF EXISTS "Allow public read access to providers" ON providers;
DROP POLICY IF EXISTS "Backend full access to providers" ON providers;

-- Step 3: Create a view that excludes sensitive data (for anon key)
DROP VIEW IF EXISTS appointments_safe_view CASCADE;
CREATE VIEW appointments_safe_view AS
SELECT 
    a.id,
    a.patient_id,
    a.provider_id,
    a.appointment_date,
    a.appointment_time,
    a.status,
    p.patient_name,
    -- Intentionally NOT including patient_phone or email
    pr.provider_name
FROM appointments a
LEFT JOIN patients p ON a.patient_id = p.id
LEFT JOIN providers pr ON a.provider_id = pr.id;

-- Step 4: Grant SELECT on the view to anon
GRANT SELECT ON appointments_safe_view TO anon;
GRANT SELECT ON appointments_safe_view TO authenticated;

-- Step 5: Allow service_role full access to raw tables (for backend writes)
CREATE POLICY "service_role_full_appointments" ON appointments FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY "service_role_full_patients" ON patients FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY "service_role_full_providers" ON providers FOR ALL TO service_role USING (true) WITH CHECK (true);

-- Step 6: Allow anon to read from the safe view only
-- (Views don't support RLS, but we control access via GRANT)

-- Test the view
SELECT * FROM appointments_safe_view LIMIT 5;

-- ============================================
-- SECURE SUPABASE SETUP FOR APPOINTMENTGUARD (V2)
-- Uses functions instead of views for security
-- ============================================

-- Step 1: Enable RLS on all tables
ALTER TABLE appointments ENABLE ROW LEVEL SECURITY;
ALTER TABLE patients ENABLE ROW LEVEL SECURITY;
ALTER TABLE providers ENABLE ROW LEVEL SECURITY;

-- Step 2: Drop existing policies
DROP POLICY IF EXISTS "Allow public read access to appointments" ON appointments;
DROP POLICY IF EXISTS "Allow authenticated users to manage appointments" ON appointments;
DROP POLICY IF EXISTS "Allow public read access to patients" ON patients;
DROP POLICY IF EXISTS "Allow authenticated users to manage patients" ON patients;
DROP POLICY IF EXISTS "Allow public read access to providers" ON providers;
DROP POLICY IF EXISTS "Allow authenticated users to manage providers" ON providers;

-- Step 3: Create secure function that returns safe data only
-- This function can be called by anon key and won't expose sensitive columns
CREATE OR REPLACE FUNCTION get_public_appointments()
RETURNS TABLE (
    id UUID,
    patient_id UUID,
    provider_id UUID,
    appointment_date DATE,
    appointment_time TIME,
    status TEXT,
    patient_name TEXT,
    provider_name TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        a.id,
        a.patient_id,
        a.provider_id,
        a.appointment_date,
        a.appointment_time,
        a.status,
        p.patient_name,
        pr.provider_name
    FROM appointments a
    LEFT JOIN patients p ON a.patient_id = p.id
    LEFT JOIN providers pr ON a.provider_id = pr.id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Step 4: Restrictive RLS policies on actual tables
-- Tables are ONLY accessible to authenticated service role (backend)

DROP POLICY IF EXISTS "Backend full access to appointments" ON appointments;
CREATE POLICY "Backend full access to appointments"
ON appointments FOR ALL
TO service_role
USING (true)
WITH CHECK (true);

DROP POLICY IF EXISTS "Backend full access to patients" ON patients;
CREATE POLICY "Backend full access to patients"
ON patients FOR ALL
TO service_role
USING (true)
WITH CHECK (true);

DROP POLICY IF EXISTS "Backend full access to providers" ON providers;
CREATE POLICY "Backend full access to providers"
ON providers FOR ALL
TO service_role
USING (true)
WITH CHECK (true);

-- Step 5: Grant execute permission on the function to anon
GRANT EXECUTE ON FUNCTION get_public_appointments() TO anon;
GRANT EXECUTE ON FUNCTION get_public_appointments() TO authenticated;

-- Verify setup
SELECT 
    'appointments' as table_name,
    rowsecurity as rls_enabled
FROM pg_tables WHERE tablename = 'appointments' AND schemaname = 'public'
UNION ALL
SELECT 
    'patients',
    rowsecurity
FROM pg_tables WHERE tablename = 'patients' AND schemaname = 'public'
UNION ALL
SELECT 
    'providers',
    rowsecurity
FROM pg_tables WHERE tablename = 'providers' AND schemaname = 'public';

-- Test the function (this should work with anon key)
SELECT * FROM get_public_appointments() LIMIT 5;

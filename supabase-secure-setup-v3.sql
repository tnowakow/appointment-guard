-- ============================================
-- SECURE SUPABASE SETUP FOR APPOINTMENTGUARD (V3)
-- Fixed type mismatch for status column
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

-- Step 3: Drop old function if exists
DROP FUNCTION IF EXISTS get_public_appointments();

-- Step 4: Create secure function with correct types
CREATE OR REPLACE FUNCTION get_public_appointments()
RETURNS TABLE (
    id UUID,
    patient_id UUID,
    provider_id UUID,
    appointment_date DATE,
    appointment_time TIME,
    status VARCHAR(20),
    patient_name TEXT,
    provider_name TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        a.id::UUID,
        a.patient_id::UUID,
        a.provider_id::UUID,
        a.appointment_date::DATE,
        a.appointment_time::TIME,
        a.status::VARCHAR(20),
        p.patient_name::TEXT,
        pr.provider_name::TEXT
    FROM appointments a
    LEFT JOIN patients p ON a.patient_id = p.id
    LEFT JOIN providers pr ON a.provider_id = pr.id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Step 5: Restrictive RLS policies on actual tables
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

-- Step 6: Grant execute permission on the function to anon
GRANT EXECUTE ON FUNCTION get_public_appointments() TO anon;
GRANT EXECUTE ON FUNCTION get_public_appointments() TO authenticated;

-- Verify setup
SELECT 
    'appointments' as table_name,
    rowsecurity as rls_enabled
FROM pg_tables WHERE tablename = 'appointments' AND schemaname = 'public';

-- Test the function
SELECT * FROM get_public_appointments() LIMIT 5;

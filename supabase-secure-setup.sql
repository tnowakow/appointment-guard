-- ============================================
-- SECURE SUPABASE SETUP FOR APPOINTMENTGUARD
-- ============================================

-- Step 1: Enable RLS on all tables (already done, but ensure it's enforced)
ALTER TABLE appointments FORCE ROW LEVEL SECURITY;
ALTER TABLE patients FORCE ROW LEVEL SECURITY;
ALTER TABLE providers FORCE ROW LEVEL SECURITY;

-- Step 2: Drop existing policies
DROP POLICY IF EXISTS "Allow public read access to appointments" ON appointments;
DROP POLICY IF EXISTS "Allow authenticated users to manage appointments" ON appointments;
DROP POLICY IF EXISTS "Allow public read access to patients" ON patients;
DROP POLICY IF EXISTS "Allow authenticated users to manage patients" ON patients;
DROP POLICY IF EXISTS "Allow public read access to providers" ON providers;
DROP POLICY IF EXISTS "Allow authenticated users to manage providers" ON providers;

-- Step 3: Create secure views that exclude sensitive data
-- These views will be what the frontend queries via anon key

-- View for appointments (safe columns only)
CREATE OR REPLACE VIEW public.appointments_public AS
SELECT 
    a.id,
    a.patient_id,
    a.provider_id,
    a.appointment_date,
    a.appointment_time,
    a.status,
    p.patient_name,
    -- Don't expose patient_phone or email in public view
    pr.provider_name
FROM appointments a
LEFT JOIN patients p ON a.patient_id = p.id
LEFT JOIN providers pr ON a.provider_id = pr.id;

-- Step 4: Restrictive RLS policies on actual tables
-- Tables are ONLY accessible to authenticated service role (backend)

-- Appointments - only service role can access raw table
DROP POLICY IF EXISTS "Backend full access to appointments" ON appointments;
CREATE POLICY "Backend full access to appointments"
ON appointments FOR ALL
TO service_role
USING (true)
WITH CHECK (true);

-- Patients - only service role can access raw table  
DROP POLICY IF EXISTS "Backend full access to patients" ON patients;
CREATE POLICY "Backend full access to patients"
ON patients FOR ALL
TO service_role
USING (true)
WITH CHECK (true);

-- Providers - only service role can access raw table
DROP POLICY IF EXISTS "Backend full access to providers" ON providers;
CREATE POLICY "Backend full access to providers"
ON providers FOR ALL
TO service_role
USING (true)
WITH CHECK (true);

-- Step 5: Allow anon key to READ from the public view only
-- This exposes safe data without sensitive columns
DROP POLICY IF EXISTS "Allow anon read from appointments_public view" ON appointments_public;
CREATE POLICY "Allow anon read from appointments_public view"
ON appointments_public FOR SELECT
TO anon
USING (true);

-- Step 6: Update the backend to use service role key for full access
-- The frontend will query the view via anon key

-- Verify setup
SELECT 
    'appointments' as table_name,
    rowsecurity as rls_enabled,
    'Use appointments_public view for frontend' as note
FROM pg_tables WHERE tablename = 'appointments' AND schemaname = 'public'
UNION ALL
SELECT 
    'patients',
    rowsecurity,
    'Sensitive data hidden from anon key'
FROM pg_tables WHERE tablename = 'patients' AND schemaname = 'public'
UNION ALL
SELECT 
    'providers',
    rowsecurity,
    'Safe to query via view'
FROM pg_tables WHERE tablename = 'providers' AND schemaname = 'public';

-- Test the view
SELECT * FROM appointments_public LIMIT 5;

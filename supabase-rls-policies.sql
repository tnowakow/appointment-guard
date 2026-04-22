-- Enable Row Level Security on all tables
ALTER TABLE appointments ENABLE ROW LEVEL SECURITY;
ALTER TABLE patients ENABLE ROW LEVEL SECURITY;
ALTER TABLE providers ENABLE ROW LEVEL SECURITY;

-- Drop existing policies if they exist (safe to run multiple times)
DROP POLICY IF EXISTS "Allow public read access to appointments" ON appointments;
DROP POLICY IF EXISTS "Allow authenticated users to manage appointments" ON appointments;
DROP POLICY IF EXISTS "Allow public read access to patients" ON patients;
DROP POLICY IF EXISTS "Allow authenticated users to manage patients" ON patients;
DROP POLICY IF EXISTS "Allow public read access to providers" ON providers;
DROP POLICY IF EXISTS "Allow authenticated users to manage providers" ON providers;

-- Appointments policies
-- 1. Allow anyone with anon key to READ appointments (for the dashboard)
CREATE POLICY "Allow public read access to appointments"
ON appointments FOR SELECT
USING (true);

-- 2. Only authenticated service role can INSERT/UPDATE/DELETE appointments
CREATE POLICY "Allow authenticated users to manage appointments"
ON appointments FOR ALL
TO authenticated
USING (true)
WITH CHECK (true);

-- Patients policies
-- 1. Allow anyone with anon key to READ patient info (needed for appointment display)
CREATE POLICY "Allow public read access to patients"
ON patients FOR SELECT
USING (true);

-- 2. Only authenticated service role can modify patients
CREATE POLICY "Allow authenticated users to manage patients"
ON patients FOR ALL
TO authenticated
USING (true)
WITH CHECK (true);

-- Providers policies
-- 1. Allow anyone with anon key to READ provider info (needed for appointment display)
CREATE POLICY "Allow public read access to providers"
ON providers FOR SELECT
USING (true);

-- 2. Only authenticated service role can modify providers
CREATE POLICY "Allow authenticated users to manage providers"
ON providers FOR ALL
TO authenticated
USING (true)
WITH CHECK (true);

-- Verify RLS is enabled
SELECT tablename, rowsecurity 
FROM pg_tables 
WHERE schemaname = 'public' 
AND tablename IN ('appointments', 'patients', 'providers');

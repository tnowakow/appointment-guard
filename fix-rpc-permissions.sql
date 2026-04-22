-- ============================================
-- FIX RPC FUNCTION PERMISSIONS
-- Ensures get_public_appointments() can be called via REST API with anon key
-- ============================================

-- Drop and recreate the function with proper SECURITY DEFINER
DROP FUNCTION IF EXISTS get_public_appointments();

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
        a.id::UUID,
        a.patient_id::UUID,
        a.provider_id::UUID,
        a.appointment_date::DATE,
        a.appointment_time::TIME,
        a.status::TEXT,
        p.patient_name::TEXT,
        pr.provider_name::TEXT
    FROM appointments a
    LEFT JOIN patients p ON a.patient_id = p.id
    LEFT JOIN providers pr ON a.provider_id = pr.id
    WHERE a.appointment_date >= CURRENT_DATE
      AND a.status NOT IN ('completed', 'cancelled')
    ORDER BY a.appointment_date ASC, a.appointment_time ASC;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Grant execute permission to anon role (required for RPC calls)
GRANT EXECUTE ON FUNCTION get_public_appointments() TO anon;
GRANT EXECUTE ON FUNCTION get_public_appointments() TO authenticated;

-- Also grant usage on the tables so SECURITY DEFINER can read them
GRANT USAGE ON SCHEMA public TO anon;
GRANT SELECT ON appointments TO anon;
GRANT SELECT ON patients TO anon;
GRANT SELECT ON providers TO anon;

-- Test it works
SELECT * FROM get_public_appointments();

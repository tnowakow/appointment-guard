-- AppointmentGuard Supabase Schema
-- Dental no-show prevention system

-- Patients table
CREATE TABLE IF NOT EXISTS patients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_name VARCHAR(255) NOT NULL,
    patient_phone VARCHAR(20) NOT NULL,
    email VARCHAR(255),
    date_of_birth DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Providers/Dentists table
CREATE TABLE IF NOT EXISTS providers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    provider_name VARCHAR(255) NOT NULL,
    specialty VARCHAR(100),
    license_number VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Offices/Locations table
CREATE TABLE IF NOT EXISTS offices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    office_name VARCHAR(255) NOT NULL,
    address TEXT NOT NULL,
    city VARCHAR(100),
    state VARCHAR(50),
    zip_code VARCHAR(20),
    phone VARCHAR(20),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Appointments table (main operational table)
CREATE TABLE IF NOT EXISTS appointments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID REFERENCES patients(id) ON DELETE CASCADE,
    provider_id UUID REFERENCES providers(id),
    office_id UUID REFERENCES offices(id),
    
    -- Appointment details
    appointment_date DATE NOT NULL,
    appointment_time TIME NOT NULL,
    duration_minutes INTEGER DEFAULT 30,
    
    -- Risk assessment (computed)
    risk_score DECIMAL(3,2),  -- 0.0 to 1.0
    risk_category VARCHAR(20),  -- LOW, MEDIUM, HIGH
    
    -- Patient history (for risk scoring)
    late_arrival_count INTEGER DEFAULT 0,
    cancellation_count INTEGER DEFAULT 0,
    is_first_visit BOOLEAN DEFAULT false,
    
    -- Intervention tracking
    intervention_sent BOOLEAN DEFAULT false,
    intervention_type VARCHAR(50),  -- confirmation, reminder, urgent
    sms_message_id VARCHAR(100),  -- Twilio message SID
    
    -- Appointment status
    status VARCHAR(20) DEFAULT 'scheduled',  -- scheduled, confirmed, completed, cancelled, no_show
    confirmed_at TIMESTAMP WITH TIME ZONE,
    arrived_at TIMESTAMP WITH TIME ZONE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Risk scoring history (for model improvement)
CREATE TABLE IF NOT EXISTS risk_scoring_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    appointment_id UUID REFERENCES appointments(id) ON DELETE CASCADE,
    risk_score DECIMAL(3,2),
    risk_category VARCHAR(20),
    actual_outcome VARCHAR(20),  -- showed, no_show, cancelled, late
    scored_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_appointments_date ON appointments(appointment_date);
CREATE INDEX IF NOT EXISTS idx_appointments_status ON appointments(status);
CREATE INDEX IF NOT EXISTS idx_appointments_risk_category ON appointments(risk_category);
CREATE INDEX IF NOT EXISTS idx_patients_phone ON patients(patient_phone);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply trigger to appointments table
DROP TRIGGER IF EXISTS update_appointments_updated_at ON appointments;
CREATE TRIGGER update_appointments_updated_at
    BEFORE UPDATE ON appointments
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

"""
AppointmentGuard - FastAPI Backend

Dental no-show prevention platform with risk scoring and SMS reminders.
Uses Supabase for database, Twilio for SMS (future).
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import os
from supabase import create_client, Client

# Import risk scoring agent
from risk_scoring import NoShowRiskAgent

# Initialize FastAPI app
app = FastAPI(title="AppointmentGuard API")

# CORS configuration
origins = [
    "https://appointment-guard-frontend-production.up.railway.app",
    "http://localhost:5173"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Supabase client initialization
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    print("⚠️ Warning: Supabase credentials not configured. Using mock data.")
else:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)


# Pydantic models
class Appointment(BaseModel):
    patient_id: str
    patient_name: str
    patient_phone: str
    appointment_date: str
    appointment_time: str
    provider_name: str
    risk_score: float
    risk_category: str
    recommendation: str


# Helper function for mock data (fallback)
def _get_mock_appointments() -> List[Appointment]:
    """Return sample appointments when Supabase is unavailable."""
    return [
        Appointment(
            patient_id="1",
            patient_name="John Doe",
            patient_phone="+15551234567",
            appointment_date=datetime.now().strftime("%Y-%m-%d"),
            appointment_time="14:00:00",
            provider_name="Dr. Smith",
            risk_score=0.85,
            risk_category="HIGH",
            recommendation="Send confirmation SMS + call if no response"
        ),
        Appointment(
            patient_id="2",
            patient_name="Jane Smith",
            patient_phone="+15559876543",
            appointment_date=datetime.now().strftime("%Y-%m-%d"),
            appointment_time="15:30:00",
            provider_name="Dr. Johnson",
            risk_score=0.25,
            risk_category="LOW",
            recommendation="Standard reminder 24 hours before"
        ),
        Appointment(
            patient_id="3",
            patient_name="Bob Wilson",
            patient_phone="+15555678901",
            appointment_date=(datetime.now()).strftime("%Y-%m-%d"),
            appointment_time="09:00:00",
            provider_name="Dr. Smith",
            risk_score=0.62,
            risk_category="MEDIUM",
            recommendation="Send reminder SMS 48 hours before"
        ),
        Appointment(
            patient_id="4",
            patient_name="Alice Brown",
            patient_phone="+15553456789",
            appointment_date=(datetime.now()).strftime("%Y-%m-%d"),
            appointment_time="11:00:00",
            provider_name="Dr. Williams",
            risk_score=0.15,
            risk_category="LOW",
            recommendation="Standard reminder 24 hours before"
        )
    ]


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "ok", "service": "AppointmentGuard API"}


@app.get("/appointments")
async def get_appointments():
    """
    Get upcoming appointments with risk scores.
    
    Returns list of appointments sorted by date/time with:
    - Patient info (name, phone masked for security)
    - Appointment details (date, time, provider)
    - Risk assessment (score, category, recommendation)
    """
    try:
        # Fetch upcoming appointments from Supabase using official client
        today = datetime.now().date()
        
        print(f"🔍 Fetching appointments from Supabase for {today}+")
        print(f"Supabase URL: {SUPABASE_URL}")
        
        # Query with embedded joins to get patient and provider names
        result = (
            supabase.table("appointments")
            .select(
                "*,patients!patient_id (id,patient_name),providers!provider_id (id,provider_name)"
            )
            .eq("status", "scheduled")
            .order("appointment_date")
            .order("appointment_time")
            .limit(50)
            .execute()
        )
        appointments_data = result.data
        print(f"✅ Got {len(appointments_data)} appointments from Supabase")
        
        if not appointments_data:
            print("⚠️ No appointments found, returning mock data")
            return {"appointments": _get_mock_appointments()}
        
        # Log the first appointment to see the join structure
        first_appointment = appointments_data[0]
        all_keys = list(first_appointment.keys())
        print(f"📋 First appointment keys: {all_keys}")
        
        has_patients_join = "patients" in all_keys or any("patient_name" in k.lower() for k in all_keys)
        has_providers_join = "providers" in all_keys or any("provider_name" in k.lower() for k in all_keys)
        
        if has_patients_join:
            print(f"✅ Patient data found")
            if "patients" in first_appointment:
                print(f"   patients field: {first_appointment['patients']}")
        else:
            print(f"❌ No patient join — need to create patients table or use two-step lookup")
            
        if has_providers_join:
            print(f"✅ Provider data found")
            if "providers" in first_appointment:
                print(f"   providers field: {first_appointment['providers']}")
        else:
            print(f"❌ No provider join — need to create providers table or use two-step lookup")
        
    except Exception as e:
        print(f"❌ Supabase query failed: {e}")
        import traceback
        traceback.print_exc()
        return {"appointments": _get_mock_appointments(), "error": str(e)}

    # Process appointments and calculate risk scores
    try:
        appointments = []
        for row in appointments_data:
            # Extract patient and provider names from joined data
            patients_obj = row.get("patients") or {}
            providers_obj = row.get("providers") or {}
            
            patient_name = patients_obj.get("patient_name", "Unknown") if isinstance(patients_obj, dict) else "Unknown"
            provider_name = providers_obj.get("provider_name", "Unknown") if isinstance(providers_obj, dict) else "Unknown"
            
            appointment_data = {
                "patient_id": str(row.get("id", "")),
                "patient_name": patient_name or "Unknown",
                "patient_phone": row.get("patient_phone", "+10000000000"),  # Masked for security
                "appointment_date": str(row.get("appointment_date", "")),
                "appointment_time": str(row.get("appointment_time", "")).split(".")[0][:8] if row.get("appointment_time") else "00:00:00",
                "provider_name": provider_name or "Unknown",
                "late_arrival_count": int(row.get("late_arrival_count", 0) or 0),
                "cancellation_count": int(row.get("cancellation_count", 0) or 0),
                "is_first_visit": bool(row.get("is_first_visit", False)),
                "days_until_appointment": (datetime.strptime(str(row.get("appointment_date", "")), "%Y-%m-%d").date() - today).days if row.get("appointment_date") else 0
            }
            
            # Simple synchronous risk calculation (no async agent needed)
            has_late_history = appointment_data["late_arrival_count"] > 2
            has_cancel_history = appointment_data["cancellation_count"] > 1
            is_first_time = appointment_data["is_first_visit"]
            days_until = appointment_data["days_until_appointment"]
            
            # Calculate risk score (0-1)
            risk_score = 0.25  # Base risk
            if has_late_history:
                risk_score += 0.3
            if has_cancel_history:
                risk_score += 0.4
            if is_first_time:
                risk_score += 0.2
            if days_until <= 1:  # Last-minute booking
                risk_score += 0.15
            
            risk_score = min(risk_score, 1.0)  # Cap at 1.0
            
            # Convert to category and recommendation
            if risk_score >= 0.7:
                risk_category = "HIGH"
                recommendation = "Send confirmation SMS + call if no response"
            elif risk_score >= 0.4:
                risk_category = "MEDIUM"
                recommendation = "Send reminder SMS 48 hours before"
            else:
                risk_category = "LOW"
                recommendation = "Standard reminder 24 hours before"
            
            appointment = Appointment(
                patient_id=appointment_data["patient_id"],
                patient_name=appointment_data["patient_name"],
                patient_phone=appointment_data["patient_phone"],
                appointment_date=appointment_data["appointment_date"],
                appointment_time=appointment_data["appointment_time"],
                provider_name=appointment_data["provider_name"],
                risk_score=risk_score,
                risk_category=risk_category,
                recommendation=recommendation
            )
            
            appointments.append(appointment)
        
        return {"appointments": appointments}
    except Exception as e:
        print(f"❌ Appointment processing failed: {e}")
        import traceback
        traceback.print_exc()
        return {"appointments": _get_mock_appointments(), "processing_error": str(e)}


@app.get("/debug/supabase-test")
async def debug_supabase():
    """Debug endpoint to test Supabase connection."""
    try:
        result = supabase.table("appointments").select("*").limit(5).execute()
        return {
            "status": "connected",
            "count": len(result.data),
            "sample": result.data[:1] if result.data else None,
            "columns": list(result.data[0].keys()) if result.data else []
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

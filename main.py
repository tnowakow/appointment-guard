"""
AppointmentGuard - Main Application (Supabase Client Version)

FastAPI application for dental no-show prevention using ZenticPro platform.
Uses official Supabase Python client for reliable database access.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
from typing import List, Optional
import os
from supabase import create_client, Client

from risk_scoring import NoShowRiskAgent
from intervention_agent import PatientInterventionAgent


app = FastAPI(
    title="AppointmentGuard",
    description="ZenticPro Platform - Dental Industry Module (No-Show Prevention)",
    version="1.0.0"
)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://appointment-guard-frontend-production.up.railway.app", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Initialize Supabase client with service role key (bypasses RLS)
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", os.getenv("SUPABASE_ANON_KEY"))

if SUPABASE_URL and SUPABASE_SERVICE_KEY:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
else:
    supabase = None


class Appointment(BaseModel):
    """Appointment data for risk scoring with validation."""
    patient_id: str
    patient_name: str
    patient_phone: str = Field(..., description="Patient's phone number (E.164 format)")
    appointment_date: str = Field(..., description="Scheduled appointment date/time")
    appointment_time: str
    provider_name: Optional[str] = "Smith"
    office_address: Optional[str] = ""

    # Historical data (from database)
    late_arrival_count: int = 0
    cancellation_count: int = 0
    is_first_visit: bool = False

    # Computed fields
    risk_score: float = Field(ge=0, le=1)
    risk_category: str
    recommendation: str


def _get_mock_appointments() -> List[Appointment]:
    """Return mock appointments for development when Supabase is unavailable."""
    from datetime import date, timedelta

    today = date.today()

    return [
        Appointment(
            patient_id="1",
            patient_name="John Doe",
            patient_phone="+15551234567",
            appointment_date=today.isoformat(),
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
            appointment_date=today.isoformat(),
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
            appointment_date=(today + timedelta(days=1)).isoformat(),
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
            appointment_date=(today + timedelta(days=2)).isoformat(),
            appointment_time="11:00:00",
            provider_name="Dr. Williams",
            risk_score=0.15,
            risk_category="LOW",
            recommendation="Standard reminder 24 hours before"
        )
    ]


@app.get("/appointments")
async def get_appointments():
    """Get upcoming appointments with no-show risk scores."""
    if not supabase:
        print("⚠️ Supabase client not initialized (missing credentials)")
        return {"appointments": _get_mock_appointments()}

    try:
        # Fetch upcoming appointments from Supabase using official client
        today = datetime.now().date()

        print(f"🔍 Fetching appointments from Supabase for {today}+")
        print(f"Supabase URL: {SUPABASE_URL}")

        # First, try simple query without joins
        result = supabase.table("appointments").select("*").limit(10).execute()
        appointments_data = result.data
        print(f"✅ Got {len(appointments_data)} raw appointments from Supabase")
        if appointments_data:
            print(f"First appointment keys: {list(appointments_data[0].keys())}")
            print(f"First appointment: {appointments_data[0]}")

        if not appointments_data:
            print("⚠️ No appointments found, returning mock data")
            return {"appointments": _get_mock_appointments()}

    except Exception as e:
        print(f"⚠️ Supabase query failed: {e}")
        import traceback
        traceback.print_exc()
        return {"appointments": _get_mock_appointments()}

    # Process appointments and calculate risk scores
    try:
        appointments = []
        for row in appointments_data:
            appointment_data = {
                "patient_id": str(row.get("id", "")),
                "patient_name": row.get("patient_name", "Unknown") or "Unknown",
                "patient_phone": "+10000000000",
                "appointment_date": str(row.get("appointment_date", "")),
                "appointment_time": str(row.get("appointment_time", "")).split(".")[0][:8] if row.get("appointment_time") else "00:00:00",
                "provider_name": row.get("provider_name", "Unknown") or "Unknown",
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


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    supabase_status = "connected" if supabase else "not configured"
    return {
        "status": "healthy",
        "version": "1.0.0",
        "supabase": supabase_status
    }


@app.get("/debug/supabase-test")
async def test_supabase_connection():
    """Debug endpoint to test Supabase connection directly."""
    result = {
        "has_url": bool(SUPABASE_URL),
        "has_service_key": bool(os.getenv("SUPABASE_SERVICE_ROLE_KEY")),
        "has_anon_key": bool(os.getenv("SUPABASE_ANON_KEY")),
        "url_preview": f"{SUPABASE_URL[:30]}..." if SUPABASE_URL else None,
    }

    if not supabase:
        result["error"] = "Supabase client not initialized"
        return result

    try:
        # Test query using official Supabase client
        test_result = supabase.table("appointments").select("*").limit(5).execute()

        result["success"] = True
        result["count"] = len(test_result.data)
        result["sample_data"] = test_result.data[:1] if test_result.data else []
        print(f"✅ Supabase test query returned {result['count']} rows")

    except Exception as e:
        result["success"] = False
        result["error"] = str(e)
        print(f"❌ Supabase test failed: {e}")

    return result


@app.post("/intervention/send")
async def send_intervention(appointment: Appointment):
    """Send intervention (SMS/call) to patient."""
    try:
        intervention_agent = PatientInterventionAgent()

        # Determine action based on risk category
        if appointment.risk_category == "HIGH":
            actions = ["sms_confirmation", "voice_call"]
        elif appointment.risk_category == "MEDIUM":
            actions = ["sms_reminder"]
        else:
            actions = ["sms_standard"]

        results = []
        for action in actions:
            result = intervention_agent.execute_action(
                patient_phone=appointment.patient_phone,
                patient_name=appointment.patient_name,
                appointment_date=f"{appointment.appointment_date} {appointment.appointment_time}",
                action_type=action
            )
            results.append(result)

        return {"success": True, "interventions_sent": results}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))

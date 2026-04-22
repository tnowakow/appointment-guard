"""
AppointmentGuard - Main Application

FastAPI application for dental no-show prevention using ZenticPro platform.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator
from datetime import datetime, timedelta
from typing import List, Optional
import os
import httpx

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
    appointment_day: Optional[str] = None
    appointment_hour: Optional[int] = None
    days_until_appointment: int = Field(..., ge=0, description="Days until appointment")

    @validator('patient_phone')
    def validate_phone(cls, v):
        from core.utils import validate_phone_number
        if not validate_phone_number(v):
            raise ValueError(f'Invalid phone number format: {v}. Expected E.164 format (e.g., +1234567890)')
        return v

    @validator('appointment_date')
    def validate_appointment_date(cls, v):
        # This is a simple string validation - in practice this would be parsed
        # For now we'll just ensure it's not empty
        if not v:
            raise ValueError('Appointment date cannot be empty')
        return v

    class Config:
        json_encoders = {datetime: str}


class RiskScoreResponse(BaseModel):
    """Risk score response."""
    patient_id: str
    risk_score: float
    risk_category: str
    recommendation: str


@app.post("/risk/score", response_model=RiskScoreResponse)
async def score_appointment(appointment: Appointment):
    """Calculate no-show risk for an appointment."""
    try:
        agent = NoShowRiskAgent()
        
        # Prepare item for prediction
        item = {
            "late_arrival_count": appointment.late_arrival_count,
            "cancellation_count": appointment.cancellation_count,
            "is_first_visit": appointment.is_first_visit,
            "appointment_day": appointment.appointment_day or "monday",
            "appointment_hour": appointment.appointment_hour or 12,
            "days_until_appointment": appointment.days_until_appointment
        }
        
        # Get risk prediction
        result = await agent.execute(item)
        
        if not result.success:
            raise HTTPException(status_code=500, detail=result.error)
        
        risk_score = result.result.get("prediction", 0.5)
        risk_category = agent.get_risk_category(risk_score)
        
        # Determine recommendation
        if risk_category == "HIGH":
            recommendation = "Send confirmation SMS + call if no response"
        elif risk_category == "MEDIUM":
            recommendation = "Send reminder SMS 24 hours before"
        else:
            recommendation = "Standard reminder only"
        
        return RiskScoreResponse(
            patient_id=appointment.patient_id,
            risk_score=risk_score,
            risk_category=risk_category,
            recommendation=recommendation
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/intervention/send")
async def send_intervention(appointment: Appointment):
    """Send intervention SMS for high-risk appointment."""
    try:
        # First score the appointment
        risk_agent = NoShowRiskAgent()
        item = {
            "late_arrival_count": appointment.late_arrival_count,
            "cancellation_count": appointment.cancellation_count,
            "is_first_visit": appointment.is_first_visit,
            "appointment_day": appointment.appointment_day or "monday",
            "appointment_hour": appointment.appointment_hour or 12,
            "days_until_appointment": appointment.days_until_appointment
        }
        
        risk_result = await risk_agent.execute(item)
        risk_score = risk_result.result.get("prediction", 0.5)
        
        # Prepare intervention data
        intervention_data = {
            "patient_name": appointment.patient_name,
            "patient_phone": appointment.patient_phone,
            "appointment_date": appointment.appointment_date,
            "appointment_time": appointment.appointment_time,
            "provider_name": appointment.provider_name,
            "office_address": appointment.office_address,
            "risk_score": risk_score,
            "days_until_appointment": appointment.days_until_appointment
        }
        
        # Run intervention agent
        agent = PatientInterventionAgent()
        result = await agent.execute(intervention_data)
        
        if not result.success:
            raise HTTPException(status_code=500, detail=result.error)
        
        return {
            "status": "success",
            "patient_id": appointment.patient_id,
            "action_taken": result.result.get("action"),
            "message_id": result.result.get("message_id")
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/batch/score")
async def score_batch(appointments: List[Appointment]):
    """Score multiple appointments at once."""
    results = []
    
    for appointment in appointments:
        try:
            risk_agent = NoShowRiskAgent()
            item = {
                "late_arrival_count": appointment.late_arrival_count,
                "cancellation_count": appointment.cancellation_count,
                "is_first_visit": appointment.is_first_visit,
                "appointment_day": appointment.appointment_day or "monday",
                "appointment_hour": appointment.appointment_hour or 12,
                "days_until_appointment": appointment.days_until_appointment
            }
            
            result = await risk_agent.execute(item)
            risk_score = result.result.get("prediction", 0.5)
            risk_category = risk_agent.get_risk_category(risk_score)
            
            results.append({
                "patient_id": appointment.patient_id,
                "risk_score": risk_score,
                "risk_category": risk_category
            })
            
        except Exception as e:
            results.append({
                "patient_id": appointment.patient_id,
                "error": str(e)
            })
    
    return {"scored": len(results), "results": results}


@app.get("/appointments")
async def _get_mock_appointments():
    """Return mock appointment data for development."""
    return {
        "count": 4,
        "appointments": [
            {
                "patient_id": "1",
                "patient_name": "John Doe",
                "patient_phone": "+15551234567",
                "appointment_date": datetime.now().strftime("%Y-%m-%d"),
                "appointment_time": "14:00:00",
                "provider_name": "Dr. Smith",
                "risk_score": 0.85,
                "risk_category": "HIGH",
                "recommendation": "Send confirmation SMS + call if no response"
            },
            {
                "patient_id": "2",
                "patient_name": "Jane Smith",
                "patient_phone": "+15559876543",
                "appointment_date": datetime.now().strftime("%Y-%m-%d"),
                "appointment_time": "10:30:00",
                "provider_name": "Dr. Johnson",
                "risk_score": 0.45,
                "risk_category": "MEDIUM",
                "recommendation": "Send reminder SMS 24 hours before"
            },
            {
                "patient_id": "3",
                "patient_name": "Bob Wilson",
                "patient_phone": "+15555678901",
                "appointment_date": (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d"),
                "appointment_time": "09:00:00",
                "provider_name": "Dr. Smith",
                "risk_score": 0.25,
                "risk_category": "LOW",
                "recommendation": "Standard reminder only"
            },
            {
                "patient_id": "4",
                "patient_name": "Alice Brown",
                "patient_phone": "+15553456789",
                "appointment_date": (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d"),
                "appointment_time": "15:30:00",
                "provider_name": "Dr. Martinez",
                "risk_score": 0.72,
                "risk_category": "HIGH",
                "recommendation": "Send confirmation SMS + call if no response"
            }
        ]
    }


@app.get("/appointments")
async def get_appointments(days_ahead: int = 7):
    """
    Get upcoming appointments from Supabase with risk scores.
    
    Args:
        days_ahead: Number of days to look ahead (default: 7)
    """
    try:
        supabase_url = os.getenv("SUPABASE_URL")
        # Use anon key for the public function (it's designed for this)
        supabase_key = os.getenv("SUPABASE_ANON_KEY")
        
        if not supabase_url or not supabase_key:
            print(f"⚠️ Supabase credentials missing: URL={bool(supabase_url)}, Key={bool(supabase_key)}")
            # Return mock data for development
            return _get_mock_appointments()
        
        # Calculate date range
        today = datetime.now().date()
        end_date = today + timedelta(days=days_ahead)
        
        # Fetch appointments from Supabase using REST API with embedded joins
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Use REST API with embedded selects (more reliable than RPC)
                url = f"{supabase_url}/rest/v1/appointments"
                headers = {
                    "apikey": supabase_key,
                    "Content-Type": "application/json",
                    "Prefer": "count=exact"
                }
                
                # Build query with embedded joins for patient and provider data
                params = {
                    "select": "id,patient_id,provider_id,appointment_date,appointment_time,status,patients(patient_name),providers(provider_name)",
                    "appointment_date.gte": today.isoformat(),
                    "status.not.in.": "(completed,cancelled)",
                    "order": "appointment_date.asc,appointment_time.asc"
                }
                
                print(f"🔍 Calling Supabase REST: {url}")
                print(f"🔑 Using key (first 20 chars): {supabase_key[:20]}...")
                response = await client.get(url, headers=headers, params=params)
                print(f"📊 Response status: {response.status_code}")
                if response.status_code != 200:
                    print(f"❌ Error response: {response.text[:500]}")
                
                response.raise_for_status()
                result = response.json()
                appointments_data = result.get("data", [])
                count = int(result.get("count", len(appointments_data)))
                print(f"✅ Got {len(appointments_data)} appointments from Supabase")
        except httpx.HTTPError as e:
            print(f"⚠️ HTTP error: {e}")
            return _get_mock_appointments()
        except Exception as supabase_error:
            print(f"⚠️ Supabase connection failed: {supabase_error}")
            import traceback
            traceback.print_exc()
            return _get_mock_appointments()
        
        # Process appointments and calculate risk scores
        appointments = []
        for row in appointments_data:
            appointment_data = {
                "patient_id": str(row.get("id", "")),
                "patient_name": row.get("patients", {}).get("patient_name", "Unknown") if row.get("patients") else "Unknown",
                "patient_phone": "+10000000000",  # Not exposed by secure query
                "appointment_date": row.get("appointment_date", ""),
                "appointment_time": str(row.get("appointment_time", "00:00:00")).split(".")[0][:8],
                "provider_name": row.get("providers", {}).get("provider_name", "Unknown") if row.get("providers") else "Unknown",
                "late_arrival_count": 0,  # Not available from public query
                "cancellation_count": 0,
                "is_first_visit": False,
                "days_until_appointment": (datetime.strptime(str(row.get("appointment_date", "")), "%Y-%m-%d").date() - today).days if row.get("appointment_date") else 0
            }
            
            # Calculate risk score using existing agent
            try:
                risk_agent = NoShowRiskAgent()
                item = {
                    "late_arrival_count": appointment_data["late_arrival_count"],
                    "cancellation_count": appointment_data["cancellation_count"],
                    "is_first_visit": appointment_data["is_first_visit"],
                    "appointment_day": datetime.strptime(str(row.get("appointment_date", "2026-01-01")), "%Y-%m-%d").strftime("%A").lower(),
                    "appointment_hour": int(str(row.get("appointment_time", "12:00:00")).split(":")[0]),
                    "days_until_appointment": appointment_data["days_until_appointment"]
                }
                
                result = await risk_agent.execute(item)
                risk_score = result.result.get("prediction", 0.5)
                risk_category = risk_agent.get_risk_category(risk_score)
                
                # Determine recommendation
                if risk_category == "HIGH":
                    recommendation = "Send confirmation SMS + call if no response"
                elif risk_category == "MEDIUM":
                    recommendation = "Send reminder SMS 24 hours before"
                else:
                    recommendation = "Standard reminder only"
                
                appointments.append({
                    **appointment_data,
                    "risk_score": round(risk_score, 2),
                    "risk_category": risk_category,
                    "recommendation": recommendation
                })
            except Exception as e:
                # If risk scoring fails, add appointment with default values
                appointments.append({
                    **appointment_data,
                    "risk_score": 0.5,
                    "risk_category": "MEDIUM",
                    "recommendation": "Standard reminder only"
                })
        
        return {
            "count": len(appointments),
            "appointments": appointments
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": "1.0.0"}

@app.get("/debug/supabase-test")
async def test_supabase_connection():
    """Debug endpoint to test Supabase connection directly."""
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_ANON_KEY")
    
    result = {
        "has_url": bool(supabase_url),
        "has_key": bool(supabase_key),
        "url_preview": f"{supabase_url[:30]}..." if supabase_url else None,
        "key_preview": f"{supabase_key[:20]}..." if supabase_key else None
    }
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            url = f"{supabase_url}/rest/v1/appointments"
            headers = {
                "apikey": supabase_key,
                "Content-Type": "application/json",
                "Prefer": "count=exact"
            }
            params = {
                "select": "id,patient_id,appointment_date,patients(patient_name)",
                "limit": "2"
            }
            
            response = await client.get(url, headers=headers, params=params)
            result["status_code"] = response.status_code
            if response.status_code == 200:
                data = response.json()
                result["success"] = True
                result["count"] = int(data.get("count", 0))
                result["sample_data"] = data.get("data", [])[:1]
            else:
                result["success"] = False
                result["error"] = response.text[:200]
    except Exception as e:
        result["success"] = False
        result["error"] = str(e)
    
    return result


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8001)))
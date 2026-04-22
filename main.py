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
        # Use service role key for backend access (full table access needed)
        supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", os.getenv("SUPABASE_ANON_KEY"))
        
        if not supabase_url or not supabase_key:
            print(f"⚠️ Supabase credentials missing: URL={bool(supabase_url)}, Key={bool(supabase_key)}")
            # Return mock data for development
            return _get_mock_appointments()
        
        # Calculate date range
        today = datetime.now().date()
        end_date = today + timedelta(days=days_ahead)
        
        # Fetch appointments from Supabase using the secure function
        try:
            async with httpx.AsyncClient() as client:
                # Call the get_public_appointments() RPC function
                url = f"{supabase_url}/rpc/get_public_appointments"
                headers = {
                    "Authorization": f"Bearer {supabase_key}",
                    "Content-Type": "application/json"
                }
                
                print(f"🔍 Calling Supabase RPC: {url}")
                response = await client.get(url, headers=headers)
                print(f"📊 Response status: {response.status_code}")
                if response.status_code != 200:
                    print(f"❌ Error response: {response.text[:200]}")
                
                response.raise_for_status()
                appointments_data = response.json()
                print(f"✅ Got {len(appointments_data)} appointments from Supabase")
        except Exception as supabase_error:
            print(f"⚠️ Supabase connection failed: {supabase_error}")
            return _get_mock_appointments()
        
        # Process appointments and calculate risk scores
        appointments = []
        for row in appointments_data:
            appointment_data = {
                "patient_id": str(row.get("id", "")),
                "patient_name": row.get("patient_name", "Unknown"),
                "patient_phone": "+10000000000",  # Not exposed by secure function
                "appointment_date": row.get("appointment_date", ""),
                "appointment_time": str(row.get("appointment_time", "00:00:00")).split(".")[0][:8],
                "provider_name": row.get("provider_name", "Unknown"),
                "late_arrival_count": 0,  # Not available from public function
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8001)))
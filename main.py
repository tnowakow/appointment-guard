"""
AppointmentGuard - Main Application

FastAPI application for dental no-show prevention using ZenticPro platform.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import List, Optional
import os

from risk_scoring import NoShowRiskAgent
from intervention_agent import PatientInterventionAgent


app = FastAPI(
    title="AppointmentGuard",
    description="ZenticPro Platform - Dental Industry Module (No-Show Prevention)",
    version="1.0.0"
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


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": "1.0.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8001)))
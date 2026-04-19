"""
Dental Industry - Patient Intervention Agent

Handles automated SMS outreach for high-risk appointments to reduce no-shows.
Uses ZenticPro TwilioService and NotificationEngine.
"""

from typing import Dict, Any, Optional
from agents.base_agent import BaseAgent, AgentInput, AgentOutput
from core.twilio_service import TwilioService


class PatientInterventionAgent(BaseAgent):
    """Automated patient outreach for appointment confirmation and reminders."""
    
    name = "PatientInterventionAgent"
    version = "1.0.0"
    
    def __init__(self):
        super().__init__()
        self.twilio = TwilioService()
    
    async def process(self, input: AgentInput) -> AgentOutput:
        """Process intervention for a high-risk appointment."""
        try:
            patient_data = input.data
            
            # Determine intervention type based on risk level and timing
            risk_score = patient_data.get("risk_score", 0.5)
            days_until = patient_data.get("days_until_appointment", 7)
            
            if risk_score >= 0.7 and days_until <= 3:
                # High risk + close appointment → send confirmation SMS + request reply
                result = await self._send_confirmation_request(patient_data)
            elif risk_score >= 0.4 and days_until == 1:
                # Medium risk + tomorrow → send reminder
                result = await self._send_reminder(patient_data)
            else:
                return AgentOutput(
                    success=True,
                    result={"action": "no_intervention_needed", "reasoning": "Risk too low or timing not optimal"}
                )
            
            return AgentOutput(
                success=result.get("sent", False),
                result=result,
                reasoning=f"Intervention sent for {patient_data.get('patient_name', 'patient')}"
            )
            
        except Exception as e:
            return AgentOutput(
                success=False,
                error=f"Intervention failed: {str(e)}"
            )
    
    async def _send_confirmation_request(self, patient_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send SMS requesting appointment confirmation."""
        patient_name = patient_data.get("patient_name", "there")
        appointment_date = patient_data.get("appointment_date", "your scheduled date")
        appointment_time = patient_data.get("appointment_time", "time")
        
        message = (
            f"Hi {patient_name}, this is Dr. {patient_data.get('provider_name', 'Smith')} office. "
            f"We're looking forward to seeing you on {appointment_date} at {appointment_time}. "
            f"Please reply YES to confirm or text us if you need to reschedule."
        )
        
        result = await self.twilio.send_sms(
            to=patient_data.get("patient_phone"),
            body=message
        )
        
        return {
            "action": "confirmation_request",
            "sent": result.get("success", False),
            "message_id": result.get("message_sid")
        }
    
    async def _send_reminder(self, patient_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send appointment reminder SMS."""
        patient_name = patient_data.get("patient_name", "there")
        appointment_date = patient_data.get("appointment_date", "tomorrow")
        appointment_time = patient_data.get("appointment_time", "time")
        office_address = patient_data.get("office_address", "")
        
        message = (
            f"Reminder: You have an appointment with Dr. {patient_data.get('provider_name', 'Smith')} "
            f"on {appointment_date} at {appointment_time}. {office_address}"
        )
        
        result = await self.twilio.send_sms(
            to=patient_data.get("patient_phone"),
            body=message
        )
        
        return {
            "action": "reminder",
            "sent": result.get("success", False),
            "message_id": result.get("message_sid")
        }

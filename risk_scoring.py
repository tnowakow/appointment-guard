"""
Dental Industry - Risk Scoring Agent

Predicts no-show risk for dental appointments using historical patterns.
Future: Replace rule-based logic with XGBoost model trained on patient data.
"""

from typing import Dict, Any
from agents.base_agent import PredictorAgent, AgentInput, AgentOutput


class NoShowRiskAgent(PredictorAgent):
    """Predict no-show probability for dental appointments (0-1 scale)."""
    
    name = "NoShowRiskAgent"
    version = "1.0.0"
    
    # Risk factors and their weights (to be replaced by ML model)
    RISK_FACTORS = {
        "late_arrival_history": 0.3,      # Patient has late arrivals
        "cancellation_history": 0.4,      # Patient cancels frequently  
        "first_time_patient": 0.2,         # New patients higher risk
        "appointment_day_of_week": 0.15,   # Fridays/Sundays higher risk
        "appointment_time": 0.1,           # Early morning/late evening higher risk
        "days_until_appointment": 0.25     # Last-minute bookings higher risk
    }
    
    def __init__(self):
        super().__init__()
    
    async def predict(self, item: Dict[str, Any]) -> float:
        """
        Predict no-show probability (0-1).
        
        Args:
            item: Dictionary with patient and appointment data
            
        Returns:
            Float between 0 (low risk) and 1 (high risk)
        """
        # Extract features from item
        has_late_history = item.get("late_arrival_count", 0) > 2
        has_cancel_history = item.get("cancellation_count", 0) > 1
        is_first_time = item.get("is_first_visit", False)
        day_of_week = item.get("appointment_day", "monday").lower()
        appointment_hour = item.get("appointment_hour", 12)
        days_until = item.get("days_until_appointment", 7)
        
        # Calculate risk score using weighted factors
        risk_score = 0.0
        
        if has_late_history:
            risk_score += self.RISK_FACTORS["late_arrival_history"]
            
        if has_cancel_history:
            risk_score += self.RISK_FACTORS["cancellation_history"]
            
        if is_first_time:
            risk_score += self.RISK_FACTORS["first_time_patient"]
        
        # Day of week factor (Friday/Sunday higher risk)
        if day_of_week in ["friday", "sunday"]:
            risk_score += self.RISK_FACTORS["appointment_day_of_week"]
            
        # Time of day factor (early morning < 9am or late > 5pm)
        if appointment_hour < 9 or appointment_hour >= 17:
            risk_score += self.RISK_FACTORS["appointment_time"]
        
        # Booking timing factor (< 48 hours notice = higher risk)
        if days_until < 2:
            risk_score += self.RISK_FACTORS["days_until_appointment"] * 1.5
        elif days_until < 7:
            risk_score += self.RISK_FACTORS["days_until_appointment"]
        
        # Normalize to 0-1 range
        return min(max(risk_score, 0.0), 1.0)
    
    def get_risk_category(self, risk_score: float) -> str:
        """Convert numeric risk score to category."""
        if risk_score >= 0.7:
            return "HIGH"
        elif risk_score >= 0.4:
            return "MEDIUM"
        else:
            return "LOW"

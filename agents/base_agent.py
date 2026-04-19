"""
ZenticPro Platform - Base Agent Class
Reusable agent orchestration pattern for all industry modules.
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class AgentInput(BaseModel):
    """Base input model for all agents."""
    data: Dict[str, Any]
    context: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = {}


class AgentOutput(BaseModel):
    """Base output model for all agents."""
    success: bool
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    confidence: Optional[float] = None  # For classification/prediction agents
    reasoning: Optional[str] = None  # Explainable AI


class BaseAgent(ABC):
    """
    Abstract base class for all ZenticPro agents.
    
    Provides common functionality:
    - Input validation
    - Error handling
    - Logging
    - Output formatting
    
    Subclasses must implement:
    - process() - Core agent logic
    """
    
    name: str = "BaseAgent"
    version: str = "1.0.0"
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize agent with optional configuration."""
        self.config = config or {}
        logger.info(f"Initialized {self.name} v{self.version}")
    
    @abstractmethod
    async def process(self, input: AgentInput) -> AgentOutput:
        """
        Process input and return result.
        
        Must be implemented by subclasses.
        
        Args:
            input: AgentInput object with data and context
            
        Returns:
            AgentOutput with result or error
        """
        pass
    
    async def execute(self, data: Dict[str, Any], **kwargs) -> AgentOutput:
        """
        Convenience method to run agent with raw dictionary.
        
        Args:
            data: Raw input data
            **kwargs: Additional context/metadata
            
        Returns:
            AgentOutput with result or error
        """
        try:
            input = AgentInput(
                data=data,
                context=kwargs.get("context"),
                metadata=kwargs.get("metadata", {})
            )
            
            logger.info(f"{self.name} processing: {data.get('id', 'unknown')}")
            result = await self.process(input)
            
            if result.success:
                logger.info(f"{self.name} completed successfully")
            else:
                logger.error(f"{self.name} failed: {result.error}")
            
            return result
            
        except Exception as e:
            logger.error(f"{self.name} error: {e}")
            return AgentOutput(
                success=False,
                error=str(e)
            )


class ClassifierAgent(BaseAgent):
    """
    Base class for classification agents (triage, categorization).
    
    Extends BaseAgent with confidence scoring and multi-label support.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None, labels: Optional[List[str]] = None):
        """
        Initialize classifier agent.
        
        Args:
            config: Agent configuration
            labels: List of possible classification labels
        """
        super().__init__(config)
        self.labels = labels or []
    
    @abstractmethod
    async def classify(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """
        Classify an item into one or more categories.
        
        Must be implemented by subclasses.
        
        Args:
            item: Item to classify
            
        Returns:
            Dictionary with classification results
        """
        pass
    
    async def process(self, input: AgentInput) -> AgentOutput:
        """Override base process to handle classification."""
        try:
            result = await self.classify(input.data)
            
            return AgentOutput(
                success=True,
                result=result,
                confidence=result.get("confidence"),
                reasoning=result.get("reasoning")
            )
            
        except Exception as e:
            return AgentOutput(
                success=False,
                error=f"Classification failed: {str(e)}",
                reasoning=None
            )


class PredictorAgent(BaseAgent):
    """
    Base class for prediction agents (risk scoring, forecasting).
    
    Extends BaseAgent with numeric predictions and confidence intervals.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize predictor agent."""
        super().__init__(config)
    
    @abstractmethod
    async def predict(self, item: Dict[str, Any]) -> float:
        """
        Predict a numeric value for an item.
        
        Must be implemented by subclasses.
        
        Args:
            item: Item to predict
            
        Returns:
            Numeric prediction (e.g., risk score 0-1)
        """
        pass
    
    async def process(self, input: AgentInput) -> AgentOutput:
        """Override base process to handle predictions."""
        try:
            prediction = await self.predict(input.data)
            
            return AgentOutput(
                success=True,
                result={"prediction": prediction},
                confidence=prediction  # For risk scores, value = confidence
            )
            
        except Exception as e:
            return AgentOutput(
                success=False,
                error=f"Prediction failed: {str(e)}"
            )

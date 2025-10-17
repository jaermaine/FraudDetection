from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import joblib
import numpy as np
import pandas as pd
from typing import List

# Initialize FastAPI app
app = FastAPI(title="Fraud Detection API")

# Enable CORS for your frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize transaction counter
transaction_counter = 0

# Load or create the model
model_path = 'models/fraud_detection_model.pkl'
try:
    model = joblib.load(model_path)
    print("Model loaded successfully!")
except Exception as e:
    print(f"Error loading model: {e}")
    model = None

# Define input schema (adjust fields based on your actual features)
class FraudInput(BaseModel):
    type: str
    amount: float
    oldbalanceOrg: float
    newbalanceOrig: float
    oldbalanceDest: float
    newbalanceDest: float
    isFlaggedFraud: int = 0

class PredictionResponse(BaseModel):
    is_fraud: bool
    fraud_probability: float
    confidence: str
    
def preprocess_transaction(data: dict, step: int):
    """Convert transaction data to model input format with one-hot encoding"""
    
    # Define all possible transaction types
    transaction_types = ['CASH_OUT', 'DEBIT', 'PAYMENT', 'TRANSFER']
    
    # Create base features
    features = {
        'step': step,
        'amount': data['amount'],
        'oldbalanceOrg': data['oldbalanceOrg'],
        'newbalanceOrig': data['newbalanceOrig'],
        'oldbalanceDest': data['oldbalanceDest'],
        'newbalanceDest': data['newbalanceDest'],
        'isFlaggedFraud': data.get('isFlaggedFraud', 0)  # Default to 0 if not provided
    }
    
    # One-hot encode the transaction type
    # Note: CASH_IN is the reference category (all 0s)
    for t_type in transaction_types:
        features[f'type_{t_type}'] = 1 if data['type'] == t_type else 0
    
    # Create DataFrame with correct column order (as expected by model)
    feature_order = [
        'step', 'amount', 'oldbalanceOrg', 'newbalanceOrig',
        'oldbalanceDest', 'newbalanceDest', 'isFlaggedFraud',
        'type_CASH_OUT', 'type_DEBIT', 'type_PAYMENT', 'type_TRANSFER'
    ]
    
    return pd.DataFrame([features])[feature_order]

@app.get("/")
def read_root():
    return {
        "message": "Fraud Detection API",
        "status": "running",
        "required_fields": [
            "type", "amount", "oldbalanceOrg",
            "newbalanceOrig", "oldbalanceDest", "newbalanceDest"
        ],
        "optional_fields": ["isFlaggedFraud (defaults to 0)"],
        "valid_types": ["CASH_OUT", "DEBIT", "PAYMENT", "TRANSFER"]
    }

@app.post("/predict", response_model=PredictionResponse)
def predict_fraud(data: FraudInput):
    global transaction_counter
    
    try:
        # Validate transaction type
        valid_types = ['CASH_OUT', 'DEBIT', 'PAYMENT', 'TRANSFER']
        if data.type not in valid_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid transaction type. Must be one of: {valid_types}"
            )
        
        # Increment the transaction counter
        transaction_counter += 1
        
        # Preprocess input with step
        input_df = preprocess_transaction(data.dict(), transaction_counter)
        
        # Verify we have the correct number of features
        if input_df.shape[1] != model.n_features_in_:
            raise HTTPException(
                status_code=400,
                detail=f"Feature mismatch: got {input_df.shape[1]}, expected {model.n_features_in_}"
            )
        
        # Make prediction
        prediction = model.predict(input_df)[0]
        probability = model.predict_proba(input_df)[0][1]
        
        # Determine confidence
        if probability > 0.8 or probability < 0.2:
            confidence = "high"
        elif probability > 0.6 or probability < 0.4:
            confidence = "medium"
        else:
            confidence = "low"
        
        return PredictionResponse(
            is_fraud=bool(prediction),
            fraud_probability=float(probability),
            confidence=confidence
        )
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error: {str(e)}")

@app.get("/model_info")
def get_model_info():
    """Get model information"""
    return {
        "model_type": type(model).__name__,
        "n_features": model.n_features_in_,
        "feature_names": model.feature_names_in_.tolist() if hasattr(model, 'feature_names_in_') else [],
        "note": "isFlaggedFraud defaults to 0 if not provided"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
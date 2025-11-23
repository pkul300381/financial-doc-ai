"""
Anomaly detection using ML algorithms and statistical methods.
"""
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import uuid

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from prophet import Prophet
from statsmodels.tsa.seasonal import seasonal_decompose

from src.models.schemas import (
    DocumentExtraction, Anomaly, AnomalyType, MonetaryAmount
)

logger = logging.getLogger(__name__)


class AnomalyDetector:
    """ML-based anomaly detection for financial documents."""
    
    def __init__(self):
        """Initialize anomaly detector."""
        self.isolation_forest = IsolationForest(
            contamination=0.1,  # Expect 10% anomalies
            random_state=42,
            n_estimators=100
        )
        self.scaler = StandardScaler()
        self.fitted = False
    
    def extract_features(self, extractions: List[DocumentExtraction]) -> pd.DataFrame:
        """Extract numerical features from document extractions."""
        features = []
        
        for extraction in extractions:
            feature_dict = {
                'document_id': extraction.document_id,
                'processing_time': extraction.processing_time_seconds,
                'text_length': len(extraction.raw_text),
                'num_tables': len(extraction.tables),
                'num_entities': len(extraction.extracted_entities),
                'avg_confidence': np.mean([e.confidence for e in extraction.extracted_entities]) if extraction.extracted_entities else 0.0,
            }
            
            # Extract monetary amounts
            if hasattr(extraction.structured_data, 'total_amount'):
                total = extraction.structured_data.total_amount
                if total and isinstance(total, MonetaryAmount):
                    feature_dict['total_amount'] = total.amount
                else:
                    feature_dict['total_amount'] = 0.0
            else:
                feature_dict['total_amount'] = 0.0
            
            features.append(feature_dict)
        
        df = pd.DataFrame(features)
        return df
    
    def fit(self, extractions: List[DocumentExtraction]) -> None:
        """Train anomaly detector on historical data."""
        try:
            df = self.extract_features(extractions)
            
            # Select numerical features
            numerical_features = ['processing_time', 'text_length', 'num_tables', 
                                'num_entities', 'avg_confidence', 'total_amount']
            
            X = df[numerical_features].fillna(0)
            
            # Scale features
            X_scaled = self.scaler.fit_transform(X)
            
            # Train isolation forest
            self.isolation_forest.fit(X_scaled)
            self.fitted = True
            
            logger.info(f"Anomaly detector trained on {len(extractions)} documents")
        except Exception as e:
            logger.error(f"Failed to train anomaly detector: {e}")
    
    def detect_outliers(self, extractions: List[DocumentExtraction]) -> List[Anomaly]:
        """Detect outlier documents using Isolation Forest."""
        if not self.fitted:
            logger.warning("Anomaly detector not fitted. Skipping outlier detection.")
            return []
        
        try:
            df = self.extract_features(extractions)
            numerical_features = ['processing_time', 'text_length', 'num_tables', 
                                'num_entities', 'avg_confidence', 'total_amount']
            
            X = df[numerical_features].fillna(0)
            X_scaled = self.scaler.transform(X)
            
            # Predict anomalies (-1 for anomalies, 1 for normal)
            predictions = self.isolation_forest.predict(X_scaled)
            anomaly_scores = self.isolation_forest.score_samples(X_scaled)
            
            anomalies = []
            for i, (pred, score) in enumerate(zip(predictions, anomaly_scores)):
                if pred == -1:
                    # Determine severity based on score
                    severity = self._calculate_severity(score)
                    
                    anomaly = Anomaly(
                        anomaly_id=str(uuid.uuid4()),
                        document_id=df.iloc[i]['document_id'],
                        anomaly_type=AnomalyType.OUTLIER_AMOUNT,
                        severity=severity,
                        description=f"Document exhibits unusual characteristics (anomaly score: {score:.3f})",
                        confidence_score=abs(score),
                    )
                    anomalies.append(anomaly)
            
            logger.info(f"Detected {len(anomalies)} outliers out of {len(extractions)} documents")
            return anomalies
        except Exception as e:
            logger.error(f"Outlier detection failed: {e}")
            return []
    
    def detect_amount_anomalies(self, extractions: List[DocumentExtraction], threshold_std: float = 3.0) -> List[Anomaly]:
        """Detect anomalous amounts using statistical thresholds."""
        try:
            amounts = []
            doc_ids = []
            
            for extraction in extractions:
                if hasattr(extraction.structured_data, 'total_amount'):
                    total = extraction.structured_data.total_amount
                    if total and isinstance(total, MonetaryAmount):
                        amounts.append(total.amount)
                        doc_ids.append(extraction.document_id)
            
            if not amounts:
                return []
            
            amounts_array = np.array(amounts)
            mean = np.mean(amounts_array)
            std = np.std(amounts_array)
            
            anomalies = []
            for i, amount in enumerate(amounts):
                z_score = abs((amount - mean) / std) if std > 0 else 0
                
                if z_score > threshold_std:
                    severity = "critical" if z_score > 5 else "high" if z_score > 4 else "medium"
                    
                    anomaly = Anomaly(
                        anomaly_id=str(uuid.uuid4()),
                        document_id=doc_ids[i],
                        anomaly_type=AnomalyType.OUTLIER_AMOUNT,
                        severity=severity,
                        description=f"Amount ${amount:,.2f} is {z_score:.1f} standard deviations from mean ${mean:,.2f}",
                        field_name="total_amount",
                        expected_value=mean,
                        actual_value=amount,
                        confidence_score=min(z_score / 5.0, 1.0)
                    )
                    anomalies.append(anomaly)
            
            logger.info(f"Detected {len(anomalies)} amount anomalies")
            return anomalies
        except Exception as e:
            logger.error(f"Amount anomaly detection failed: {e}")
            return []
    
    def _calculate_severity(self, anomaly_score: float) -> str:
        """Calculate severity based on anomaly score."""
        abs_score = abs(anomaly_score)
        if abs_score > 0.5:
            return "critical"
        elif abs_score > 0.3:
            return "high"
        elif abs_score > 0.1:
            return "medium"
        else:
            return "low"


class TrendAnalyzer:
    """Time series trend analysis using Prophet."""
    
    def __init__(self):
        """Initialize trend analyzer."""
        self.model = None
    
    def analyze_trends(
        self, 
        extractions: List[DocumentExtraction],
        forecast_periods: int = 30
    ) -> Dict[str, Any]:
        """Analyze trends in document amounts over time using Prophet."""
        try:
            # Prepare time series data
            data = []
            for extraction in extractions:
                if hasattr(extraction.structured_data, 'total_amount'):
                    total = extraction.structured_data.total_amount
                    if total and isinstance(total, MonetaryAmount):
                        data.append({
                            'ds': extraction.metadata.upload_timestamp,
                            'y': total.amount
                        })
            
            if len(data) < 10:
                logger.warning("Insufficient data for trend analysis (need at least 10 points)")
                return {}
            
            df = pd.DataFrame(data)
            df = df.sort_values('ds')
            
            # Train Prophet model
            model = Prophet(
                daily_seasonality=False,
                weekly_seasonality=True,
                yearly_seasonality=False
            )
            model.fit(df)
            
            # Make forecast
            future = model.make_future_dataframe(periods=forecast_periods)
            forecast = model.predict(future)
            
            # Calculate trend direction
            recent_trend = forecast['trend'].iloc[-forecast_periods:].mean()
            historical_trend = forecast['trend'].iloc[:-forecast_periods].mean()
            trend_direction = "increasing" if recent_trend > historical_trend else "decreasing"
            
            # Detect trend anomalies
            anomalies = self._detect_trend_anomalies(df, forecast)
            
            result = {
                'trend_direction': trend_direction,
                'forecast': forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].tail(forecast_periods).to_dict('records'),
                'anomalies': anomalies,
                'average_amount': df['y'].mean(),
                'trend_change_pct': ((recent_trend - historical_trend) / historical_trend * 100) if historical_trend != 0 else 0
            }
            
            logger.info(f"Trend analysis complete: {trend_direction} trend detected")
            return result
        except Exception as e:
            logger.error(f"Trend analysis failed: {e}")
            return {}
    
    def _detect_trend_anomalies(self, df: pd.DataFrame, forecast: pd.DataFrame) -> List[Dict]:
        """Detect points that deviate significantly from predicted trend."""
        anomalies = []
        
        # Merge actual and predicted values
        merged = df.merge(forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']], on='ds', how='left')
        
        for _, row in merged.iterrows():
            if pd.notna(row['yhat']):
                # Check if actual is outside prediction interval
                if row['y'] < row['yhat_lower'] or row['y'] > row['yhat_upper']:
                    anomalies.append({
                        'date': row['ds'].isoformat(),
                        'actual': row['y'],
                        'predicted': row['yhat'],
                        'deviation': abs(row['y'] - row['yhat'])
                    })
        
        return anomalies


class ValidationEngine:
    """Data validation and consistency checks."""
    
    def validate_extraction(self, extraction: DocumentExtraction) -> List[Anomaly]:
        """Validate extraction data and identify issues."""
        anomalies = []
        
        # Check for missing critical fields
        if extraction.document_type.value in ['invoice', 'bank_statement']:
            missing_fields = self._check_missing_fields(extraction)
            anomalies.extend(missing_fields)
        
        # Check for duplicate detection
        # (In production, would compare against database)
        
        # Check for validation errors in structured data
        validation_errors = self._validate_structured_data(extraction)
        anomalies.extend(validation_errors)
        
        return anomalies
    
    def _check_missing_fields(self, extraction: DocumentExtraction) -> List[Anomaly]:
        """Check for missing required fields."""
        anomalies = []
        
        if extraction.document_type == "invoice":
            required_fields = ['invoice_number', 'total_amount', 'vendor_name']
            for field in required_fields:
                if not hasattr(extraction.structured_data, field) or getattr(extraction.structured_data, field) is None:
                    anomaly = Anomaly(
                        anomaly_id=str(uuid.uuid4()),
                        document_id=extraction.document_id,
                        anomaly_type=AnomalyType.MISSING_DATA,
                        severity="medium",
                        description=f"Required field '{field}' is missing",
                        field_name=field,
                        confidence_score=1.0
                    )
                    anomalies.append(anomaly)
        
        return anomalies
    
    def _validate_structured_data(self, extraction: DocumentExtraction) -> List[Anomaly]:
        """Validate structured data for logical consistency."""
        anomalies = []
        
        # Example: Check if subtotal + tax = total for invoices
        if hasattr(extraction.structured_data, 'subtotal') and hasattr(extraction.structured_data, 'total_amount'):
            # Add validation logic here
            pass
        
        return anomalies

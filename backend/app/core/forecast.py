"""Price forecasting module using quantile regression."""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from statsmodels.regression.quantile_regression import QuantReg
from sklearn.linear_model import LinearRegression
from typing import Dict, List, Tuple, Union
import logging
import statsmodels.api as sm

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PriceForecast:
    """
    Price forecasting class using quantile regression with OLS fallback.
    
    Attributes:
        min_samples (int): Minimum number of samples required for quantile regression.
        quantiles (List[float]): List of quantiles to forecast (P10, P50, P90).
    """
    
    def __init__(self, min_samples: int = 10):
        """
        Initialize the forecaster.
        
        Args:
            min_samples: Minimum number of samples required for quantile regression.
                        If fewer samples are available, falls back to OLS.
        """
        self.min_samples = min_samples
        self.quantiles = [0.1, 0.5, 0.9]  # P10, P50, P90
        
    def _prepare_data(self, prices: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """
        Prepare price data for regression.
        
        Args:
            prices: DataFrame with DateTimeIndex and 'Close' column
            
        Returns:
            Tuple of (X, y) arrays for regression
            
        Raises:
            ValueError: If data is empty or contains missing values
        """
        if len(prices) == 0:
            raise ValueError("Empty price data provided")
            
        if prices['Close'].isna().any():
            raise ValueError("Price data contains missing values")
            
        # Create time feature (days from start)
        X = np.arange(len(prices)).reshape(-1, 1)
        y = prices['Close'].values
        
        return X, y
        
    def _add_intercept(self, X):
        """Add intercept column to feature matrix."""
        return np.column_stack([np.ones(len(X)), X])

    def _fit_quantile_regression(self, X, y, quantile=0.5):
        """Fit quantile regression model."""
        model = QuantReg(y, self._add_intercept(X))
        return model.fit(q=quantile)

    def _predict_with_intercept(self, model, X):
        """Make predictions with proper intercept handling."""
        X_with_intercept = self._add_intercept(X)
        return model.predict(X_with_intercept)

    def _fallback_to_ols(self, X, y):
        """Fallback to OLS when quantile regression fails."""
        model = LinearRegression()
        model.fit(X, y)
        return model

    def create_forecast(self, price_data: pd.DataFrame, horizon_days: int = 30) -> Dict:
        """Create price forecast with confidence bands."""
        X, y = self._prepare_data(price_data)
        
        # Handle constant prices
        if np.allclose(y, y[0], rtol=1e-5):
            constant_value = y[0]
            forecast_dates = pd.date_range(
                start=price_data.index[-1] + pd.Timedelta(days=1),
                periods=horizon_days,
                freq='D'
            )
            return {
                'dates': forecast_dates.strftime('%Y-%m-%d').tolist(),
                'bands': {
                    'P10': [constant_value] * horizon_days,
                    'P50': [constant_value] * horizon_days,
                    'P90': [constant_value] * horizon_days
                }
            }

        # Create forecast features
        forecast_steps = np.arange(len(X), len(X) + horizon_days)
        forecast_features = forecast_steps.reshape(-1, 1)

        try:
            if len(price_data) < self.min_samples:
                raise ValueError("Insufficient samples for quantile regression")

            # Fit models for different quantiles
            q10_model = self._fit_quantile_regression(X, y, quantile=0.1)
            q50_model = self._fit_quantile_regression(X, y, quantile=0.5)
            q90_model = self._fit_quantile_regression(X, y, quantile=0.9)

            # Generate predictions
            p10 = self._predict_with_intercept(q10_model, forecast_features)
            p50 = self._predict_with_intercept(q50_model, forecast_features)
            p90 = self._predict_with_intercept(q90_model, forecast_features)

        except Exception as e:
            logger.warning(f"Quantile regression failed: {str(e)}. Falling back to OLS.")
            # Fallback to OLS with confidence intervals
            model = self._fallback_to_ols(X, y)
            p50 = model.predict(forecast_features)
            
            # Estimate prediction intervals
            residuals = y - model.predict(X)
            std_dev = np.std(residuals)
            p10 = p50 - 1.28 * std_dev  # Approx. 10th percentile
            p90 = p50 + 1.28 * std_dev  # Approx. 90th percentile

        # Ensure proper ordering of quantiles
        p10 = np.minimum(p10, p50)
        p90 = np.maximum(p90, p50)

        # Create forecast dates
        forecast_dates = pd.date_range(
            start=price_data.index[-1] + pd.Timedelta(days=1),
            periods=horizon_days,
            freq='D'
        )
        
        return {
            'dates': forecast_dates.strftime('%Y-%m-%d').tolist(),
            'bands': {
                'P10': p10.tolist(),
                'P50': p50.tolist(),
                'P90': p90.tolist()
            }
        }

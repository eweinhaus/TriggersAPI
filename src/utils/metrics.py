"""CloudWatch metrics helper for structured metric emission"""

import os
import time
from datetime import datetime, timezone
import boto3
from typing import Dict, List, Optional, Any
from collections import defaultdict
from src.utils.logging import get_logger

logger = get_logger(__name__)

# CloudWatch client (lazy initialization)
_cloudwatch_client = None


def _get_cloudwatch_client():
    """Get or initialize CloudWatch client."""
    global _cloudwatch_client
    if _cloudwatch_client is None:
        region = os.getenv('AWS_REGION', 'us-east-1')
        _cloudwatch_client = boto3.client('cloudwatch', region_name=region)
    return _cloudwatch_client


class CloudWatchMetrics:
    """Helper class for emitting CloudWatch metrics with batching."""
    
    def __init__(self, namespace: str = 'TriggersAPI/Production'):
        """
        Initialize CloudWatch metrics helper.
        
        Args:
            namespace: CloudWatch metric namespace
        """
        self.namespace = namespace
        self.client = _get_cloudwatch_client()
        self._latency_values: Dict[str, List[float]] = defaultdict(list)
        self._batch: List[Dict[str, Any]] = []
        self._batch_size_limit = 20  # CloudWatch limit
    
    def record_latency(
        self,
        endpoint: str,
        method: str,
        duration_ms: float,
        percentiles: List[int] = [50, 95, 99]
    ) -> None:
        """
        Record latency metric with percentiles.
        
        Args:
            endpoint: Endpoint path (e.g., '/v1/events')
            method: HTTP method (e.g., 'POST')
            duration_ms: Request duration in milliseconds
            percentiles: List of percentiles to calculate (default: [50, 95, 99])
        """
        try:
            # Store latency value for percentile calculation
            key = f"{method}:{endpoint}"
            self._latency_values[key].append(duration_ms)
            
            # Calculate percentiles if we have enough data or at batch flush
            # For now, we'll emit the raw value and calculate percentiles on CloudWatch side
            # or flush when batch is full
            
            # Emit raw latency value
            self._add_metric(
                MetricName='ApiLatency',
                Value=duration_ms,
                Unit='Milliseconds',
                Dimensions=[
                    {'Name': 'Endpoint', 'Value': endpoint},
                    {'Name': 'Method', 'Value': method},
                ]
            )
            
        except Exception as e:
            logger.warning(
                "Failed to record latency metric",
                extra={
                    'operation': 'record_latency',
                    'error': str(e),
                }
            )
    
    def record_success(self, endpoint: str, method: str) -> None:
        """
        Record successful request metric.
        
        Args:
            endpoint: Endpoint path
            method: HTTP method
        """
        try:
            self._add_metric(
                MetricName='ApiRequestCount',
                Value=1,
                Unit='Count',
                Dimensions=[
                    {'Name': 'Endpoint', 'Value': endpoint},
                    {'Name': 'Method', 'Value': method},
                    {'Name': 'Status', 'Value': 'success'},
                ]
            )
        except Exception as e:
            logger.warning(
                "Failed to record success metric",
                extra={
                    'operation': 'record_success',
                    'error': str(e),
                }
            )
    
    def record_error(self, endpoint: str, method: str, error_type: str) -> None:
        """
        Record error metric.
        
        Args:
            endpoint: Endpoint path
            method: HTTP method
            error_type: Error type (e.g., 'VALIDATION_ERROR', 'NOT_FOUND')
        """
        try:
            self._add_metric(
                MetricName='ApiErrorRate',
                Value=1,
                Unit='Count',
                Dimensions=[
                    {'Name': 'Endpoint', 'Value': endpoint},
                    {'Name': 'Method', 'Value': method},
                    {'Name': 'ErrorType', 'Value': error_type},
                ]
            )
            
            # Also record as failed request
            self._add_metric(
                MetricName='ApiRequestCount',
                Value=1,
                Unit='Count',
                Dimensions=[
                    {'Name': 'Endpoint', 'Value': endpoint},
                    {'Name': 'Method', 'Value': method},
                    {'Name': 'Status', 'Value': 'error'},
                ]
            )
        except Exception as e:
            logger.warning(
                "Failed to record error metric",
                extra={
                    'operation': 'record_error',
                    'error': str(e),
                }
            )
    
    def record_request_count(self, endpoint: str, method: str) -> None:
        """
        Record request count metric.
        
        Args:
            endpoint: Endpoint path
            method: HTTP method
        """
        try:
            self._add_metric(
                MetricName='ApiRequestCount',
                Value=1,
                Unit='Count',
                Dimensions=[
                    {'Name': 'Endpoint', 'Value': endpoint},
                    {'Name': 'Method', 'Value': method},
                ]
            )
        except Exception as e:
            logger.warning(
                "Failed to record request count metric",
                extra={
                    'operation': 'record_request_count',
                    'error': str(e),
                }
            )
    
    def record_event_ingestion_rate(self, events_per_second: float) -> None:
        """
        Record event ingestion rate.
        
        Args:
            events_per_second: Events per second
        """
        try:
            self._add_metric(
                MetricName='EventIngestionRate',
                Value=events_per_second,
                Unit='Count/Second',
                Dimensions=[]
            )
        except Exception as e:
            logger.warning(
                "Failed to record event ingestion rate",
                extra={
                    'operation': 'record_event_ingestion_rate',
                    'error': str(e),
                }
            )
    
    def _add_metric(
        self,
        MetricName: str,
        Value: float,
        Unit: str,
        Dimensions: List[Dict[str, str]]
    ) -> None:
        """
        Add metric to batch.
        
        Args:
            MetricName: CloudWatch metric name
            Value: Metric value
            Unit: Metric unit (e.g., 'Count', 'Milliseconds')
            Dimensions: Metric dimensions
        """
        metric_data = {
            'MetricName': MetricName,
            'Value': Value,
            'Unit': Unit,
            'Dimensions': Dimensions,
            'Timestamp': datetime.now(timezone.utc),
        }
        
        self._batch.append(metric_data)
        
        # Flush if batch is full
        if len(self._batch) >= self._batch_size_limit:
            self.flush()
    
    def flush(self) -> None:
        """Flush batched metrics to CloudWatch."""
        if not self._batch:
            return
        
        try:
            # CloudWatch PutMetricData accepts up to 20 metrics per call
            # Split batch into chunks of 20
            chunk_size = 20
            for i in range(0, len(self._batch), chunk_size):
                chunk = self._batch[i:i + chunk_size]
                
                # Convert timestamps to datetime objects
                for metric in chunk:
                    if 'Timestamp' in metric:
                        metric['Timestamp'] = datetime.fromtimestamp(
                            metric['Timestamp'], tz=timezone.utc
                        )
                
                self.client.put_metric_data(
                    Namespace=self.namespace,
                    MetricData=chunk
                )
            
            self._batch.clear()
            
        except Exception as e:
            logger.error(
                "Failed to flush metrics to CloudWatch",
                extra={
                    'operation': 'flush_metrics',
                    'error': str(e),
                    'error_type': type(e).__name__,
                    'batch_size': len(self._batch),
                }
            )
            # Clear batch on error to prevent memory buildup
            self._batch.clear()


# Global metrics instance
_metrics_instance: Optional[CloudWatchMetrics] = None


def get_metrics() -> CloudWatchMetrics:
    """
    Get global CloudWatch metrics instance.
    
    Returns:
        CloudWatchMetrics instance
    """
    global _metrics_instance
    if _metrics_instance is None:
        namespace = os.getenv('CLOUDWATCH_NAMESPACE', 'TriggersAPI/Production')
        _metrics_instance = CloudWatchMetrics(namespace=namespace)
    return _metrics_instance


# Convenience functions
def record_latency(endpoint: str, method: str, duration_ms: float) -> None:
    """Record latency metric."""
    get_metrics().record_latency(endpoint, method, duration_ms)


def record_success(endpoint: str, method: str) -> None:
    """Record success metric."""
    get_metrics().record_success(endpoint, method)


def record_error(endpoint: str, method: str, error_type: str) -> None:
    """Record error metric."""
    get_metrics().record_error(endpoint, method, error_type)


def record_request_count(endpoint: str, method: str) -> None:
    """Record request count metric."""
    get_metrics().record_request_count(endpoint, method)


def record_event_ingestion_rate(events_per_second: float) -> None:
    """Record event ingestion rate."""
    get_metrics().record_event_ingestion_rate(events_per_second)


def flush_metrics() -> None:
    """Flush all pending metrics to CloudWatch."""
    get_metrics().flush()


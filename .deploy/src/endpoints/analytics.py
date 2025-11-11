"""Analytics endpoints: get metrics, summary, export"""

from fastapi import APIRouter, Request, Depends, Query, Response
from typing import Optional
from datetime import datetime, timedelta, timezone
import csv
import io
import json
from src.database import _get_analytics_table
from src.auth import get_api_key
from src.exceptions import ValidationError, InternalError
from src.utils.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.get(
    "/analytics",
    status_code=200,
    tags=["analytics"],
    summary="Get analytics data",
    description="""
    Get aggregated analytics data for a date range.
    
    **Metrics:**
    - Event volume (by hour/day)
    - Source distribution
    - Event type distribution
    - Error rates (if available)
    
    **Date Range:**
    - Default: Last 7 days
    - Maximum: 30 days
    """,
    responses={
        200: {"description": "Analytics data"},
        400: {"description": "Invalid date range"},
        401: {"description": "Unauthorized"}
    }
)
async def get_analytics_endpoint(
    request: Request,
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    metric_type: str = Query("daily", regex="^(hourly|daily)$", description="Metric type"),
    authenticated_api_key: str = Depends(get_api_key)
):
    """Get analytics data."""
    try:
        # Default to last 7 days if not provided
        if not start_date or not end_date:
            end = datetime.now(timezone.utc)
            start = end - timedelta(days=7)
            start_date = start.strftime('%Y-%m-%d')
            end_date = end.strftime('%Y-%m-%d')
        
        # Validate date format
        try:
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        except ValueError:
            raise ValidationError("Invalid date format. Use YYYY-MM-DD")
        
        if start_dt > end_dt:
            raise ValidationError("start_date must be before or equal to end_date")
        
        if (end_dt - start_dt).days > 30:
            raise ValidationError("Date range cannot exceed 30 days")
        
        # Query analytics table
        table = _get_analytics_table()
        metrics = []
        
        current_date = start_dt
        while current_date <= end_dt:
            date_str = current_date.strftime('%Y-%m-%d')
            
            if metric_type == 'hourly':
                # Query all hourly metrics for this date
                for hour in range(24):
                    metric_key = f'hourly-{hour:02d}'
                    try:
                        response = table.get_item(
                            Key={
                                'metric_date': date_str,
                                'metric_type': metric_key
                            }
                        )
                        if 'Item' in response:
                            item = response['Item']
                            metrics.append({
                                'date': date_str,
                                'hour': hour,
                                'event_count': item.get('event_count', 0),
                                'source_distribution': item.get('source_distribution', {}),
                                'event_type_distribution': item.get('event_type_distribution', {})
                            })
                    except Exception as e:
                        logger.warning(f"Error getting hourly metric: {e}")
            else:
                # Daily metric
                try:
                    response = table.get_item(
                        Key={
                            'metric_date': date_str,
                            'metric_type': 'daily'
                        }
                    )
                    if 'Item' in response:
                        item = response['Item']
                        metrics.append({
                            'date': date_str,
                            'event_count': item.get('event_count', 0),
                            'source_distribution': item.get('source_distribution', {}),
                            'event_type_distribution': item.get('event_type_distribution', {})
                        })
                except Exception as e:
                    logger.warning(f"Error getting daily metric: {e}")
            
            current_date += timedelta(days=1)
        
        return {
            "metrics": metrics,
            "start_date": start_date,
            "end_date": end_date,
            "metric_type": metric_type,
            "request_id": request.state.request_id
        }
    except ValidationError:
        raise
    except Exception as e:
        raise InternalError(
            message="Failed to get analytics",
            details={"error": str(e)},
            request_id=request.state.request_id
        )


@router.get(
    "/analytics/summary",
    status_code=200,
    tags=["analytics"],
    summary="Get analytics summary",
    description="""
    Get summary statistics for a date range.
    
    **Summary Includes:**
    - Total events
    - Top sources
    - Top event types
    - Error rate (if available)
    """,
    responses={
        200: {"description": "Analytics summary"},
        400: {"description": "Invalid date range"},
        401: {"description": "Unauthorized"}
    }
)
async def get_analytics_summary_endpoint(
    request: Request,
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    authenticated_api_key: str = Depends(get_api_key)
):
    """Get analytics summary."""
    try:
        # Default to last 7 days
        if not start_date or not end_date:
            end = datetime.now(timezone.utc)
            start = end - timedelta(days=7)
            start_date = start.strftime('%Y-%m-%d')
            end_date = end.strftime('%Y-%m-%d')
        
        # Validate dates
        try:
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        except ValueError:
            raise ValidationError("Invalid date format. Use YYYY-MM-DD")
        
        if start_dt > end_dt:
            raise ValidationError("start_date must be before or equal to end_date")
        
        # Query and aggregate
        table = _get_analytics_table()
        total_events = 0
        source_counts = {}
        event_type_counts = {}
        
        current_date = start_dt
        while current_date <= end_dt:
            date_str = current_date.strftime('%Y-%m-%d')
            
            try:
                response = table.get_item(
                    Key={
                        'metric_date': date_str,
                        'metric_type': 'daily'
                    }
                )
                if 'Item' in response:
                    item = response['Item']
                    total_events += item.get('event_count', 0)
                    
                    # Aggregate source distribution
                    source_dist = item.get('source_distribution', {})
                    for source, count in source_dist.items():
                        source_counts[source] = source_counts.get(source, 0) + count
                    
                    # Aggregate event type distribution
                    event_type_dist = item.get('event_type_distribution', {})
                    for event_type, count in event_type_dist.items():
                        event_type_counts[event_type] = event_type_counts.get(event_type, 0) + count
            except Exception as e:
                logger.warning(f"Error getting daily metric: {e}")
            
            current_date += timedelta(days=1)
        
        # Get top sources and event types
        top_sources = sorted(source_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        top_event_types = sorted(event_type_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return {
            "total_events": total_events,
            "top_sources": [{"source": s, "count": c} for s, c in top_sources],
            "top_event_types": [{"event_type": e, "count": c} for e, c in top_event_types],
            "start_date": start_date,
            "end_date": end_date,
            "request_id": request.state.request_id
        }
    except ValidationError:
        raise
    except Exception as e:
        raise InternalError(
            message="Failed to get analytics summary",
            details={"error": str(e)},
            request_id=request.state.request_id
        )


@router.get(
    "/analytics/export",
    status_code=200,
    tags=["analytics"],
    summary="Export analytics data",
    description="""
    Export analytics data as CSV or JSON.
    
    **Formats:**
    - CSV: Comma-separated values
    - JSON: JSON array
    
    **Date Range:**
    - Default: Last 7 days
    - Maximum: 30 days
    """,
    responses={
        200: {"description": "Exported analytics data"},
        400: {"description": "Invalid date range or format"},
        401: {"description": "Unauthorized"}
    }
)
async def export_analytics_endpoint(
    request: Request,
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    format: str = Query("json", regex="^(csv|json)$", description="Export format"),
    metric_type: str = Query("daily", regex="^(hourly|daily)$", description="Metric type"),
    authenticated_api_key: str = Depends(get_api_key)
):
    """Export analytics data."""
    try:
        # Get analytics data (reuse get_analytics logic)
        # For simplicity, call the same logic
        if not start_date or not end_date:
            end = datetime.now(timezone.utc)
            start = end - timedelta(days=7)
            start_date = start.strftime('%Y-%m-%d')
            end_date = end.strftime('%Y-%m-%d')
        
        # Validate dates
        try:
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        except ValueError:
            raise ValidationError("Invalid date format. Use YYYY-MM-DD")
        
        if start_dt > end_dt:
            raise ValidationError("start_date must be before or equal to end_date")
        
        # Query analytics (simplified - reuse get_analytics logic)
        table = _get_analytics_table()
        metrics = []
        
        current_date = start_dt
        while current_date <= end_dt:
            date_str = current_date.strftime('%Y-%m-%d')
            
            try:
                response = table.get_item(
                    Key={
                        'metric_date': date_str,
                        'metric_type': 'daily' if metric_type == 'daily' else 'hourly-00'
                    }
                )
                if 'Item' in response:
                    item = response['Item']
                    metrics.append({
                        'date': date_str,
                        'event_count': item.get('event_count', 0),
                        'source_distribution': item.get('source_distribution', {}),
                        'event_type_distribution': item.get('event_type_distribution', {})
                    })
            except Exception:
                pass
            
            current_date += timedelta(days=1)
        
        # Format response
        if format == 'csv':
            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=['date', 'event_count', 'sources', 'event_types'])
            writer.writeheader()
            for metric in metrics:
                writer.writerow({
                    'date': metric['date'],
                    'event_count': metric['event_count'],
                    'sources': json.dumps(metric.get('source_distribution', {})),
                    'event_types': json.dumps(metric.get('event_type_distribution', {}))
                })
            
            return Response(
                content=output.getvalue(),
                media_type='text/csv',
                headers={
                    'Content-Disposition': f'attachment; filename="analytics-{start_date}-to-{end_date}.csv"'
                }
            )
        else:
            return {
                "metrics": metrics,
                "start_date": start_date,
                "end_date": end_date,
                "format": format,
                "request_id": request.state.request_id
            }
    except ValidationError:
        raise
    except Exception as e:
        raise InternalError(
            message="Failed to export analytics",
            details={"error": str(e)},
            request_id=request.state.request_id
        )


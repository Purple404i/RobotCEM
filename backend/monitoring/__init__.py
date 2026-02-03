"""
Monitoring Module - Metrics and observability

Includes:
- Prometheus metrics
- Performance monitoring
- Health checks
"""

try:
    from .metrics import MetricsCollector
except ImportError as e:
    import warnings
    warnings.warn(f"Could not import monitoring modules: {e}", ImportWarning)

__all__ = [
    "MetricsCollector",
]

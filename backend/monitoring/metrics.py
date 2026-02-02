from prometheus_client import Counter, Histogram, Gauge
import time

# Metrics
designs_generated = Counter(
    'designs_generated_total',
    'Total number of designs generated',
    ['device_type', 'status']
)

generation_duration = Histogram(
    'design_generation_duration_seconds',
    'Time taken to generate design',
    buckets=[10, 30, 60, 120, 300, 600]
)

active_jobs = Gauge(
    'active_jobs',
    'Number of currently active jobs'
)

component_cache_hits = Counter(
    'component_cache_hits_total',
    'Number of component cache hits'
)

stl_file_size = Histogram(
    'stl_file_size_bytes',
    'Size of generated STL files',
    buckets=[1024*10, 1024*100, 1024*1024, 1024*1024*10]
)

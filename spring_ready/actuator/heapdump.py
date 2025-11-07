"""
Actuator Heapdump Endpoint.
Provides memory snapshot/profiling data (Python adaptation of Java heap dump).
"""

import sys
import gc
import tracemalloc
from typing import Dict, Any


class HeapdumpEndpoint:
    """
    Heapdump endpoint for Spring Boot Actuator compatibility.

    Python adaptation: Returns memory statistics and profiling data
    instead of binary heap dump (which is Java-specific).
    """

    def get_memory_stats(self) -> Dict[str, Any]:
        """
        Get memory statistics (JSON format, not binary dump).

        Returns:
            Dictionary with memory usage statistics
        """
        # Force garbage collection for accurate stats
        gc.collect()

        # Get GC stats
        gc_stats = {
            "collections": gc.get_count(),
            "threshold": gc.get_threshold(),
            "objects": len(gc.get_objects())
        }

        # Get system memory info
        import resource
        rusage = resource.getrusage(resource.RUSAGE_SELF)

        memory_stats = {
            "gc": gc_stats,
            "memory": {
                "maxrss": rusage.ru_maxrss,  # Maximum resident set size
                "ixrss": rusage.ru_ixrss,  # Integral shared memory size
                "idrss": rusage.ru_idrss,  # Integral unshared data size
                "isrss": rusage.ru_isrss  # Integral unshared stack size
            },
            "python": {
                "version": sys.version.split()[0],
                "implementation": sys.implementation.name,
                "refcount": sys.gettotalrefcount() if hasattr(sys, 'gettotalrefcount') else "N/A"
            }
        }

        # Add tracemalloc stats if available
        if tracemalloc.is_tracing():
            current, peak = tracemalloc.get_traced_memory()
            memory_stats["tracemalloc"] = {
                "current": current,
                "peak": peak,
                "tracing": True
            }
        else:
            memory_stats["tracemalloc"] = {
                "tracing": False,
                "note": "Call tracemalloc.start() to enable detailed memory tracing"
            }

        return memory_stats


def create_default_heapdump_endpoint() -> HeapdumpEndpoint:
    """
    Create heapdump endpoint with default configuration.

    Returns:
        HeapdumpEndpoint instance
    """
    return HeapdumpEndpoint()

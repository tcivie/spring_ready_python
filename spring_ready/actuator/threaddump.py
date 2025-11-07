"""
Actuator Thread Dump Endpoint.
Shows information about all running threads.
"""

import threading
import sys
import traceback
from typing import Dict, Any, List


class ThreadDumpEndpoint:
    """
    Thread dump endpoint for Spring Boot Actuator compatibility.

    Shows information about all running threads (Python equivalent of Java thread dump).
    Note: Python has the GIL (Global Interpreter Lock), so threading behavior
    differs from Java/JVM.
    """

    def __init__(self):
        """Initialize thread dump endpoint"""
        pass

    def _get_thread_state(self, thread: threading.Thread) -> str:
        """
        Get thread state as a string.

        Args:
            thread: Thread instance

        Returns:
            State string (RUNNABLE, WAITING, TIMED_WAITING, TERMINATED)
        """
        if thread.is_alive():
            return "RUNNABLE"
        return "TERMINATED"

    def _get_stack_trace(self, thread_id: int) -> List[Dict[str, Any]]:
        """
        Get stack trace for a thread.

        Args:
            thread_id: Thread identifier

        Returns:
            List of stack frame dictionaries
        """
        frames = []

        # Get all stack frames
        try:
            frame = sys._current_frames().get(thread_id)
            if frame:
                # Extract stack frames
                stack = traceback.extract_stack(frame)
                for frame_summary in stack:
                    frames.append({
                        "methodName": frame_summary.name,
                        "fileName": frame_summary.filename,
                        "lineNumber": frame_summary.lineno,
                        "className": "",  # Python doesn't have classes in stack frames like Java
                        "nativeMethod": False
                    })
        except:
            pass  # If we can't get the stack, return empty list

        return frames

    def _get_thread_info(self, thread: threading.Thread) -> Dict[str, Any]:
        """
        Get detailed information about a thread.

        Args:
            thread: Thread instance

        Returns:
            Thread information dictionary
        """
        thread_id = thread.ident or 0

        return {
            "threadName": thread.name,
            "threadId": thread_id,
            "daemon": thread.daemon,
            "suspended": False,
            "threadState": self._get_thread_state(thread),
            "stackTrace": self._get_stack_trace(thread_id) if thread.is_alive() else []
        }

    def get_thread_dump(self) -> Dict[str, Any]:
        """
        Get thread dump with all running threads.

        Returns:
            Dictionary with threads list
        """
        threads = []

        # Get all threads
        for thread in threading.enumerate():
            threads.append(self._get_thread_info(thread))

        return {
            "threads": threads
        }


def create_default_threaddump_endpoint() -> ThreadDumpEndpoint:
    """
    Create thread dump endpoint.

    Returns:
        ThreadDumpEndpoint instance
    """
    return ThreadDumpEndpoint()

"""Alarm runner that executes run_alarm.py as a subprocess."""
import subprocess
import os
import time
import threading
from typing import Callable
from config import config
from utils.logger import logger
from utils.process_lock import ProcessLock


class AlarmRunner:
    """Manages execution of run_alarm.py alarm script."""

    def __init__(self, on_triggered: Callable, on_completed: Callable):
        """
        Initialize alarm runner.

        Args:
            on_triggered: Callback when alarm starts (receives alarm_id)
            on_completed: Callback when alarm completes (receives alarm_id, status, error)
        """
        self.on_triggered = on_triggered
        self.on_completed = on_completed
        self.alarm_script_path = os.path.join(config.CV_ALARM_ROOT, config.RUN_ALARM_SCRIPT)

    def run_alarm(self, alarm_id: int):
        """
        Trigger alarm execution in a background thread.

        Args:
            alarm_id: Alarm ID
        """
        # Run in background thread to avoid blocking scheduler
        thread = threading.Thread(target=self._execute_alarm, args=(alarm_id,))
        thread.daemon = True
        thread.start()

    def _execute_alarm(self, alarm_id: int):
        """
        Execute the alarm script.

        Args:
            alarm_id: Alarm ID
        """
        logger.info(f"Alarm {alarm_id} triggered, attempting to run alarm script...")

        # Try to acquire process lock
        lock = ProcessLock()
        if not lock.acquire(timeout=0):
            error_msg = "Another alarm is already running"
            logger.warning(f"Alarm {alarm_id}: {error_msg}")
            self.on_completed(alarm_id, "failed", error_msg)
            return

        try:
            # Check if alarm script exists
            if not os.path.exists(self.alarm_script_path):
                error_msg = f"Alarm script not found: {self.alarm_script_path}"
                logger.error(f"Alarm {alarm_id}: {error_msg}")
                self.on_completed(alarm_id, "failed", error_msg)
                return

            # Check if model file exists
            model_path = os.path.join(config.CV_ALARM_ROOT, config.MODEL_PATH)
            if not os.path.exists(model_path):
                error_msg = f"Model file not found: {model_path}"
                logger.error(f"Alarm {alarm_id}: {error_msg}")
                self.on_completed(alarm_id, "failed", error_msg)
                return

            # Notify that alarm is starting
            self.on_triggered(alarm_id)
            logger.info(f"Alarm {alarm_id}: Starting run_alarm.py...")

            # Execute alarm script
            try:
                process = subprocess.Popen(
                    ["python", config.RUN_ALARM_SCRIPT],
                    cwd=config.CV_ALARM_ROOT,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )

                # Wait for process to complete (with timeout)
                try:
                    stdout, stderr = process.communicate(timeout=config.MAX_ALARM_DURATION)
                    exit_code = process.returncode

                    if exit_code == 0:
                        logger.info(f"Alarm {alarm_id}: Completed successfully")
                        self.on_completed(alarm_id, "completed", None)
                    else:
                        error_msg = f"Alarm script exited with code {exit_code}"
                        if stderr:
                            error_msg += f": {stderr.decode()[:200]}"
                        logger.error(f"Alarm {alarm_id}: {error_msg}")
                        self.on_completed(alarm_id, "failed", error_msg)

                except subprocess.TimeoutExpired:
                    # Process exceeded max duration, kill it
                    logger.warning(f"Alarm {alarm_id}: Exceeded max duration, terminating...")
                    process.kill()
                    process.communicate()  # Clean up
                    error_msg = f"Alarm exceeded maximum duration ({config.MAX_ALARM_DURATION}s)"
                    self.on_completed(alarm_id, "stopped_early", error_msg)

            except FileNotFoundError:
                error_msg = "Python interpreter not found"
                logger.error(f"Alarm {alarm_id}: {error_msg}")
                self.on_completed(alarm_id, "failed", error_msg)

            except Exception as e:
                error_msg = f"Unexpected error: {str(e)}"
                logger.error(f"Alarm {alarm_id}: {error_msg}")
                self.on_completed(alarm_id, "failed", error_msg)

        finally:
            # Always release the lock
            lock.release()

    def check_prerequisites(self) -> tuple[bool, str]:
        """
        Check if alarm can be run (script and model exist).

        Returns:
            Tuple of (success, error_message)
        """
        if not os.path.exists(self.alarm_script_path):
            return False, f"Alarm script not found: {self.alarm_script_path}"

        model_path = os.path.join(config.CV_ALARM_ROOT, config.MODEL_PATH)
        if not os.path.exists(model_path):
            return False, f"Model file not found: {model_path}"

        return True, ""

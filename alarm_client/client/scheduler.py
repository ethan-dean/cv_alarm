"""Alarm scheduler using APScheduler."""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.jobstores.base import JobLookupError
import pytz
from config import config
from utils.logger import logger
from typing import Dict, List, Callable


class AlarmScheduler:
    """Manages alarm scheduling using APScheduler."""

    def __init__(self, alarm_callback: Callable):
        """
        Initialize the alarm scheduler.

        Args:
            alarm_callback: Function to call when alarm fires (receives alarm_id)
        """
        self.scheduler = BackgroundScheduler(timezone=pytz.timezone(config.TIMEZONE))
        self.alarm_callback = alarm_callback
        self.alarms: Dict[int, dict] = {}  # Store alarm configurations

    def start(self):
        """Start the scheduler."""
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info(f"Scheduler started with timezone: {config.TIMEZONE}")

    def shutdown(self):
        """Shutdown the scheduler."""
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)
            logger.info("Scheduler shutdown")

    def add_alarm(self, alarm_id: int, time: str, repeat_days: List[int], enabled: bool):
        """
        Add or update an alarm.

        Args:
            alarm_id: Alarm ID
            time: Time in HH:MM format
            repeat_days: List of day indices (0=Monday, 6=Sunday)
            enabled: Whether alarm is enabled
        """
        # Store alarm configuration
        self.alarms[alarm_id] = {
            "id": alarm_id,
            "time": time,
            "repeat_days": repeat_days,
            "enabled": enabled
        }

        # Remove existing job if it exists
        self.remove_alarm(alarm_id)

        # Only schedule if enabled
        if not enabled:
            logger.info(f"Alarm {alarm_id} is disabled, not scheduling")
            return

        # Parse time
        try:
            hour, minute = map(int, time.split(":"))
        except ValueError:
            logger.error(f"Invalid time format for alarm {alarm_id}: {time}")
            return

        # Create cron trigger
        if repeat_days:
            # Recurring alarm
            day_of_week = ",".join(str(d) for d in sorted(repeat_days))
            trigger = CronTrigger(
                day_of_week=day_of_week,
                hour=hour,
                minute=minute,
                timezone=pytz.timezone(config.TIMEZONE)
            )
            logger.info(f"Scheduling recurring alarm {alarm_id} at {time} on days {repeat_days}")
        else:
            # One-time alarm (TODO: implement using DateTrigger for next occurrence)
            # For now, we'll skip one-time alarms
            logger.warning(f"One-time alarms not yet implemented, skipping alarm {alarm_id}")
            return

        # Add job to scheduler
        try:
            self.scheduler.add_job(
                func=self.alarm_callback,
                trigger=trigger,
                id=f"alarm_{alarm_id}",
                args=[alarm_id],
                replace_existing=True,
                misfire_grace_time=60  # Allow up to 1 minute late execution
            )
            logger.info(f"Alarm {alarm_id} scheduled successfully")
        except Exception as e:
            logger.error(f"Failed to schedule alarm {alarm_id}: {e}")

    def remove_alarm(self, alarm_id: int):
        """
        Remove an alarm from the scheduler.

        Args:
            alarm_id: Alarm ID
        """
        job_id = f"alarm_{alarm_id}"
        try:
            self.scheduler.remove_job(job_id)
            logger.info(f"Removed alarm {alarm_id} from scheduler")
        except JobLookupError:
            # Job doesn't exist, which is fine
            pass

        # Remove from stored alarms
        if alarm_id in self.alarms:
            del self.alarms[alarm_id]

    def update_alarm(self, alarm_id: int, time: str, repeat_days: List[int], enabled: bool):
        """
        Update an existing alarm.

        Args:
            alarm_id: Alarm ID
            time: Time in HH:MM format
            repeat_days: List of day indices
            enabled: Whether alarm is enabled
        """
        # Simply call add_alarm which handles updates
        self.add_alarm(alarm_id, time, repeat_days, enabled)

    def clear_all_alarms(self):
        """Remove all alarms from the scheduler."""
        alarm_ids = list(self.alarms.keys())
        for alarm_id in alarm_ids:
            self.remove_alarm(alarm_id)
        logger.info("Cleared all alarms from scheduler")

    def get_scheduled_alarms(self) -> List[dict]:
        """
        Get list of currently scheduled alarms.

        Returns:
            List of alarm configurations
        """
        return list(self.alarms.values())

    def get_next_run_time(self, alarm_id: int) -> str | None:
        """
        Get the next run time for an alarm.

        Args:
            alarm_id: Alarm ID

        Returns:
            Next run time as string, or None if not scheduled
        """
        job_id = f"alarm_{alarm_id}"
        try:
            job = self.scheduler.get_job(job_id)
            if job and job.next_run_time:
                return job.next_run_time.isoformat()
        except JobLookupError:
            pass
        return None

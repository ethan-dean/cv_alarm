"""Process locking to ensure only one alarm runs at a time."""
import os
import time
from config import config
from utils.logger import logger


class ProcessLock:
    """File-based process lock to prevent concurrent alarm execution."""

    def __init__(self, lock_file_path: str = None):
        """
        Initialize process lock.

        Args:
            lock_file_path: Path to lock file
        """
        self.lock_file_path = lock_file_path or config.LOCK_FILE_PATH
        self.lock_acquired = False

    def acquire(self, timeout: int = 0) -> bool:
        """
        Acquire the process lock.

        Args:
            timeout: Maximum time to wait for lock (seconds), 0 = no wait

        Returns:
            True if lock acquired, False otherwise
        """
        start_time = time.time()

        while True:
            # Check if lock file exists
            if os.path.exists(self.lock_file_path):
                # Check if lock is stale (older than MAX_ALARM_DURATION)
                lock_age = time.time() - os.path.getmtime(self.lock_file_path)
                if lock_age > config.MAX_ALARM_DURATION:
                    logger.warning(f"Stale lock file detected (age: {lock_age:.0f}s). Removing...")
                    try:
                        os.remove(self.lock_file_path)
                    except OSError as e:
                        logger.error(f"Failed to remove stale lock: {e}")
                        return False
                else:
                    # Lock is held by another process
                    if timeout == 0:
                        logger.info("Lock is held by another process")
                        return False

                    # Wait and retry
                    elapsed = time.time() - start_time
                    if elapsed >= timeout:
                        logger.warning(f"Timeout waiting for lock ({timeout}s)")
                        return False

                    time.sleep(1)
                    continue

            # Create lock file
            try:
                # Use exclusive creation (fails if file exists)
                fd = os.open(self.lock_file_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                os.write(fd, str(os.getpid()).encode())
                os.close(fd)
                self.lock_acquired = True
                logger.info(f"Process lock acquired: {self.lock_file_path}")
                return True
            except FileExistsError:
                # Lock was created between check and creation (race condition)
                if timeout == 0:
                    return False
                continue
            except OSError as e:
                logger.error(f"Failed to create lock file: {e}")
                return False

    def release(self):
        """Release the process lock."""
        if self.lock_acquired and os.path.exists(self.lock_file_path):
            try:
                os.remove(self.lock_file_path)
                self.lock_acquired = False
                logger.info(f"Process lock released: {self.lock_file_path}")
            except OSError as e:
                logger.error(f"Failed to remove lock file: {e}")

    def is_locked(self) -> bool:
        """
        Check if the lock is currently held.

        Returns:
            True if lock exists and is not stale, False otherwise
        """
        if not os.path.exists(self.lock_file_path):
            return False

        # Check if lock is stale
        lock_age = time.time() - os.path.getmtime(self.lock_file_path)
        return lock_age <= config.MAX_ALARM_DURATION

    def __enter__(self):
        """Context manager entry."""
        if not self.acquire():
            raise RuntimeError("Failed to acquire process lock")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.release()

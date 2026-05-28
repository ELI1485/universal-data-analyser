"""Scheduler service for periodic background tasks.

Uses APScheduler to manage scheduled jobs such as periodic analysis,
report generation, and system cleanup tasks.
"""

import logging
from datetime import datetime
from typing import Callable, Optional

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

logger = logging.getLogger(__name__)


class SchedulerService:
    """Service managing background scheduled tasks.

    Provides an interface to add, remove, and manage periodic tasks
    using APScheduler's BackgroundScheduler.
    """

    def __init__(self) -> None:
        """Initialize the scheduler service."""
        self._scheduler = BackgroundScheduler(
            job_defaults={"coalesce": True, "max_instances": 1}
        )
        self._is_running = False
        logger.info("Service de planification initialisé.")

    def start(self) -> None:
        """Start the background scheduler.

        If already running, this is a no-op.
        """
        if self._is_running:
            logger.warning("Le planificateur est déjà en cours d'exécution.")
            return

        try:
            self._scheduler.start()
            self._is_running = True
            logger.info("Planificateur démarré.")
        except Exception as e:
            logger.error("Erreur lors du démarrage du planificateur: %s", e)
            raise

    def stop(self) -> None:
        """Stop the background scheduler gracefully."""
        if not self._is_running:
            logger.warning("Le planificateur n'est pas en cours d'exécution.")
            return

        try:
            self._scheduler.shutdown(wait=True)
            self._is_running = False
            logger.info("Planificateur arrêté.")
        except Exception as e:
            logger.error("Erreur lors de l'arrêt du planificateur: %s", e)
            raise

    def add_interval_job(
        self,
        func: Callable,
        job_id: str,
        hours: int = 0,
        minutes: int = 0,
        seconds: int = 0,
        **kwargs,
    ) -> None:
        """Add a job that runs at a fixed interval.

        Args:
            func: The callable to execute.
            job_id: A unique identifier for the job.
            hours: Interval hours between executions.
            minutes: Interval minutes between executions.
            seconds: Interval seconds between executions.
            **kwargs: Additional arguments passed to the callable.
        """
        trigger = IntervalTrigger(hours=hours, minutes=minutes, seconds=seconds)
        self._scheduler.add_job(
            func,
            trigger=trigger,
            id=job_id,
            replace_existing=True,
            kwargs=kwargs,
        )
        logger.info(
            "Job intervalle ajouté: %s (toutes les %dh %dm %ds)",
            job_id,
            hours,
            minutes,
            seconds,
        )

    def add_cron_job(
        self,
        func: Callable,
        job_id: str,
        hour: int = 0,
        minute: int = 0,
        day_of_week: str = "mon-fri",
        **kwargs,
    ) -> None:
        """Add a job that runs on a cron schedule.

        Args:
            func: The callable to execute.
            job_id: A unique identifier for the job.
            hour: Hour of the day (0-23).
            minute: Minute of the hour (0-59).
            day_of_week: Days to run (e.g., 'mon-fri', 'mon,wed,fri').
            **kwargs: Additional arguments passed to the callable.
        """
        trigger = CronTrigger(hour=hour, minute=minute, day_of_week=day_of_week)
        self._scheduler.add_job(
            func,
            trigger=trigger,
            id=job_id,
            replace_existing=True,
            kwargs=kwargs,
        )
        logger.info(
            "Job cron ajouté: %s (à %02d:%02d, jours: %s)",
            job_id,
            hour,
            minute,
            day_of_week,
        )

    def remove_job(self, job_id: str) -> bool:
        """Remove a scheduled job by its ID.

        Args:
            job_id: The unique identifier of the job to remove.

        Returns:
            True if the job was removed, False if not found.
        """
        try:
            self._scheduler.remove_job(job_id)
            logger.info("Job supprimé: %s", job_id)
            return True
        except Exception as e:
            logger.warning("Impossible de supprimer le job '%s': %s", job_id, e)
            return False

    def list_jobs(self) -> list[dict]:
        """List all scheduled jobs.

        Returns:
            A list of dicts with job information (id, name, next_run_time).
        """
        jobs = self._scheduler.get_jobs()
        return [
            {
                "id": job.id,
                "name": job.name,
                "next_run_time": str(job.next_run_time) if job.next_run_time else None,
                "trigger": str(job.trigger),
            }
            for job in jobs
        ]

    @property
    def is_running(self) -> bool:
        """Check if the scheduler is currently running.

        Returns:
            True if the scheduler is active.
        """
        return self._is_running

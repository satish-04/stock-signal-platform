"""Dramatiq actor module for background paper-trading jobs.

Actors are added in the next implementation block. Importing this module configures
the dedicated Redis broker without enabling order submission.
"""

from app.workers.broker import broker

__all__ = ["broker"]

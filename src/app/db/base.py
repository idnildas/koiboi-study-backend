"""SQLAlchemy declarative base for all ORM models.

All database models should inherit from this Base class to be included
in the ORM registry and participate in migrations.
"""

from sqlalchemy.orm import declarative_base

Base = declarative_base()

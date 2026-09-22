"""Alembic environment backed by the application's validated database settings."""

from alembic import context

from backend.app.core.config import get_database_settings
from backend.app.db.base import Base
from backend.app.db.models.branch import Branch  # noqa: F401
from backend.app.db.models.price import Price  # noqa: F401
from backend.app.db.models.product import Product  # noqa: F401
from backend.app.db.session import create_database_engine

config = context.config
target_metadata = Base.metadata


def get_database_url() -> str:
    """Reveal the validated URL only at the database connection boundary."""

    return get_database_settings().database_url.get_secret_value()


def run_migrations_offline() -> None:
    """Generate SQL without creating an Engine."""

    context.configure(
        url=get_database_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=True,
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations through the same safe engine factory used by the app."""

    connectable = create_database_engine(get_database_url())
    try:
        with connectable.connect() as connection:
            context.configure(
                connection=connection,
                target_metadata=target_metadata,
                render_as_batch=True,
                compare_type=True,
            )

            with context.begin_transaction():
                context.run_migrations()
    finally:
        connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

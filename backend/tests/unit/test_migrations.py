import importlib.util
from pathlib import Path

from alembic.config import Config


def test_alembic_config_validity() -> None:
    """Verify that alembic.ini is present and loads valid configuration."""
    backend_dir = Path(__file__).resolve().parent.parent.parent
    ini_path = backend_dir / "alembic.ini"
    assert ini_path.exists(), "alembic.ini must exist in backend directory"

    config = Config(str(ini_path))
    assert config.get_main_option("script_location") == "migrations"
    assert config.get_main_option("file_template") == "%(rev)s_%(slug)s"


def test_migration_files_exist() -> None:
    """Verify that migrations environment and template files exist."""
    backend_dir = Path(__file__).resolve().parent.parent.parent
    migrations_dir = backend_dir / "migrations"

    env_path = migrations_dir / "env.py"
    template_path = migrations_dir / "script.py.mako"
    versions_dir = migrations_dir / "versions"

    assert env_path.exists(), "migrations/env.py must exist"
    assert template_path.exists(), "migrations/script.py.mako must exist"
    assert versions_dir.exists(), "migrations/versions directory must exist"


def test_initial_migration_structure() -> None:
    """Verify 001_initial_tenancy_and_auth defines upgrade and downgrade."""
    backend_dir = Path(__file__).resolve().parent.parent.parent
    migration_file = backend_dir / "migrations" / "versions" / "001_initial_tenancy_and_auth.py"
    assert migration_file.exists(), "001_initial_tenancy_and_auth.py must exist"

    spec = importlib.util.spec_from_file_location("migration_001", str(migration_file))
    assert spec is not None and spec.loader is not None
    migration_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration_mod)

    # Check revision identifiers
    assert migration_mod.revision == "001"
    assert migration_mod.down_revision is None

    # Check upgrade and downgrade exist and are callable
    assert callable(migration_mod.upgrade)
    assert callable(migration_mod.downgrade)


def test_products_migration_structure() -> None:
    """Verify 002_products_and_inventory defines upgrade and downgrade."""
    backend_dir = Path(__file__).resolve().parent.parent.parent
    migration_file = backend_dir / "migrations" / "versions" / "002_products_and_inventory.py"
    assert migration_file.exists(), "002_products_and_inventory.py must exist"

    spec = importlib.util.spec_from_file_location("migration_002", str(migration_file))
    assert spec is not None and spec.loader is not None
    migration_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration_mod)

    # Check revision identifiers
    assert migration_mod.revision == "002"
    assert migration_mod.down_revision == "001"

    # Check upgrade and downgrade exist and are callable
    assert callable(migration_mod.upgrade)
    assert callable(migration_mod.downgrade)

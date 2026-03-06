import sys
import uuid
from pathlib import Path
from datetime import datetime
from types import SimpleNamespace

import pytest

# Ensure `app` package is importable regardless of IDE/test runner cwd.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture
def user():
    return SimpleNamespace(id=uuid.uuid4(), email="alice@example.com")


@pytest.fixture
def todo_node():
    return SimpleNamespace(
        id=uuid.uuid4(),
        title="Task",
        description="desc",
        completed=False,
        deadline=None,
        created_at=datetime.utcnow(),
        parent_id=None,
        context_tags=[],
    )

from app.main import app


def test_app_includes_auth_routes():
    paths = {route.path for route in app.routes}
    assert "/auth/register" in paths
    assert "/auth/login" in paths


def test_app_includes_todo_routes():
    paths = {route.path for route in app.routes}
    assert "/todos/" in paths
    assert "/todos/{todo_id}" in paths


def test_app_has_cors_middleware():
    middleware_names = {m.cls.__name__ for m in app.user_middleware}
    assert "CORSMiddleware" in middleware_names

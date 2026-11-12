from app.core.config import Settings


def test_settings_read_values_from_environment(monkeypatch):
    monkeypatch.setenv("ENV", "test")
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://u:p@db:5432/x")
    monkeypatch.setenv("JWT_SECRET", "s3cret")
    monkeypatch.setenv("CORS_ORIGINS", '["http://example.com"]')

    settings = Settings(_env_file=None)

    assert settings.env == "test"
    assert settings.database_url == "postgresql+psycopg://u:p@db:5432/x"
    assert settings.jwt_secret == "s3cret"
    assert settings.cors_origins == ["http://example.com"]


def test_settings_have_safe_defaults(monkeypatch):
    for name in ("ENV", "DATABASE_URL", "JWT_SECRET", "CORS_ORIGINS"):
        monkeypatch.delenv(name, raising=False)

    settings = Settings(_env_file=None)

    assert settings.env == "dev"
    assert settings.cors_origins == ["http://localhost:5173"]

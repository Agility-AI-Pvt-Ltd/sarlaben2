from app.core.config import Settings


def test_database_url_uses_asyncpg_driver() -> None:
    config = Settings(
        _env_file=None,
        DATABASE_URL="postgresql://user:password@localhost:5432/cow_x",
    )

    assert (
        config.database_url == "postgresql+asyncpg://user:password@localhost:5432/cow_x"
    )


def test_neon_database_url_uses_asyncpg_ssl_parameters() -> None:
    config = Settings(
        _env_file=None,
        DATABASE_URL=(
            "postgresql://user:password@example.neon.tech/cow_x"
            "?sslmode=require&channel_binding=require"
        ),
    )

    assert config.database_url.endswith("?ssl=require")

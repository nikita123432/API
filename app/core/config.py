from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DB_HOST: str
    DB_PORT: int
    PG_USER: str
    PG_PASSWORD: str
    PG_DB: str
    DOCKER_PORT: int

    SMTP_SERVER: str
    SMTP_PORT: int
    EMAIL_SENDER: str
    EMAIL_PASSWORD: str

    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str

    @property
    def DATABASE_URL_asyncpg(self):
        return f"postgresql+asyncpg://{self.PG_USER}:{self.PG_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.PG_DB}"

    @property
    def DATABASE_URL_psycopg(self):
        # DSN
        return f"postgresql+psycopg://{self.PG_USER}:{self.PG_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.PG_DB}"

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()





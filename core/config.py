from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Sign Language API"
    debug: bool = False
    firebase_key_path: str = "./serviceAccountKey.json"

    class Config:
        env_file = ".env"


settings = Settings()

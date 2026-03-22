from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Snowflake (key-pair auth)
    snowflake_account: str = ""
    snowflake_user: str = ""
    snowflake_private_key_path: str = "./snowflake_key.p8"
    snowflake_database: str = "vinci_db"
    snowflake_schema: str = "insurer_policies"
    snowflake_warehouse: str = "COMPUTE_WH"

    # Google
    google_application_credentials: str = ""
    google_api_key: str = ""
    google_project_id: str = ""
    google_project_number: str = ""
    documentai_processor_id: str = ""
    documentai_processor_name: str = ""
    documentai_location: str = "us"

    # MongoDB Atlas
    mongodb_uri: str = ""
    mongodb_database: str = "vinci"

    # ElevenLabs
    elevenlabs_api_key: str = ""
    elevenlabs_voice_id: str = "21m00Tcm4TlvDq8ikWAM"  # default Rachel voice

    # Capital One Nessie
    nessie_api_key: str = ""
    nessie_base_url: str = "http://api.nessieisreal.com"

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()

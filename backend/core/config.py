# >>> PERSONA START
import os


class PersonaSettings:
    PARAM_SEED_SALT: str = os.getenv("TESKI_PARAM_SALT", "teski-dev-salt")


persona_settings = PersonaSettings()
# <<< PERSONA END

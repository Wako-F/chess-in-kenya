import uvicorn

from chesske_platform.chesske.api import create_app
from chesske_platform.chesske.config import Settings


def main() -> None:
    settings = Settings()
    app = create_app(settings)
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)


if __name__ == "__main__":
    main()

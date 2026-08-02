import uvicorn

from agent_service.config import settings


def main() -> None:
    uvicorn.run(
        "agent_service.app:create_app",
        factory=True,
        host=settings.HOST,
        port=settings.PORT,
        reload=False,
    )


if __name__ == "__main__":
    main()

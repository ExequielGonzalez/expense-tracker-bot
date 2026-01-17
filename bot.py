from app.boot import build_dependencies
from app.telegram_app import build_application


def main() -> None:
    app = build_application()
    dependencies = build_dependencies()
    app.bot_data.update(dependencies)

    print("[INFO] Bot listo para recibir mensajes.")
    app.run_polling()


if __name__ == '__main__':
    main()


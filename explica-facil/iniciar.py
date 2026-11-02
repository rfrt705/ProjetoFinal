"""Prepara as configurações locais e inicia os dois serviços do projeto."""
from pathlib import Path
import secrets
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parent


def main():
    if not shutil.which("docker"):
        sys.exit("Instala o Docker Desktop e volta a executar este ficheiro.")
    ready = subprocess.run(["docker", "info"], capture_output=True)
    if ready.returncode:
        sys.exit("Abre o Docker Desktop, espera que esteja pronto e tenta novamente.")
    env = ROOT / ".env"
    if not env.exists():
        text = (ROOT / ".env.example").read_text(encoding="utf-8")
        text = text.replace("COMPOSE_PROJECT_NAME=SUBSTITUIR", f"COMPOSE_PROJECT_NAME=explica-facil-{secrets.token_hex(4)}")
        for key in ("DJANGO_SECRET_KEY", "MYSQL_PASSWORD", "MYSQL_ROOT_PASSWORD"):
            text = text.replace(f"{key}=SUBSTITUIR", f"{key}={secrets.token_urlsafe(36)}")
        env.write_text(text, encoding="utf-8")
        env.chmod(0o600)
        print("Configuração local criada. Os valores secretos ficaram apenas no .env.")
    print("A preparar o site e a base de dados. A primeira execução demora mais.")
    result = subprocess.run(["docker", "compose", "up", "--build", "-d", "--wait", "--wait-timeout", "240"], cwd=ROOT)
    if result.returncode:
        sys.exit("O arranque não terminou. Consulta docker compose logs para perceber o motivo.")
    port = next((line.split("=", 1)[1] for line in env.read_text().splitlines() if line.startswith("HOST_PORT=")), "8008")
    print(f"Abre http://localhost:{port}/ no navegador.")
    print("Para criar dados fictícios: docker compose exec web python manage.py preparar_demo")
    print("Lê o GUIA_PASSO_A_PASSO.md para continuar.")


if __name__ == "__main__":
    main()

"""Guarda uma cópia SQL da base normal sem escrever credenciais no comando."""
from datetime import datetime
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent


def main():
    folder = ROOT / "backups"
    folder.mkdir(exist_ok=True)
    target = folder / f"explica_facil_{datetime.now():%Y%m%d_%H%M%S}.sql"
    command = ["docker", "compose", "exec", "-T", "db", "sh", "-c",
               'MYSQL_PWD="$MYSQL_PASSWORD" mysqldump -u explica --single-transaction --no-tablespaces --set-gtid-purged=OFF explica_facil']
    with target.open("xb") as output:
        result = subprocess.run(command, cwd=ROOT, stdout=output, stderr=subprocess.PIPE)
    if result.returncode:
        target.unlink()
        sys.exit("Não foi possível criar a cópia. Confirma que o serviço db está a funcionar.")
    print(f"Cópia criada: {target}")
    print("O ficheiro contém os dados do projeto e fica fora do repositório.")


if __name__ == "__main__":
    main()

"""Restaura uma cópia na base de testes. Nunca escolhe a base normal como destino."""
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent


def mysql(sql=None, source=None):
    command = ["docker", "compose", "exec", "-T", "db", "sh", "-c",
               'MYSQL_PWD="$MYSQL_PASSWORD" mysql -u explica' + (" test_explica_facil" if source else "")]
    if source:
        with source.open("rb") as stream:
            result = subprocess.run(command, cwd=ROOT, stdin=stream, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    else:
        result = subprocess.run(command, cwd=ROOT, input=sql.encode(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode:
        sys.exit("O restauro de teste falhou. A base normal não foi alterada. Confirma os serviços e as permissões da base de testes.")
    return result.stdout.decode()


def main():
    if len(sys.argv) != 2:
        sys.exit("Utilização: python verificar_restauro.py backups/nome_da_copia.sql")
    source = Path(sys.argv[1]).resolve()
    if not source.is_file() or source.parent != (ROOT / "backups").resolve():
        sys.exit("Escolhe uma cópia SQL criada por backup.py dentro da pasta backups.")
    print("Vou substituir apenas test_explica_facil. Não executes testes automáticos em simultâneo.")
    mysql("DROP DATABASE IF EXISTS test_explica_facil; CREATE DATABASE test_explica_facil CHARACTER SET utf8mb4;")
    mysql(source=source)
    result = mysql("SELECT COUNT(*) AS sessoes_restauradas FROM test_explica_facil.explicacoes_sessao; "
                   "SELECT COUNT(*) AS inscricoes_restauradas FROM test_explica_facil.explicacoes_inscricao;")
    print(result)
    mysql("DROP DATABASE test_explica_facil;")
    print("Restauro concluído e base temporária removida. A base normal foi preservada.")


if __name__ == "__main__":
    main()

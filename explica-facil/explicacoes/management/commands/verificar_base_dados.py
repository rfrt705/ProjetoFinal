from django.core.management.base import BaseCommand, CommandError
from django.db import connection
from django.db.models import Count, Q
from explicacoes.models import Disciplina, Disponibilidade, Inscricao, Notificacao, Sessao, Utilizador


class Command(BaseCommand):
    help = "Confirma a ligação e apresenta contagens, sem mostrar palavras-passe ou dados pessoais."

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        self.stdout.write(self.style.SUCCESS(f"Ligação concluída. Motor: {connection.vendor}."))
        for model in [Utilizador, Disciplina, Disponibilidade, Sessao, Inscricao, Notificacao]:
            self.stdout.write(f"{model._meta.verbose_name_plural}: {model.objects.count()}")
        invalid = Sessao.objects.annotate(total=Count("inscricoes", filter=Q(inscricoes__estado="ativa"))).filter(total__gt=3).count()
        if invalid:
            raise CommandError(f"Foram encontradas {invalid} sessões acima da lotação.")
        self.stdout.write(self.style.SUCCESS("Nenhuma sessão ultrapassa três alunos ativos."))

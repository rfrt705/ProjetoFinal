"""Cria dados fictícios sem apagar dados existentes nem repor palavras-passe."""
from datetime import datetime, time, timedelta
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from explicacoes.models import Disciplina, Disponibilidade, ProfessorDisciplina, Sessao, Utilizador
from explicacoes.services import guardar_sessao, inscrever


class Command(BaseCommand):
    help = "Cria contas fictícias e sessões de demonstração na semana atual e na seguinte."

    @transaction.atomic
    def handle(self, *args, **options):
        password = "Aprender2026!"
        admin, created = Utilizador.objects.get_or_create(email="admin@explicafacil.test", defaults={"first_name": "Administração Demo", "papel": "administrador", "is_superuser": True})
        if created:
            admin.set_password(password)
            admin.save()
        teachers = []
        for email, name in [("ana@explicafacil.test", "Ana Silva"), ("maria@explicafacil.test", "Maria Santos"), ("sofia@explicafacil.test", "Sofia Martins")]:
            user, created = Utilizador.objects.get_or_create(email=email, defaults={"first_name": name, "papel": "professor"})
            if created:
                user.set_password(password)
                user.save()
            teachers.append(user)
            for day in range(5):
                Disponibilidade.objects.get_or_create(professor=user, dia_semana=day, hora_inicio=time(9), hora_fim=time(18))
        students = []
        for index, name in enumerate(["Inês Martins", "Miguel Costa", "Beatriz Sousa", "Tomás Pereira"], 1):
            user, created = Utilizador.objects.get_or_create(email=f"aluno{index}@explicafacil.test", defaults={"first_name": name, "papel": "aluno"})
            if created:
                user.set_password(password)
                user.save()
            students.append(user)
        disciplines = []
        for name, teacher in zip(["Matemática", "Português", "Inglês"], teachers):
            discipline, _ = Disciplina.objects.get_or_create(nome=name)
            ProfessorDisciplina.objects.get_or_create(professor=teacher, disciplina=discipline)
            disciplines.append(discipline)
        today = timezone.localdate()
        monday = today - timedelta(days=today.weekday())
        count = 0
        for week in range(2):
            for day in range(5):
                for number, hour in enumerate([10, 15]):
                    course = (day + number) % 3
                    date = monday + timedelta(days=week * 7 + day)
                    start = timezone.make_aware(datetime.combine(date, time(hour)))
                    if start <= timezone.now():
                        continue
                    if Sessao.objects.filter(professor=teachers[course], inicio=start).exists():
                        continue
                    session = guardar_sessao(admin, disciplines[course], teachers[course], start)
                    # As ocupações 0, 1, 2 e 3 permitem demonstrar todas as cores.
                    for student in students[:(day + number) % 4]:
                        inscrever(student, session.pk)
                    count += 1
        self.stdout.write(self.style.SUCCESS(f"Demonstração preparada. {count} novas sessões. Nenhum registo existente foi apagado."))
        self.stdout.write("Contas fictícias: admin@explicafacil.test, ana@explicafacil.test, aluno1@explicafacil.test")
        self.stdout.write("Palavra-passe inicial das contas demo: Aprender2026!")

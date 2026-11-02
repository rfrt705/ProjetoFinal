from datetime import datetime, time, timedelta
from django.test import TestCase
from django.utils import timezone
from explicacoes.models import Disciplina, Disponibilidade, ProfessorDisciplina, Utilizador
from explicacoes.services import guardar_sessao


def criar_cenario():
    admin = Utilizador.objects.create_superuser("admin@example.test", "Teste2026!forte", first_name="Admin")
    professor = Utilizador.objects.create_user("prof@example.test", "Teste2026!forte", first_name="Professor", papel="professor")
    aluno = Utilizador.objects.create_user("aluno@example.test", "Teste2026!forte", first_name="Aluno")
    disciplina = Disciplina.objects.create(nome="Matemática")
    ProfessorDisciplina.objects.create(professor=professor, disciplina=disciplina)
    for day in range(5):
        Disponibilidade.objects.create(professor=professor, dia_semana=day, hora_inicio=time(9), hora_fim=time(18))
    today = timezone.localdate()
    date = today + timedelta(days=7-today.weekday())
    inicio = timezone.make_aware(datetime.combine(date, time(10)))
    sessao = guardar_sessao(admin, disciplina, professor, inicio)
    return admin, professor, aluno, disciplina, sessao


class CenarioTestCase(TestCase):
    def setUp(self):
        self.admin, self.professor, self.aluno, self.disciplina, self.sessao = criar_cenario()

from datetime import time, timedelta
from django.core.exceptions import PermissionDenied, ValidationError
from explicacoes import services
from explicacoes.models import Disponibilidade, ProfessorDisciplina
from .base import CenarioTestCase


class HorarioTests(CenarioTestCase):
    def test_duracao_de_uma_hora(self):
        self.assertEqual(self.sessao.fim-self.sessao.inicio, timedelta(hours=1))

    def test_sessoes_consecutivas_permitidas(self):
        new = services.guardar_sessao(self.admin, self.disciplina, self.professor, self.sessao.fim)
        self.assertEqual(new.inicio, self.sessao.fim)

    def test_professor_nao_pode_ter_sessoes_simultaneas(self):
        with self.assertRaisesMessage(ValidationError, "já tem"):
            services.guardar_sessao(self.admin, self.disciplina, self.professor, self.sessao.inicio)

    def test_horario_fora_da_lista_recusado(self):
        with self.assertRaisesMessage(ValidationError, "horários fixos"):
            services.guardar_sessao(self.admin, self.disciplina, self.professor, self.sessao.inicio+timedelta(minutes=15))

    def test_professor_sem_disciplina_recusado(self):
        ProfessorDisciplina.objects.all().delete()
        with self.assertRaisesMessage(ValidationError, "associado"):
            services.guardar_sessao(self.admin, self.disciplina, self.professor, self.sessao.fim)

    def test_fora_da_disponibilidade_recusado(self):
        Disponibilidade.objects.all().delete()
        with self.assertRaisesMessage(ValidationError, "disponibilidade"):
            services.guardar_sessao(self.admin, self.disciplina, self.professor, self.sessao.fim)

    def test_disponibilidades_sobrepostas_recusadas(self):
        with self.assertRaisesMessage(ValidationError, "sobrepõe"):
            services.guardar_disponibilidade(self.professor, 0, time(10), time(12))

    def test_nao_remove_disponibilidade_usada_por_sessao(self):
        interval = self.professor.disponibilidades.get(dia_semana=0)
        with self.assertRaisesMessage(ValidationError, "necessário"):
            services.apagar_disponibilidade(self.professor, interval.pk)

    def test_nao_edita_horario_com_alunos_inscritos(self):
        services.inscrever(self.aluno, self.sessao.pk)
        with self.assertRaisesMessage(ValidationError, "já tem alunos"):
            services.guardar_sessao(self.admin, self.disciplina, self.professor, self.sessao.fim, self.sessao.pk)

    def test_aluno_nao_cria_sessoes(self):
        with self.assertRaises(PermissionDenied):
            services.guardar_sessao(self.aluno, self.disciplina, self.professor, self.sessao.fim)

    def test_nao_desativa_utilizador_com_inscricoes_futuras(self):
        services.inscrever(self.aluno, self.sessao.pk)
        self.aluno.is_active = False
        with self.assertRaisesMessage(ValidationError, "Resolve primeiro"):
            self.aluno.full_clean(exclude=["password"])

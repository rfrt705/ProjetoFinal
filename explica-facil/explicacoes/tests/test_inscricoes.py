from datetime import timedelta
from unittest.mock import patch
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone
from explicacoes.models import Inscricao, Notificacao, Sessao, Utilizador
from explicacoes import services
from .base import CenarioTestCase


class InscricaoTests(CenarioTestCase):
    def test_tres_alunos_aceites_quarto_recusado(self):
        for n in range(3):
            student = Utilizador.objects.create_user(f"aluno{n}@example.test", "abc", first_name=f"Aluno {n}")
            services.inscrever(student, self.sessao.pk)
        with self.assertRaisesMessage(ValidationError, "completa"):
            services.inscrever(self.aluno, self.sessao.pk)
        self.assertEqual(self.sessao.ocupacao, 3)

    def test_inscricao_duplicada_nao_ocupa_duas_vagas(self):
        services.inscrever(self.aluno, self.sessao.pk)
        with self.assertRaisesMessage(ValidationError, "Já estás"):
            services.inscrever(self.aluno, self.sessao.pk)
        self.assertEqual(self.sessao.ocupacao, 1)

    def test_base_de_dados_impede_duplicado(self):
        Inscricao.objects.create(aluno=self.aluno, sessao=self.sessao)
        with self.assertRaises(IntegrityError), transaction.atomic():
            Inscricao.objects.create(aluno=self.aluno, sessao=self.sessao)

    def test_cancelar_liberta_vaga_e_reativa_o_mesmo_registo(self):
        inscricao = services.inscrever(self.aluno, self.sessao.pk)
        services.cancelar_inscricao(self.aluno, inscricao.pk)
        self.assertEqual(self.sessao.ocupacao, 0)
        nova = services.inscrever(self.aluno, self.sessao.pk)
        self.assertEqual(inscricao.pk, nova.pk)
        self.assertEqual(self.sessao.ocupacao, 1)
        self.assertIsNone(nova.cancelada_em)

    def test_nao_cancela_inscricao_de_outro_aluno(self):
        booking = services.inscrever(self.aluno, self.sessao.pk)
        other = Utilizador.objects.create_user("outro@example.test", "abc")
        with self.assertRaises(PermissionDenied):
            services.cancelar_inscricao(other, booking.pk)

    def test_nao_inscreve_professor(self):
        with self.assertRaises(PermissionDenied):
            services.inscrever(self.professor, self.sessao.pk)

    def test_sessao_passada_ou_cancelada_nao_aceita_inscricao(self):
        Sessao.objects.filter(pk=self.sessao.pk).update(inicio=timezone.now()-timedelta(hours=1))
        with self.assertRaises(ValidationError):
            services.inscrever(self.aluno, self.sessao.pk)

    def test_aluno_nao_pode_ter_duas_sessoes_sobrepostas(self):
        services.inscrever(self.aluno, self.sessao.pk)
        second = Sessao.objects.create(professor=self.professor, disciplina=self.disciplina,
                                      inicio=self.sessao.inicio+timedelta(minutes=30), fim=self.sessao.fim+timedelta(minutes=30))
        with self.assertRaisesMessage(ValidationError, "coincide"):
            services.inscrever(self.aluno, second.pk)

    def test_cancelar_sessao_cancela_inscricoes_e_avisa_participantes(self):
        booking = services.inscrever(self.aluno, self.sessao.pk)
        services.cancelar_sessao(self.admin, self.sessao.pk, "Professor indisponível")
        booking.refresh_from_db(); self.sessao.refresh_from_db()
        self.assertEqual(self.sessao.estado, "cancelada")
        self.assertEqual(booking.estado, "cancelada")
        self.assertEqual(Notificacao.objects.filter(tipo="cancelamento_sessao").count(), 2)
        services.cancelar_sessao(self.admin, self.sessao.pk, "Repetição")
        self.assertEqual(Notificacao.objects.filter(tipo="cancelamento_sessao").count(), 2)
        with self.assertRaises(ValidationError):
            services.inscrever(self.aluno, self.sessao.pk)

    def test_falha_da_notificacao_reverte_inscricao(self):
        with patch("explicacoes.services.notificar", side_effect=RuntimeError("Falha simulada")):
            with self.assertRaises(RuntimeError):
                services.inscrever(self.aluno, self.sessao.pk)
        self.assertEqual(Inscricao.objects.count(), 0)

    def test_cancelar_duas_vezes_nao_duplica_aviso(self):
        booking = services.inscrever(self.aluno, self.sessao.pk)
        services.cancelar_inscricao(self.aluno, booking.pk)
        services.cancelar_inscricao(self.aluno, booking.pk)
        self.assertEqual(Notificacao.objects.filter(tipo="cancelamento_inscricao").count(), 1)

    def test_aviso_so_para_alunos_ativos_da_sessao_e_professor(self):
        services.inscrever(self.aluno, self.sessao.pk)
        total = services.enviar_aviso(self.admin, self.sessao.pk, "Trazer calculadora.")
        self.assertEqual(total, 2)
        self.assertEqual(Notificacao.objects.filter(tipo="aviso").count(), 2)

    def test_cancelamento_depois_do_inicio_recusado(self):
        booking = services.inscrever(self.aluno, self.sessao.pk)
        Sessao.objects.filter(pk=self.sessao.pk).update(inicio=timezone.now()-timedelta(minutes=1))
        with self.assertRaises(ValidationError):
            services.cancelar_inscricao(self.aluno, booking.pk)

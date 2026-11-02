"""Estes testes precisam de MySQL: SQLite não implementa os mesmos bloqueios."""
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from unittest import skipUnless
from django.core.exceptions import ValidationError
from django.db import close_old_connections, connection
from django.test import TransactionTestCase
from explicacoes.models import Inscricao, Sessao, Utilizador
from explicacoes.services import inscrever
from .base import criar_cenario


@skipUnless(connection.vendor == "mysql", "O teste de bloqueios exige MySQL.")
class SimultaneidadeTests(TransactionTestCase):
    def setUp(self):
        self.admin, self.professor, self.aluno, self.disciplina, self.sessao = criar_cenario()

    def correr_pedidos(self, requests):
        barrier = Barrier(len(requests))

        def attempt(pair):
            close_old_connections()
            student_id, session_id = pair
            try:
                student = Utilizador.objects.get(pk=student_id)
                barrier.wait(timeout=10)
                inscrever(student, session_id)
                return "aceite"
            except ValidationError:
                return "recusado"
            finally:
                connection.close()

        with ThreadPoolExecutor(max_workers=len(requests)) as executor:
            return list(executor.map(attempt, requests))

    def test_so_um_aluno_ocupa_a_ultima_vaga(self):
        students = [Utilizador.objects.create_user(f"concorrente{i}@example.test", "abc") for i in range(4)]
        inscrever(students[0], self.sessao.pk)
        inscrever(students[1], self.sessao.pk)
        results = self.correr_pedidos([(s.pk, self.sessao.pk) for s in students[2:]])
        self.assertCountEqual(results, ["aceite", "recusado"])
        self.assertEqual(Inscricao.objects.filter(sessao=self.sessao, estado="ativa").count(), 3)

    def test_mesmo_aluno_nao_ocupa_sessoes_sobrepostas(self):
        other = Sessao.objects.create(professor=self.professor, disciplina=self.disciplina,
                                     inicio=self.sessao.inicio, fim=self.sessao.fim)
        results = self.correr_pedidos([(self.aluno.pk, self.sessao.pk), (self.aluno.pk, other.pk)])
        self.assertCountEqual(results, ["aceite", "recusado"])
        self.assertEqual(Inscricao.objects.filter(aluno=self.aluno, estado="ativa").count(), 1)

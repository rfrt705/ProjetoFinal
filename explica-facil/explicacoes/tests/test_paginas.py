from datetime import timedelta
from django.test import Client
from django.urls import reverse
from django.utils import timezone
from explicacoes.models import Disciplina, Disponibilidade, Notificacao, ProfessorDisciplina, Sessao, Utilizador
from explicacoes.services import inscrever
from .base import CenarioTestCase


class PaginasTests(CenarioTestCase):
    def test_anonimo_encaminhado_para_entrada(self):
        self.assertRedirects(self.client.get("/"), "/entrar/?next=/")

    def test_registo_publico_so_cria_aluno(self):
        response = self.client.post(reverse("registo"), {
            "first_name": "Nova Aluna", "email": "nova@example.test", "papel": "administrador",
            "password1": "UmaSenhaForte2026!", "password2": "UmaSenhaForte2026!",
        })
        self.assertRedirects(response, reverse("plano"))
        user = Utilizador.objects.get(email="nova@example.test")
        self.assertEqual(user.papel, "aluno")
        self.assertFalse(user.is_staff)
        self.assertNotEqual(user.password, "UmaSenhaForte2026!")

    def test_login_com_email_em_maiusculas(self):
        response = self.client.post(reverse("login"), {"username": self.aluno.email.upper(), "password": "Teste2026!forte"})
        self.assertRedirects(response, reverse("plano"))

    def test_paginas_do_aluno(self):
        self.client.force_login(self.aluno)
        for name in ["plano", "minhas_inscricoes", "notificacoes"]:
            self.assertEqual(self.client.get(reverse(name)).status_code, 200)
        self.assertEqual(self.client.get(reverse("detalhe", args=[self.sessao.pk])).status_code, 200)

    def test_aluno_nao_acede_a_gestao_ou_professor(self):
        self.client.force_login(self.aluno)
        for name in ["gestao_sessoes", "nova_sessao", "disponibilidades", "sessoes_professor"]:
            self.assertEqual(self.client.get(reverse(name)).status_code, 403)

    def test_paginas_do_professor(self):
        self.client.force_login(self.professor)
        for name in ["sessoes_professor", "disponibilidades"]:
            self.assertEqual(self.client.get(reverse(name)).status_code, 200)

    def test_paginas_do_administrador(self):
        self.client.force_login(self.admin)
        for name in ["gestao_sessoes", "nova_sessao", "admin:index", "admin:explicacoes_utilizador_changelist", "admin:explicacoes_disciplina_add"]:
            self.assertEqual(self.client.get(reverse(name)).status_code, 200)

    def test_admin_cria_professor_no_painel(self):
        self.client.force_login(self.admin)
        response = self.client.post(reverse("admin:explicacoes_utilizador_add"), {
            "email": "novo-prof@example.test", "first_name": "Novo Professor", "papel": "professor",
            "password1": "OutraSenha2026!forte", "password2": "OutraSenha2026!forte", "is_active": "on",
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Utilizador.objects.get(email="novo-prof@example.test").papel, "professor")

    def test_notificacoes_privadas(self):
        notification = Notificacao.objects.create(destinatario=self.professor, tipo="aviso", mensagem="Privada")
        self.client.force_login(self.aluno)
        self.assertNotContains(self.client.get(reverse("notificacoes")), "Privada")
        self.assertEqual(self.client.post(reverse("ler_notificacao", args=[notification.pk])).status_code, 404)

    def test_inscricao_exige_post_e_csrf(self):
        self.client.force_login(self.aluno)
        self.assertEqual(self.client.get(reverse("inscrever", args=[self.sessao.pk])).status_code, 405)
        protected = Client(enforce_csrf_checks=True)
        protected.force_login(self.aluno)
        self.assertEqual(protected.post(reverse("inscrever", args=[self.sessao.pk])).status_code, 403)

    def test_inscricao_e_cancelamento_pela_interface(self):
        self.client.force_login(self.aluno)
        self.assertEqual(self.client.post(reverse("inscrever", args=[self.sessao.pk])).status_code, 302)
        booking = self.aluno.inscricoes.get()
        self.assertEqual(self.client.get(reverse("cancelar_inscricao", args=[booking.pk])).status_code, 200)
        self.client.post(reverse("cancelar_inscricao", args=[booking.pk]))
        booking.refresh_from_db()
        self.assertEqual(booking.estado, "cancelada")

    def test_detalhe_nao_mostra_nomes_dos_outros_alunos(self):
        inscrever(self.aluno, self.sessao.pk)
        other = Utilizador.objects.create_user("outra@example.test", "abc", first_name="Pessoa privada")
        inscrever(other, self.sessao.pk)
        self.client.force_login(self.aluno)
        self.assertNotContains(self.client.get(reverse("detalhe", args=[self.sessao.pk])), "Pessoa privada")

    def test_admin_normal_tem_acesso_a_gestao(self):
        normal = Utilizador.objects.create_user("gestor@example.test", "abc", papel="administrador")
        self.client.force_login(normal)
        self.assertEqual(self.client.get(reverse("admin:explicacoes_disciplina_changelist")).status_code, 200)
        self.assertEqual(self.client.get(reverse("gestao_sessoes")).status_code, 200)

    def test_administrador_cria_sessao_pelo_formulario(self):
        self.client.force_login(self.admin)
        inicio = timezone.localtime(self.sessao.fim)
        response = self.client.post(reverse("nova_sessao"), {
            "disciplina": self.disciplina.pk, "professor": self.professor.pk,
            "data": inicio.strftime("%Y-%m-%d"), "hora": inicio.strftime("%H:%M"),
        })
        self.assertRedirects(response, reverse("gestao_sessoes"))
        self.assertTrue(Sessao.objects.filter(inicio=inicio).exists())

    def test_admin_cria_disciplina_e_associa_professor(self):
        self.client.force_login(self.admin)
        response = self.client.post(reverse("admin:explicacoes_disciplina_add"), {
            "nome": "Física", "ativa": "on",
            "professores_associados-TOTAL_FORMS": "1", "professores_associados-INITIAL_FORMS": "0",
            "professores_associados-MIN_NUM_FORMS": "0", "professores_associados-MAX_NUM_FORMS": "1000",
            "professores_associados-0-professor": self.professor.pk,
        })
        self.assertEqual(response.status_code, 302)
        course = Disciplina.objects.get(nome="Física")
        self.assertTrue(ProfessorDisciplina.objects.filter(professor=self.professor, disciplina=course).exists())

    def test_professor_nao_reduz_disponibilidade_usada(self):
        self.client.force_login(self.professor)
        interval = Disponibilidade.objects.get(professor=self.professor, dia_semana=0)
        response = self.client.post(reverse("editar_disponibilidade", args=[interval.pk]), {
            "dia_semana": "0", "hora_inicio": "14:00", "hora_fim": "18:00",
        })
        self.assertContains(response, "sem disponibilidade")
        interval.refresh_from_db()
        self.assertEqual(interval.hora_inicio.hour, 9)

    def test_aviso_lido_apenas_por_post(self):
        item = Notificacao.objects.create(destinatario=self.aluno, tipo="aviso", mensagem="Mensagem")
        self.client.force_login(self.aluno)
        url = reverse("ler_notificacao", args=[item.pk])
        self.assertEqual(self.client.get(url).status_code, 405)
        self.client.post(url)
        item.refresh_from_db()
        self.assertIsNotNone(item.lida_em)

    def test_mensagem_html_e_apresentada_como_texto(self):
        Notificacao.objects.create(destinatario=self.aluno, tipo="aviso", mensagem="<script>alert(1)</script>")
        self.client.force_login(self.aluno)
        response = self.client.get(reverse("notificacoes"))
        self.assertContains(response, "&lt;script&gt;")
        self.assertNotContains(response, "<script>alert(1)</script>")

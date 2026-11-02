from django.urls import path
from . import views

urlpatterns = [
    path("", views.plano, name="plano"),
    path("registar/", views.registo, name="registo"),
    path("sessoes/<int:pk>/", views.detalhe, name="detalhe"),
    path("sessoes/<int:pk>/inscrever/", views.inscrever, name="inscrever"),
    path("inscricoes/", views.minhas_inscricoes, name="minhas_inscricoes"),
    path("inscricoes/<int:pk>/cancelar/", views.cancelar_inscricao, name="cancelar_inscricao"),
    path("professor/sessoes/", views.sessoes_professor, name="sessoes_professor"),
    path("professor/disponibilidade/", views.disponibilidades, name="disponibilidades"),
    path("professor/disponibilidade/<int:pk>/editar/", views.disponibilidades, name="editar_disponibilidade"),
    path("professor/disponibilidade/<int:pk>/remover/", views.apagar_disponibilidade, name="apagar_disponibilidade"),
    path("gestao/sessoes/", views.gestao_sessoes, name="gestao_sessoes"),
    path("gestao/sessoes/nova/", views.formulario_sessao, name="nova_sessao"),
    path("gestao/sessoes/<int:pk>/editar/", views.formulario_sessao, name="editar_sessao"),
    path("gestao/sessoes/<int:pk>/cancelar/", views.cancelar_sessao, name="cancelar_sessao"),
    path("gestao/sessoes/<int:pk>/aviso/", views.aviso, name="aviso"),
    path("notificacoes/", views.notificacoes, name="notificacoes"),
    path("notificacoes/<int:pk>/ler/", views.ler_notificacao, name="ler_notificacao"),
]

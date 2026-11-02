"""Regras que alteram os dados. Os bloqueios protegem pedidos simultâneos."""
from datetime import timedelta
from django.conf import settings
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone
from .models import Disciplina, Disponibilidade, Inscricao, Notificacao, Sessao, Utilizador


def texto_sessao(sessao):
    inicio = timezone.localtime(sessao.inicio)
    return f"{sessao.disciplina.nome}, {inicio:%d/%m/%Y}, {inicio:%H:%M}–{timezone.localtime(sessao.fim):%H:%M}"


def notificar(destinatario, sessao, tipo, mensagem):
    return Notificacao.objects.create(destinatario=destinatario, sessao=sessao, tipo=tipo, mensagem=mensagem)


@transaction.atomic
def inscrever(aluno, sessao_id):
    # A mesma pessoa não pode fazer duas inscrições incompatíveis em simultâneo.
    aluno = Utilizador.objects.select_for_update().get(pk=aluno.pk)
    if aluno.papel != "aluno" or not aluno.is_active:
        raise PermissionDenied("Só os alunos ativos se podem inscrever.")
    # Dois alunos que disputam a última vaga são atendidos um de cada vez.
    sessao = Sessao.objects.select_for_update().get(pk=sessao_id)
    if sessao.estado != "agendada" or sessao.inicio <= timezone.now():
        raise ValidationError("Esta sessão já começou ou foi cancelada.")
    existente = Inscricao.objects.filter(aluno=aluno, sessao=sessao).first()
    if existente and existente.estado == "ativa":
        raise ValidationError("Já estás inscrito nesta sessão.")
    if sessao.inscricoes.filter(estado="ativa").count() >= settings.CAPACIDADE_SESSAO:
        raise ValidationError("A sessão está completa. Escolhe outro horário.")
    if aluno.inscricoes.filter(estado="ativa", sessao__estado="agendada",
                              sessao__inicio__lt=sessao.fim, sessao__fim__gt=sessao.inicio).exists():
        raise ValidationError("Já tens uma explicação que coincide com este horário.")
    if existente:
        existente.estado = "ativa"
        existente.cancelada_em = None
        existente.save(update_fields=["estado", "cancelada_em", "atualizada_em"])
        inscricao = existente
    else:
        inscricao = Inscricao.objects.create(aluno=aluno, sessao=sessao)
    notificar(aluno, sessao, "inscricao", f"Inscrição confirmada: {texto_sessao(sessao)}. Professor: {sessao.professor.nome}.")
    return inscricao


@transaction.atomic
def cancelar_inscricao(aluno, inscricao_id):
    aluno = Utilizador.objects.select_for_update().get(pk=aluno.pk)
    inscricao = Inscricao.objects.get(pk=inscricao_id)
    if inscricao.aluno_id != aluno.pk or aluno.papel != "aluno":
        raise PermissionDenied("Esta inscrição não te pertence.")
    sessao = Sessao.objects.select_for_update().get(pk=inscricao.sessao_id)
    inscricao.refresh_from_db()
    if inscricao.estado == "cancelada":
        return False
    if sessao.inicio <= timezone.now():
        raise ValidationError("Só podes cancelar antes do início da sessão.")
    inscricao.estado = "cancelada"
    inscricao.cancelada_em = timezone.now()
    inscricao.save(update_fields=["estado", "cancelada_em", "atualizada_em"])
    notificar(aluno, sessao, "cancelamento_inscricao", f"Cancelaste a tua inscrição: {texto_sessao(sessao)}.")
    return True


@transaction.atomic
def guardar_sessao(administrador, disciplina, professor, inicio, sessao_id=None):
    if not administrador.administrador:
        raise PermissionDenied
    disciplina = Disciplina.objects.select_for_update().get(pk=disciplina.pk)
    # Serializar a criação por professor impede duas sessões sobrepostas.
    professor_ids = {professor.pk}
    if sessao_id:
        professor_ids.add(Sessao.objects.get(pk=sessao_id).professor_id)
    list(Utilizador.objects.select_for_update().filter(pk__in=professor_ids).order_by("pk"))
    if sessao_id:
        sessao = Sessao.objects.select_for_update().get(pk=sessao_id)
        if sessao.professor_id not in professor_ids:
            raise ValidationError("A sessão foi alterada entretanto. Atualiza a página e tenta novamente.")
        if sessao.estado == "cancelada" or not sessao.futura:
            raise ValidationError("Só podes editar sessões futuras que não estejam canceladas.")
        changed = (sessao.disciplina_id != disciplina.pk or sessao.professor_id != professor.pk or sessao.inicio != inicio)
        if changed and sessao.inscricoes.filter(estado="ativa").exists():
            raise ValidationError("Esta sessão já tem alunos. Cancela-a e cria outra para alterar o horário, professor ou disciplina.")
    else:
        sessao = Sessao()
    sessao.professor_id = professor.pk
    # Recarregar os objetos depois de obter o bloqueio evita usar dados antigos.
    sessao.professor = Utilizador.objects.get(pk=professor.pk)
    sessao.disciplina = disciplina
    sessao.inicio = inicio
    sessao.fim = inicio + timedelta(hours=1)
    sessao.full_clean()
    sessao.save()
    return sessao


@transaction.atomic
def cancelar_sessao(administrador, sessao_id, motivo):
    if not administrador.administrador:
        raise PermissionDenied
    sessao = Sessao.objects.select_for_update().get(pk=sessao_id)
    if sessao.estado == "cancelada":
        return False
    if not sessao.futura:
        raise ValidationError("Só podes cancelar sessões futuras.")
    motivo = motivo.strip()
    if not motivo:
        raise ValidationError("Indica o motivo do cancelamento.")
    if len(motivo) > 500:
        raise ValidationError("O motivo pode ter no máximo 500 caracteres.")
    inscritos = list(sessao.inscricoes.filter(estado="ativa").select_related("aluno"))
    sessao.estado = "cancelada"
    sessao.motivo_cancelamento = motivo
    sessao.save(update_fields=["estado", "motivo_cancelamento"])
    sessao.inscricoes.filter(estado="ativa").update(estado="cancelada", cancelada_em=timezone.now(), atualizada_em=timezone.now())
    destinatarios = {i.aluno_id: i.aluno for i in inscritos}
    destinatarios[sessao.professor_id] = sessao.professor
    for pessoa in destinatarios.values():
        notificar(pessoa, sessao, "cancelamento_sessao", f"Sessão cancelada: {texto_sessao(sessao)}. Motivo: {motivo}")
    return True


@transaction.atomic
def guardar_disponibilidade(professor, dia_semana, hora_inicio, hora_fim, disponibilidade_id=None):
    professor = Utilizador.objects.select_for_update().get(pk=professor.pk)
    if professor.papel != "professor" or not professor.is_active:
        raise PermissionDenied
    if disponibilidade_id:
        disponibilidade = Disponibilidade.objects.get(pk=disponibilidade_id, professor=professor)
    else:
        disponibilidade = Disponibilidade(professor=professor)
    disponibilidade.dia_semana = dia_semana
    disponibilidade.hora_inicio = hora_inicio
    disponibilidade.hora_fim = hora_fim
    disponibilidade.full_clean()
    disponibilidade.save()
    return disponibilidade


@transaction.atomic
def apagar_disponibilidade(professor, disponibilidade_id):
    professor = Utilizador.objects.select_for_update().get(pk=professor.pk)
    if professor.papel != "professor":
        raise PermissionDenied
    disponibilidade = Disponibilidade.objects.get(pk=disponibilidade_id, professor=professor)
    restantes = list(professor.disponibilidades.exclude(pk=disponibilidade.pk))
    for sessao in professor.sessoes_lecionadas.filter(estado="agendada", inicio__gt=timezone.now()):
        if not any(d.abrange(sessao.inicio, sessao.fim) for d in restantes):
            raise ValidationError("Este intervalo é necessário para uma sessão futura. Resolve essa sessão primeiro.")
    disponibilidade.delete()


@transaction.atomic
def enviar_aviso(administrador, sessao_id, mensagem):
    if not administrador.administrador:
        raise PermissionDenied
    sessao = Sessao.objects.select_for_update().get(pk=sessao_id)
    mensagem = mensagem.strip()
    if not mensagem or len(mensagem) > 1000:
        raise ValidationError("Escreve uma mensagem com 1 a 1000 caracteres.")
    ids = set(sessao.inscricoes.filter(estado="ativa").values_list("aluno_id", flat=True))
    ids.add(sessao.professor_id)
    destinatarios = list(Utilizador.objects.filter(pk__in=ids, is_active=True))
    for pessoa in destinatarios:
        notificar(pessoa, sessao, "aviso", f"{texto_sessao(sessao)}. {mensagem}")
    return len(destinatarios)

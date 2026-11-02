from datetime import datetime, time, timedelta
from functools import wraps
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import Count, Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST
from .forms import AvisoForm, DisponibilidadeForm, MotivoForm, RegistoForm, SessaoForm
from .models import DIAS, Disciplina, Disponibilidade, Inscricao, Notificacao, Sessao, Utilizador
from . import services


def perfil(papel):
    def decorator(view):
        @login_required
        @wraps(view)
        def wrapped(request, *args, **kwargs):
            allowed = request.user.administrador if papel == "administrador" else request.user.papel == papel
            if not allowed:
                raise PermissionDenied
            return view(request, *args, **kwargs)
        return wrapped
    return decorator


def erros_formulario(form, exc):
    for message in exc.messages:
        form.add_error(None, message)


def registo(request):
    if request.user.is_authenticated:
        return redirect("plano")
    form = RegistoForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, "Conta criada. Já podes escolher a tua explicação.")
        return redirect("plano")
    return render(request, "registration/registo.html", {"form": form})


@login_required
def plano(request):
    try:
        selected = datetime.strptime(request.GET.get("semana", ""), "%Y-%m-%d").date()
    except (ValueError, TypeError):
        selected = timezone.localdate()
    monday = selected - timedelta(days=selected.weekday())
    start = timezone.make_aware(datetime.combine(monday, time.min))
    end = start + timedelta(days=7)
    sessions = Sessao.objects.filter(inicio__gte=start, inicio__lt=end).select_related("disciplina", "professor").annotate(
        total_ativos=Count("inscricoes", filter=Q(inscricoes__estado="ativa")))
    disciplina = request.GET.get("disciplina", "")
    professor = request.GET.get("professor", "")
    if disciplina.isdigit():
        sessions = sessions.filter(disciplina_id=disciplina)
    if professor.isdigit():
        sessions = sessions.filter(professor_id=professor)
    sessions = list(sessions)
    days = []
    for i, name in DIAS:
        date = monday + timedelta(days=i)
        items = [s for s in sessions if timezone.localtime(s.inicio).date() == date]
        if i < 5 or items:
            days.append({"nome": name, "data": date, "sessoes": items})
    inscritas = set(request.user.inscricoes.filter(estado="ativa").values_list("sessao_id", flat=True))
    return render(request, "explicacoes/plano.html", {
        "dias": days, "segunda": monday, "domingo": monday + timedelta(days=6),
        "anterior": monday - timedelta(days=7), "seguinte": monday + timedelta(days=7),
        "disciplinas": Disciplina.objects.filter(ativa=True),
        "professores": Utilizador.objects.filter(papel="professor", is_active=True),
        "filtro_disciplina": disciplina, "filtro_professor": professor,
        "inscritas": inscritas, "total_sessoes": len(sessions),
        "total_vagas": sum(s.vagas for s in sessions if s.estado == "agendada" and s.futura),
        "total_inscricoes": len(inscritas),
    })


@login_required
def detalhe(request, pk):
    session = get_object_or_404(Sessao.objects.select_related("disciplina", "professor"), pk=pk)
    booking = Inscricao.objects.filter(aluno=request.user, sessao=session, estado="ativa").first()
    alunos = None
    if request.user.administrador or session.professor_id == request.user.pk:
        alunos = session.inscricoes.filter(estado="ativa").select_related("aluno")
    return render(request, "explicacoes/detalhe.html", {"sessao": session, "inscricao": booking, "alunos": alunos})


@perfil("aluno")
@require_POST
def inscrever(request, pk):
    get_object_or_404(Sessao, pk=pk)
    try:
        services.inscrever(request.user, pk)
        messages.success(request, "Inscrição confirmada. Guardámos os detalhes nas tuas notificações.")
    except ValidationError as exc:
        for message in exc.messages:
            messages.error(request, message)
    return redirect("detalhe", pk=pk)


@perfil("aluno")
def minhas_inscricoes(request):
    bookings = request.user.inscricoes.select_related("sessao__disciplina", "sessao__professor")
    return render(request, "explicacoes/inscricoes.html", {"inscricoes": bookings})


@perfil("aluno")
def cancelar_inscricao(request, pk):
    booking = get_object_or_404(Inscricao.objects.select_related("sessao__disciplina"), pk=pk, aluno=request.user)
    if request.method == "POST":
        try:
            changed = services.cancelar_inscricao(request.user, pk)
            messages.success(request, "Inscrição cancelada. A vaga ficou disponível." if changed else "Esta inscrição já estava cancelada.")
        except ValidationError as exc:
            for message in exc.messages:
                messages.error(request, message)
        return redirect("minhas_inscricoes")
    return render(request, "explicacoes/confirmar.html", {
        "titulo": "Cancelar a tua inscrição?", "texto": str(booking.sessao),
        "descricao": "A tua vaga ficará disponível para outro aluno.",
        "voltar": reverse("minhas_inscricoes"), "botao": "Sim, cancelar inscrição",
    })


@perfil("professor")
def sessoes_professor(request):
    sessions = request.user.sessoes_lecionadas.select_related("disciplina").prefetch_related("inscricoes__aluno")
    return render(request, "explicacoes/professor.html", {"sessoes": sessions})


@perfil("professor")
def disponibilidades(request, pk=None):
    instance = get_object_or_404(Disponibilidade, pk=pk, professor=request.user) if pk else None
    initial = {field: getattr(instance, field) for field in ["dia_semana", "hora_inicio", "hora_fim"]} if instance else None
    form = DisponibilidadeForm(request.POST or None, initial=initial)
    if request.method == "POST" and form.is_valid():
        try:
            services.guardar_disponibilidade(request.user, disponibilidade_id=pk, **form.cleaned_data)
            messages.success(request, "Disponibilidade guardada.")
            return redirect("disponibilidades")
        except ValidationError as exc:
            erros_formulario(form, exc)
    return render(request, "explicacoes/disponibilidades.html", {
        "form": form, "intervalos": request.user.disponibilidades.all(), "a_editar": instance,
    })


@perfil("professor")
def apagar_disponibilidade(request, pk):
    interval = get_object_or_404(Disponibilidade, pk=pk, professor=request.user)
    if request.method == "POST":
        try:
            services.apagar_disponibilidade(request.user, pk)
            messages.success(request, "Intervalo removido.")
        except ValidationError as exc:
            for message in exc.messages:
                messages.error(request, message)
        return redirect("disponibilidades")
    return render(request, "explicacoes/confirmar.html", {
        "titulo": "Remover disponibilidade?", "texto": str(interval),
        "descricao": "O intervalo só será removido se não for necessário para sessões futuras.",
        "voltar": reverse("disponibilidades"), "botao": "Remover intervalo",
    })


@perfil("administrador")
def gestao_sessoes(request):
    sessions = Sessao.objects.select_related("disciplina", "professor").annotate(
        total_ativos=Count("inscricoes", filter=Q(inscricoes__estado="ativa")))
    return render(request, "explicacoes/gestao.html", {"sessoes": sessions})


@perfil("administrador")
def formulario_sessao(request, pk=None):
    instance = get_object_or_404(Sessao, pk=pk) if pk else None
    initial = None
    if instance:
        local = timezone.localtime(instance.inicio)
        initial = {"disciplina": instance.disciplina_id, "professor": instance.professor_id, "data": local.date(), "hora": local.strftime("%H:%M")}
    form = SessaoForm(request.POST or None, initial=initial)
    if request.method == "POST" and form.is_valid():
        try:
            services.guardar_sessao(request.user, form.cleaned_data["disciplina"], form.cleaned_data["professor"], form.inicio(), sessao_id=pk)
            messages.success(request, "Sessão guardada no plano semanal.")
            return redirect("gestao_sessoes")
        except ValidationError as exc:
            erros_formulario(form, exc)
    return render(request, "explicacoes/formulario.html", {
        "form": form, "titulo": "Editar sessão" if instance else "Nova sessão",
        "descricao": "Cada sessão dura uma hora e tem três lugares. O professor deve ter disponibilidade e lecionar a disciplina escolhida.",
        "voltar": reverse("gestao_sessoes"), "botao": "Guardar sessão",
    })


@perfil("administrador")
def cancelar_sessao(request, pk):
    session = get_object_or_404(Sessao.objects.select_related("disciplina"), pk=pk)
    form = MotivoForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            services.cancelar_sessao(request.user, pk, form.cleaned_data["motivo"])
            messages.success(request, "Sessão cancelada. Os alunos e o professor têm um aviso no site.")
            return redirect("gestao_sessoes")
        except ValidationError as exc:
            erros_formulario(form, exc)
    return render(request, "explicacoes/formulario.html", {
        "form": form, "titulo": "Cancelar sessão", "descricao": str(session),
        "voltar": reverse("gestao_sessoes"), "botao": "Confirmar cancelamento", "perigo": True,
    })


@perfil("administrador")
def aviso(request, pk):
    session = get_object_or_404(Sessao.objects.select_related("disciplina", "professor"), pk=pk)
    recipients = list(session.inscricoes.filter(estado="ativa").select_related("aluno"))
    names = [i.aluno.nome for i in recipients] + [session.professor.nome]
    form = AvisoForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        services.enviar_aviso(request.user, pk, form.cleaned_data["mensagem"])
        messages.success(request, "Aviso guardado nas notificações dos destinatários.")
        return redirect("gestao_sessoes")
    return render(request, "explicacoes/formulario.html", {
        "form": form, "titulo": "Enviar aviso", "descricao": str(session),
        "nota": "Destinatários: " + ", ".join(names) + ". O aviso fica dentro do site; não é enviado por email.",
        "voltar": reverse("gestao_sessoes"), "botao": "Confirmar e enviar aviso",
    })


@login_required
def notificacoes(request):
    return render(request, "explicacoes/notificacoes.html", {"notificacoes": request.user.notificacoes.select_related("sessao__disciplina")})


@login_required
@require_POST
def ler_notificacao(request, pk):
    notification = get_object_or_404(Notificacao, pk=pk, destinatario=request.user)
    if not notification.lida_em:
        notification.lida_em = timezone.now()
        notification.save(update_fields=["lida_em"])
    return redirect("notificacoes")

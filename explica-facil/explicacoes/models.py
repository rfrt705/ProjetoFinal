"""As sete entidades descritas na documentação do projeto."""
from datetime import timedelta
from django.conf import settings
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


DIAS = [(0, "Segunda-feira"), (1, "Terça-feira"), (2, "Quarta-feira"),
        (3, "Quinta-feira"), (4, "Sexta-feira"), (5, "Sábado"), (6, "Domingo")]


class UtilizadorManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("O email é obrigatório.")
        user = self.model(email=email.strip().lower(), **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.update(is_superuser=True, is_staff=True, papel="administrador")
        return self.create_user(email, password, **extra_fields)


class Utilizador(AbstractUser):
    class Papel(models.TextChoices):
        ALUNO = "aluno", "Aluno"
        PROFESSOR = "professor", "Professor"
        ADMIN = "administrador", "Administrador"

    username = None
    email = models.EmailField("email", unique=True)
    first_name = models.CharField("nome completo", max_length=150)
    papel = models.CharField("perfil", max_length=20, choices=Papel.choices, default=Papel.ALUNO)
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name"]
    objects = UtilizadorManager()

    class Meta:
        verbose_name = "utilizador"
        verbose_name_plural = "utilizadores"
        ordering = ["first_name", "email"]

    @property
    def nome(self):
        return self.first_name or self.email

    @property
    def administrador(self):
        return self.is_superuser or self.papel == self.Papel.ADMIN

    def clean(self):
        super().clean()
        self.email = self.email.strip().lower()
        if self.pk:
            old = type(self).objects.get(pk=self.pk)
            changing = old.papel != self.papel or (old.is_active and not self.is_active)
            if changing and (self.inscricoes.filter(estado="ativa", sessao__inicio__gt=timezone.now(), sessao__estado="agendada").exists()
                             or self.sessoes_lecionadas.filter(estado="agendada", inicio__gt=timezone.now()).exists()):
                raise ValidationError("Resolve primeiro as inscrições ou sessões futuras deste utilizador.")

    def save(self, *args, **kwargs):
        self.email = self.email.strip().lower()
        self.is_staff = self.administrador
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nome


class Disciplina(models.Model):
    nome = models.CharField(max_length=80, unique=True)
    ativa = models.BooleanField(default=True)

    class Meta:
        ordering = ["nome"]

    def clean(self):
        if self.pk and not self.ativa and self.sessoes.filter(estado="agendada", inicio__gt=timezone.now()).exists():
            raise ValidationError("A disciplina tem sessões futuras. Resolve-as antes de a desativar.")

    def __str__(self):
        return self.nome


class ProfessorDisciplina(models.Model):
    professor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
                                  related_name="disciplinas_lecionadas", limit_choices_to={"papel": "professor"})
    disciplina = models.ForeignKey(Disciplina, on_delete=models.PROTECT, related_name="professores_associados")

    class Meta:
        verbose_name = "associação de professor e disciplina"
        verbose_name_plural = "associações de professores e disciplinas"
        constraints = [models.UniqueConstraint(fields=["professor", "disciplina"], name="professor_disciplina_unicos")]

    def clean(self):
        if self.professor_id and self.professor.papel != "professor":
            raise ValidationError("O utilizador escolhido deve ter o perfil de professor.")

    def __str__(self):
        return f"{self.professor} · {self.disciplina}"


class Disponibilidade(models.Model):
    professor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="disponibilidades")
    dia_semana = models.PositiveSmallIntegerField(choices=DIAS)
    hora_inicio = models.TimeField("início")
    hora_fim = models.TimeField("fim")

    class Meta:
        ordering = ["dia_semana", "hora_inicio"]
        verbose_name_plural = "disponibilidades"
        constraints = [
            models.CheckConstraint(condition=models.Q(hora_fim__gt=models.F("hora_inicio")), name="disponibilidade_intervalo_valido"),
            models.CheckConstraint(condition=models.Q(dia_semana__gte=0, dia_semana__lte=6), name="dia_semana_valido"),
        ]

    def clean(self):
        if not self.professor_id or not self.hora_inicio or not self.hora_fim:
            return
        if self.professor.papel != "professor":
            raise ValidationError("Só um professor pode ter disponibilidade.")
        if self.hora_fim <= self.hora_inicio:
            raise ValidationError("A hora de fim deve ser posterior à hora de início.")
        others = type(self).objects.filter(professor_id=self.professor_id).exclude(pk=self.pk)
        if others.filter(dia_semana=self.dia_semana, hora_inicio__lt=self.hora_fim, hora_fim__gt=self.hora_inicio).exists():
            raise ValidationError("Este intervalo sobrepõe-se a outra disponibilidade.")
        if self.pk:
            intervals = list(others) + [self]
            for session in self.professor.sessoes_lecionadas.filter(estado="agendada", inicio__gt=timezone.now()):
                if not any(interval.abrange(session.inicio, session.fim) for interval in intervals):
                    raise ValidationError("Esta alteração deixa uma sessão futura sem disponibilidade.")

    def abrange(self, inicio, fim):
        start, end = timezone.localtime(inicio), timezone.localtime(fim)
        return (start.date() == end.date() and start.weekday() == self.dia_semana
                and self.hora_inicio <= start.time() and end.time() <= self.hora_fim)

    def __str__(self):
        return f"{self.get_dia_semana_display()} · {self.hora_inicio:%H:%M}–{self.hora_fim:%H:%M}"


class Sessao(models.Model):
    class Estado(models.TextChoices):
        AGENDADA = "agendada", "Agendada"
        CANCELADA = "cancelada", "Cancelada"

    professor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="sessoes_lecionadas")
    disciplina = models.ForeignKey(Disciplina, on_delete=models.PROTECT, related_name="sessoes")
    inicio = models.DateTimeField("início")
    fim = models.DateTimeField()
    estado = models.CharField(max_length=12, choices=Estado.choices, default=Estado.AGENDADA)
    motivo_cancelamento = models.CharField(max_length=500, blank=True)
    criada_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["inicio", "disciplina__nome"]
        verbose_name = "sessão"
        verbose_name_plural = "sessões"
        indexes = [models.Index(fields=["professor", "inicio", "estado"])]
        constraints = [models.CheckConstraint(condition=models.Q(fim__gt=models.F("inicio")), name="sessao_intervalo_valido")]

    def clean(self):
        if not self.inicio or not self.professor_id or not self.disciplina_id:
            return
        self.fim = self.inicio + timedelta(hours=1)
        if self.inicio <= timezone.now():
            raise ValidationError("Escolhe uma data e hora futuras.")
        local = timezone.localtime(self.inicio)
        if local.weekday() not in settings.ALLOWED_WEEKDAYS or local.strftime("%H:%M") not in settings.SESSION_START_TIMES or local.second or local.microsecond:
            raise ValidationError("Escolhe um dos horários fixos e um dia de funcionamento autorizados.")
        if self.professor.papel != "professor" or not self.professor.is_active:
            raise ValidationError("Escolhe um professor ativo.")
        if not self.disciplina.ativa or not ProfessorDisciplina.objects.filter(professor_id=self.professor_id, disciplina_id=self.disciplina_id).exists():
            raise ValidationError("O professor não está associado a esta disciplina ativa.")
        if not any(d.abrange(self.inicio, self.fim) for d in self.professor.disponibilidades.all()):
            raise ValidationError("A sessão não cabe na disponibilidade do professor.")
        if type(self).objects.filter(professor_id=self.professor_id, estado="agendada", inicio__lt=self.fim, fim__gt=self.inicio).exclude(pk=self.pk).exists():
            raise ValidationError("O professor já tem uma sessão neste intervalo.")

    @property
    def ocupacao(self):
        if hasattr(self, "total_ativos"):
            return self.total_ativos
        return self.inscricoes.filter(estado="ativa").count()

    @property
    def vagas(self):
        return max(0, settings.CAPACIDADE_SESSAO - self.ocupacao)

    @property
    def futura(self):
        return self.inicio > timezone.now()

    @property
    def cor(self):
        if self.estado == "cancelada" or self.ocupacao == 0:
            return "cinzento"
        return "vermelho" if self.ocupacao >= settings.CAPACIDADE_SESSAO else "verde"

    @property
    def etiqueta(self):
        if self.estado == "cancelada":
            return "Cancelada"
        if self.ocupacao == 0:
            return "Sem alunos · com vagas"
        if self.vagas == 0:
            return "Completa · sem vagas"
        return f"Mínimo atingido · {self.vagas} {'vaga' if self.vagas == 1 else 'vagas'}"

    def __str__(self):
        return f"{self.disciplina} · {timezone.localtime(self.inicio):%d/%m/%Y %H:%M}"


class Inscricao(models.Model):
    class Estado(models.TextChoices):
        ATIVA = "ativa", "Ativa"
        CANCELADA = "cancelada", "Cancelada"

    aluno = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="inscricoes")
    sessao = models.ForeignKey(Sessao, on_delete=models.PROTECT, related_name="inscricoes")
    estado = models.CharField(max_length=10, choices=Estado.choices, default=Estado.ATIVA)
    criada_em = models.DateTimeField(auto_now_add=True)
    atualizada_em = models.DateTimeField(auto_now=True)
    cancelada_em = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "inscrição"
        verbose_name_plural = "inscrições"
        ordering = ["sessao__inicio"]
        constraints = [models.UniqueConstraint(fields=["aluno", "sessao"], name="aluno_sessao_unicos")]

    def __str__(self):
        return f"{self.aluno} · {self.sessao}"


class Notificacao(models.Model):
    destinatario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="notificacoes")
    sessao = models.ForeignKey(Sessao, null=True, blank=True, on_delete=models.PROTECT)
    tipo = models.CharField(max_length=30)
    mensagem = models.TextField()
    criada_em = models.DateTimeField(auto_now_add=True)
    lida_em = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-criada_em"]
        verbose_name = "notificação"
        verbose_name_plural = "notificações"

    def __str__(self):
        return f"{self.destinatario} · {self.tipo}"

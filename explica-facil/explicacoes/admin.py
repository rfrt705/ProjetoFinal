from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.core.exceptions import ValidationError
from django.db import transaction
from django.forms.models import BaseInlineFormSet
from django.utils import timezone
from .forms import AlterarUtilizadorAdminForm, CriarUtilizadorAdminForm
from .models import Disciplina, Disponibilidade, Inscricao, Notificacao, ProfessorDisciplina, Sessao, Utilizador


class PermissoesGestao:
    def has_module_permission(self, request):
        return request.user.administrador

    def has_view_permission(self, request, obj=None):
        return request.user.administrador

    def has_add_permission(self, request):
        return request.user.administrador

    def has_change_permission(self, request, obj=None):
        return request.user.administrador

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Utilizador)
class UtilizadorAdmin(PermissoesGestao, UserAdmin):
    form = AlterarUtilizadorAdminForm
    add_form = CriarUtilizadorAdminForm
    ordering = ["first_name"]
    list_display = ["first_name", "email", "papel", "is_active"]
    list_filter = ["papel", "is_active"]
    search_fields = ["first_name", "email"]
    fieldsets = ((None, {"fields": ("email", "first_name", "password", "papel", "is_active")}),)
    add_fieldsets = ((None, {"classes": ("wide",), "fields": ("email", "first_name", "papel", "password1", "password2", "is_active")}),)
    filter_horizontal = ()

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs if request.user.is_superuser else qs.filter(is_superuser=False)

    def save_model(self, request, obj, form, change):
        with transaction.atomic():
            if change:
                Utilizador.objects.select_for_update().get(pk=obj.pk)
                obj.full_clean(exclude=["password"])
            super().save_model(request, obj, form, change)


class AssociacoesFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        for form in self.forms:
            if not hasattr(form, "cleaned_data") or form.errors or not form.instance.pk:
                continue
            old = ProfessorDisciplina.objects.get(pk=form.instance.pk)
            changed = form.cleaned_data.get("DELETE") or old.professor_id != form.cleaned_data.get("professor", old.professor).pk
            if changed and Sessao.objects.filter(professor_id=old.professor_id, disciplina_id=old.disciplina_id,
                                                estado="agendada", inicio__gt=timezone.now()).exists():
                raise ValidationError("Esta associação tem sessões futuras. Resolve essas sessões antes de a remover ou alterar.")

    def save(self, commit=True):
        with transaction.atomic():
            ids = set(self.instance.professores_associados.values_list("professor_id", flat=True))
            for form in self.forms:
                if hasattr(form, "cleaned_data") and form.cleaned_data.get("professor"):
                    ids.add(form.cleaned_data["professor"].pk)
            list(Utilizador.objects.select_for_update().filter(pk__in=ids).order_by("pk"))
            self.clean()
            return super().save(commit)


class ProfessorInline(admin.TabularInline):
    model = ProfessorDisciplina
    formset = AssociacoesFormSet
    extra = 1

    def has_add_permission(self, request, obj=None): return request.user.administrador
    def has_change_permission(self, request, obj=None): return request.user.administrador
    def has_delete_permission(self, request, obj=None): return request.user.administrador
    def has_view_permission(self, request, obj=None): return request.user.administrador


@admin.register(Disciplina)
class DisciplinaAdmin(PermissoesGestao, admin.ModelAdmin):
    list_display = ["nome", "ativa"]
    search_fields = ["nome"]
    inlines = [ProfessorInline]

    def save_model(self, request, obj, form, change):
        with transaction.atomic():
            if change:
                Disciplina.objects.select_for_update().get(pk=obj.pk)
                obj.full_clean()
            super().save_model(request, obj, form, change)


class ConsultaAdmin(PermissoesGestao, admin.ModelAdmin):
    """As alterações de sessões passam pelos serviços, não por este painel."""
    def has_add_permission(self, request): return False
    def has_change_permission(self, request, obj=None): return False
    def get_readonly_fields(self, request, obj=None):
        return [field.name for field in self.model._meta.fields]


@admin.register(Sessao)
class SessaoAdmin(ConsultaAdmin):
    list_display = ["disciplina", "professor", "inicio", "fim", "estado"]
    list_filter = ["estado", "disciplina"]


@admin.register(Inscricao)
class InscricaoAdmin(ConsultaAdmin):
    list_display = ["aluno", "sessao", "estado"]
    list_filter = ["estado"]


@admin.register(Disponibilidade)
class DisponibilidadeAdmin(ConsultaAdmin):
    list_display = ["professor", "dia_semana", "hora_inicio", "hora_fim"]


@admin.register(Notificacao)
class NotificacaoAdmin(ConsultaAdmin):
    list_display = ["destinatario", "tipo", "criada_em", "lida_em"]

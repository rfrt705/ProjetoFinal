from datetime import datetime, time
from django import forms
from django.conf import settings
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm, UserChangeForm
from django.utils import timezone
from .models import DIAS, Disciplina, Utilizador


class LoginEmailForm(AuthenticationForm):
    username = forms.EmailField(label="Email", widget=forms.EmailInput(attrs={"autofocus": True, "autocomplete": "email"}))

    def clean_username(self):
        return self.cleaned_data["username"].strip().lower()


class RegistoForm(UserCreationForm):
    class Meta:
        model = Utilizador
        fields = ["first_name", "email", "password1", "password2"]
        labels = {"first_name": "Nome completo", "email": "Email"}

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if Utilizador.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Já existe uma conta com este email.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.papel = "aluno"
        if commit:
            user.save()
        return user


class CriarUtilizadorAdminForm(UserCreationForm):
    class Meta:
        model = Utilizador
        fields = ["email", "first_name", "papel", "is_active"]


class AlterarUtilizadorAdminForm(UserChangeForm):
    class Meta:
        model = Utilizador
        fields = "__all__"


class SessaoForm(forms.Form):
    disciplina = forms.ModelChoiceField(queryset=Disciplina.objects.none())
    professor = forms.ModelChoiceField(queryset=Utilizador.objects.none())
    data = forms.DateField(label="Data", widget=forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"))
    hora = forms.ChoiceField(label="Hora de início")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["disciplina"].queryset = Disciplina.objects.filter(ativa=True)
        self.fields["professor"].queryset = Utilizador.objects.filter(papel="professor", is_active=True)
        self.fields["hora"].choices = [(slot, slot) for slot in settings.SESSION_START_TIMES]

    def inicio(self):
        naive = datetime.combine(self.cleaned_data["data"], time.fromisoformat(self.cleaned_data["hora"]))
        return timezone.make_aware(naive, timezone.get_current_timezone())


class DisponibilidadeForm(forms.Form):
    dia_semana = forms.TypedChoiceField(label="Dia da semana", choices=DIAS, coerce=int)
    hora_inicio = forms.TimeField(label="Hora de início", widget=forms.TimeInput(attrs={"type": "time"}, format="%H:%M"))
    hora_fim = forms.TimeField(label="Hora de fim", widget=forms.TimeInput(attrs={"type": "time"}, format="%H:%M"))


class MotivoForm(forms.Form):
    motivo = forms.CharField(label="Motivo do cancelamento", max_length=500, widget=forms.Textarea(attrs={"rows": 3}))


class AvisoForm(forms.Form):
    mensagem = forms.CharField(label="Mensagem", max_length=1000, widget=forms.Textarea(attrs={"rows": 5}))

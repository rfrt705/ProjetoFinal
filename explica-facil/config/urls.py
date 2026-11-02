from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path
from explicacoes.forms import LoginEmailForm

urlpatterns = [
    path("administracao/", admin.site.urls),
    path("entrar/", auth_views.LoginView.as_view(template_name="registration/login.html", authentication_form=LoginEmailForm), name="login"),
    path("sair/", auth_views.LogoutView.as_view(), name="logout"),
    path("", include("explicacoes.urls")),
]
admin.site.site_header = "Explica Fácil"
admin.site.site_title = "Gestão do Explica Fácil"
admin.site.index_title = "Utilizadores e disciplinas"

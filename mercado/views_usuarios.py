"""Login, troca de senha e gestão de usuários.

Todas as telas do app exigem login (``LoginRequiredMiddleware`` no settings);
as de ``/usuarios/`` exigem também o papel de administrador
(``exigir_administrador``). Usuário desativado não entra, mas o histórico
dele continua no banco: por isso não existe "excluir".
"""

from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import SetPasswordForm
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView, LogoutView, PasswordChangeView
from django.contrib.messages.views import SuccessMessageMixin
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.decorators.http import require_POST

from .autorizacao import exigir_administrador
from .forms_usuarios import FormularioNovoUsuario


class TelaDeLogin(LoginView):
    """``GET/POST /entrar/``. Quem já está logado vai direto ao painel."""

    template_name = "login.html"
    redirect_authenticated_user = True


class Sair(LogoutView):
    """``POST /sair/``. GET não encerra a sessão (proteção contra link malicioso)."""

    next_page = reverse_lazy("entrar")


class TrocarMinhaSenha(SuccessMessageMixin, PasswordChangeView):
    """``/senha/``: qualquer usuário troca a própria senha, informando a atual."""

    template_name = "senha_propria.html"
    success_url = reverse_lazy("painel")
    success_message = "Senha alterada."


@exigir_administrador
def listar_usuarios(request: HttpRequest) -> HttpResponse:
    """``GET /usuarios/``: lista com papel, situação e ações.

    Exemplo: link "Usuários" no cabeçalho, visível só para administradores.
    """
    usuarios = User.objects.order_by("username")
    return render(request, "usuarios/lista.html", {"usuarios": usuarios})


@exigir_administrador
def criar_usuario(request: HttpRequest) -> HttpResponse:
    """``GET/POST /usuarios/novo/``: cadastro de usuário pelo administrador."""
    formulario = FormularioNovoUsuario(request.POST or None)
    if request.method == "POST" and formulario.is_valid():
        usuario = formulario.save()
        messages.success(request, f"Usuário {usuario.username} criado.")
        return redirect("usuarios")
    return render(request, "usuarios/novo.html", {"formulario": formulario})


@exigir_administrador
def definir_senha_usuario(request: HttpRequest, usuario_id: int) -> HttpResponse:
    """``GET/POST /usuarios/<id>/senha/``: administrador define nova senha sem saber a atual."""
    usuario = get_object_or_404(User, pk=usuario_id)
    formulario = SetPasswordForm(usuario, request.POST or None)
    if request.method == "POST" and formulario.is_valid():
        formulario.save()
        # Trocar a própria senha invalida a sessão; isto mantém o admin logado.
        if usuario == request.user:
            update_session_auth_hash(request, usuario)
        messages.success(request, f"Senha de {usuario.username} alterada.")
        return redirect("usuarios")
    contexto = {"formulario": formulario, "usuario_alvo": usuario}
    return render(request, "usuarios/senha.html", contexto)


@exigir_administrador
@require_POST
def alternar_ativo_usuario(request: HttpRequest, usuario_id: int) -> HttpResponse:
    """``POST /usuarios/<id>/ativo/``: desativa ou reativa o usuário."""
    usuario = get_object_or_404(User, pk=usuario_id)
    if usuario == request.user:
        messages.error(request, "Você não pode desativar a si mesmo.")
        return redirect("usuarios")
    usuario.is_active = not usuario.is_active
    usuario.save(update_fields=["is_active"])
    situacao = "reativado" if usuario.is_active else "desativado"
    messages.success(request, f"Usuário {usuario.username} {situacao}.")
    return redirect("usuarios")

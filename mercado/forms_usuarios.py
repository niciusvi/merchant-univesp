"""Formulários das telas de usuários.

Reaproveitam os do Django (validação de senha, mensagens em português) e só
acrescentam o que o projeto precisa: o papel de administrador do mercado.
"""

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import PerfilDeAcesso


class FormularioNovoUsuario(UserCreationForm):
    """Cadastro feito pelo administrador: usuário, senha (duas vezes) e papel.

    Exemplo: ``FormularioNovoUsuario(request.POST)``; ``form.save()`` devolve o ``User``
    já com ``PerfilDeAcesso``.
    """

    administrador = forms.BooleanField(
        required=False,
        label="Também é administrador do mercado",
        help_text="Administradores criam usuários e trocam a senha dos outros.",
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username",)

    def save(self, commit: bool = True) -> User:
        """Grava usuário e perfil juntos (sempre persiste; ``commit`` é da assinatura herdada)."""
        usuario = super().save(commit=False)
        # Usuário do mercado nunca ganha poderes do Django: /admin/ é da conta técnica.
        usuario.is_staff = False
        usuario.is_superuser = False
        usuario.save()
        PerfilDeAcesso.objects.create(
            usuario=usuario, administrador=self.cleaned_data["administrador"]
        )
        return usuario

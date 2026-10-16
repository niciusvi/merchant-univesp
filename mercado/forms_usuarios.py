"""Formulários das telas de usuários.

Reaproveitam os do Django (validação de senha, mensagens em português) e só
acrescentam o que o projeto precisa: o papel de administrador.
"""

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


class FormularioNovoUsuario(UserCreationForm):
    """Cadastro feito pelo administrador: usuário, senha (duas vezes) e papel.

    Exemplo: ``FormularioNovoUsuario(request.POST)``; ``form.save()`` devolve o ``User``.
    """

    administrador = forms.BooleanField(
        required=False,
        label="Também é administrador",
        help_text="Administradores criam usuários e trocam a senha dos outros.",
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username",)

    def save(self, commit: bool = True) -> User:
        usuario = super().save(commit=False)
        # No Django o papel de administrador é a dupla superuser + staff.
        usuario.is_superuser = self.cleaned_data["administrador"]
        usuario.is_staff = self.cleaned_data["administrador"]
        if commit:
            usuario.save()
        return usuario

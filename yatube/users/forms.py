from django.contrib.auth.forms import UserCreationForm, PasswordResetForm
from django.contrib.auth import get_user_model


User = get_user_model()


class CreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('first_name', 'last_name', 'username', 'email')


class PasswordResetForm(PasswordResetForm):
    class Meta(PasswordResetForm):
        model = User
        # fields = ('current_password', 'new_password', 'new_password_repeat')
        fields = ('email')

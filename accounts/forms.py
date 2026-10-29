from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from members.models import Member

from .models import User


class PendingApprovalAuthenticationForm(AuthenticationForm):
    """Login form that tells self-registered members their account is awaiting approval
    instead of showing the generic "invalid username or password" error."""

    error_messages = {
        **AuthenticationForm.error_messages,
        'pending_approval': (
            'Your account is still awaiting approval by the church administration. '
            'You will be able to sign in once it has been approved.'
        ),
    }

    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if username is not None and password:
            self.user_cache = authenticate(self.request, username=username, password=password)
            if self.user_cache is None:
                if self._is_pending_approval(username, password):
                    raise ValidationError(
                        self.error_messages['pending_approval'],
                        code='pending_approval',
                    )
                raise self.get_invalid_login_error()
            self.confirm_login_allowed(self.user_cache)

        return self.cleaned_data

    @staticmethod
    def _is_pending_approval(username, password):
        try:
            candidate = User._default_manager.get_by_natural_key(username)
        except User.DoesNotExist:
            return False
        return not candidate.is_active and candidate.check_password(password)


class UserRegistrationForm(forms.ModelForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'phone', 'role', 'photo']


class MemberRegistrationForm(forms.Form):
    member_number = forms.CharField(label='Member Number', max_length=20)
    last_name = forms.CharField(label='Last Name', max_length=100)
    username = forms.CharField(label='Username', max_length=150)
    email = forms.EmailField(label='Email', required=True)
    phone = forms.CharField(label='Phone (optional)', max_length=20, required=False)
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Confirm Password', widget=forms.PasswordInput)

    def clean_username(self):
        username = self.cleaned_data['username'].strip()
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError('This username is already taken.')
        return username

    def clean_password1(self):
        password1 = self.cleaned_data.get('password1')
        if password1:
            try:
                validate_password(password1)
            except ValidationError as exc:
                raise forms.ValidationError('; '.join(exc.messages))
        return password1

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 != password2:
            raise forms.ValidationError('The two passwords do not match.')
        return password2

    def clean(self):
        cleaned = super().clean()
        member_number = (cleaned.get('member_number') or '').strip()
        last_name = (cleaned.get('last_name') or '').strip()
        member = Member.objects.filter(member_number__iexact=member_number).first()
        if not member:
            self.add_error('member_number', 'No member found with this number. Please contact the church office.')
        elif member.last_name.strip().lower() != last_name.lower():
            self.add_error('last_name', 'The last name does not match our records.')
        elif member.user_id:
            self.add_error('member_number', 'An account already exists for this member.')
        else:
            self.member = member
        return cleaned


class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone', 'photo', 'role']


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone', 'photo']

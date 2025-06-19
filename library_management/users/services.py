from django.contrib.auth.tokens import default_token_generator
from django.shortcuts import get_object_or_404
from django.utils.encoding import force_bytes
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from django.utils.http import urlsafe_base64_encode

from library_management.users.models import User


class UserService:
    def generate_password_reset_link(self, user, base_url):
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        return f"{base_url}?uid={uid}&token={token}"

    def get_user_by_uid(self, uid):
        user_id = force_str(urlsafe_base64_decode(uid))
        return get_object_or_404(User, pk=user_id)

    def validate_password_reset_token(self, user, token):
        return default_token_generator.check_token(user, token)

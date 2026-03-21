from api.models import User
from rest_framework_simplejwt.tokens import RefreshToken


def register_user(validated_data):
    user = User.objects.create_user(
        username=validated_data['username'],
        email=validated_data['email'],
        password=validated_data['password']
    )
    return user
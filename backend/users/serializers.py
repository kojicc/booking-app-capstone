# users/serializers.py
from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from .models import User

class UserSerializer(serializers.ModelSerializer):
    username = serializers.CharField(read_only=True, allow_null=True)
    email = serializers.EmailField(required=True, validators=[UniqueValidator(queryset=User.objects.all())])

    class Meta:
        model = User
        # Expose username (read-only), email (primary identifier) and other fields
        fields = ["id", "google_id", "username", "email", "role", "first_name", "last_name", "password"]
        extra_kwargs = {"password": {"write_only": True}}

    def create(self, validated_data):
        # Ensure username is not set from input and remains NULL in DB
        validated_data.pop('username', None)
        password = validated_data.pop("password", None)

        user = User(**validated_data)
        # Explicitly null username to satisfy the requirement
        user.username = None
        if password:
            user.set_password(password)
        user.save()
        return user

from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import User


class RegisterSerializer(serializers.ModelSerializer):
    password  = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True, label='Confirm password')

    class Meta:
        model  = User
        fields = ['email', 'username', 'first_name', 'last_name', 'phone', 'role', 'password', 'password2']
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name':  {'required': True},
            'username':   {'required': False},   # auto-generated if not provided
            'phone':      {'required': False},
            'role':       {'required': False},
        }

    def validate(self, attrs):
        if attrs['password'] != attrs.pop('password2'):
            raise serializers.ValidationError({'password': 'Passwords do not match.'})

        # Auto-generate username if not provided
        if not attrs.get('username'):
            base    = attrs['email'].split('@')[0]
            username = base
            counter  = 1
            while User.objects.filter(username=username).exists():
                username = f'{base}{counter}'
                counter += 1
            attrs['username'] = username

        return attrs

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user


class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()

    class Meta:
        model  = User
        fields = ['id', 'email', 'username', 'first_name', 'last_name',
                  'full_name', 'phone', 'role', 'avatar', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']

    def get_full_name(self, obj):
        return obj.get_full_name()


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password])

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Current password is incorrect.')
        return value
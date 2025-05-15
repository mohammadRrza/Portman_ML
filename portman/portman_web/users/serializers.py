from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

from rest_framework import serializers
from dslam.serializers import ResellerSerializer, CitySerializer
from dslam.models import DSLAM, Command
from users.models import *
from khayyam import JalaliDatetime
from django.contrib.contenttypes.models import ContentType
from filemanager.models import File as FileManagerFile
from filemanager.serializers import FileSerializer

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    last_login = serializers.DateTimeField(format='%Y-%m-%d %H:%M:%S', required=False, read_only=True)
    date_joined = serializers.DateTimeField(format='%Y-%m-%d %H:%M:%S', required=False, read_only=True)
    password = serializers.CharField(write_only=True, required=True)
    confirm_password = serializers.CharField(write_only=True, required=True)
    reseller_info = ResellerSerializer(source='reseller', read_only=True)
    image = serializers.SerializerMethodField('get_image')

    def get_image(self, obj):
        files = FileManagerFile.objects.filter(object_id=obj.id, content_type=ContentType.objects.get_for_model(obj)).order_by('-id').first()
        return FileSerializer([files], many=True).data if files else None

    class Meta:
        model = User
        fields = (
            'id', 'username', 'email', 'first_name', 'tel', 'mobile_number',
            'last_name', 'last_login', 'is_active', 'type', 'fa_first_name', 'fa_last_name',
            'date_joined', 'confirm_password', 'password',
            'reseller_info', 'reseller', 'image', 'card_validity_date'
        )

        read_only_fields = ('id', 'date_joined', 'last_login')


    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already exists")
        return value

    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError("Password mismatch")
        del data['confirm_password']
        return data

    def create(self, validated_data):
        user = User.objects.create(**validated_data)
        user.set_password(validated_data['password'])
        user.save()
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            'email', 'first_name', 'last_name', 'fa_first_name', 'fa_last_name', 'username', 'tel', 'reseller', 'mobile_number', 'type', 'is_active',
        )

    def validate_email(self, value):
        if User.objects.filter(email=value).exclude(pk=self.instance.pk).exists():
            raise serializers.ValidationError('Email already exists')
        return value


class ChangePasswordSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)
    new_password = serializers.CharField(write_only=True, required=True)
    confirm_password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = (
            'password', 'new_password', 'confirm_password'
        )

    def validate_password(self, value):
        if not self.instance.check_password(value):
            raise serializers.ValidationError("Invalid password")
        return value

    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError("Password mismatch")
        return data


class UserAuditLogSerializer(serializers.ModelSerializer):
    created_at = serializers.SerializerMethodField('get_created_persian_date')

    def get_created_persian_date(self, obj):
        return JalaliDatetime(obj.created_at).strftime("%Y-%m-%d %H:%M:%S")

    class Meta:
        model = UserAuditLog
        fields = ('username', 'model_name', 'instance_id', 'action', 'description', 'ip', 'created_at')


class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = ('id', 'title', 'codename', 'description')


class PermissionProfileSerializer(serializers.ModelSerializer):
    permissions = serializers.SerializerMethodField(read_only=True, required=False)

    def get_permissions(self, obj):
        permissions = obj.permissionprofilepermission_set.all()
        return [{'id': p.permission.pk, 'name': p.permission.title} for p in permissions]

    class Meta:
        model = PermissionProfile
        fields = ('id', 'name', 'permissions')


class PermissionProfilePermissionSerializer(serializers.ModelSerializer):
    permission_info = PermissionSerializer(source='permission', read_only=True, required=False)
    permission_profile_info = PermissionProfileSerializer(source='permission_profile', read_only=True, required=False)

    class Meta:
        model = PermissionProfilePermission
        fields = ('id', 'permission_profile', 'permission', 'permission_profile_info', 'permission_info')


class UserPermissionProfileSerializer(serializers.ModelSerializer):
    permission_profile_name = serializers.CharField(source='permission_profile.name', read_only=True)

    class Meta:
        model = UserPermissionProfile
        fields = ('id', 'user', 'action', 'is_active', 'permission_profile', 'permission_profile_name')


class PortmanLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = PortmanLog
        fields = '__all__'


class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'email', 'first_name', 'last_name', 'fa_first_name', 'fa_last_name')


class ContactGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactGroup
        fields = '__all__'


class ContactGroupIndexSerializer(serializers.ModelSerializer):
    user_info = ContactSerializer(source='user', read_only=True, required=False)
    group_info = ContactGroupSerializer(source='group', read_only=True, required=False)

    class Meta:
        model = ContactGroupIndex
        fields = '__all__'


class NotifiableUserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ('id', 'first_name', 'last_name', 'email', 'mobile_number')


class ShowNotificationLogSerializer(serializers.ModelSerializer):
    sender_info = NotifiableUserSerializer(source='sender', read_only=True, required=False)
    receiver_info = NotifiableUserSerializer(source='receiver', read_only=True, required=False)

    class Meta:
        model = NotificationLog
        fields = '__all__'


class UserPermissionSerializer(serializers.ModelSerializer):
    permissions = serializers.SerializerMethodField('get_permission_profiles')

    def get_permission_profiles(self, obj):
        dslams_set = set()
        commands_set = set()
        permission_profile_objs = obj.userpermissionprofile_set.all()

        for permission_profile_obj in permission_profile_objs:
            objects = permission_profile_obj.userpermissionprofileobject_set.all()
            for item in objects:
                if item.content_type.model == 'dslam':
                    dslam_obj = DSLAM.objects.filter(pk=item.object_id).first()
                    if dslam_obj:
                        dslam_tpl = (dslam_obj.id, dslam_obj.ip, dslam_obj.name)
                        dslams_set.add(dslam_tpl)
                elif item.content_type.model == 'command':
                    command_obj = Command.objects.filter(pk=item.object_id).first()
                    if command_obj:
                        command_tpl = (command_obj.id, command_obj.text)
                        commands_set.add(command_tpl)

        # Convert the sets back to list of dictionaries (assuming order isn't important).
        dslams = [dict(id=id_, ip=ip, name=name) for id_, ip, name in dslams_set]
        commands = [dict(id=id_, name=name) for id_, name in commands_set]

        return dict(dslams=dslams, commands=commands)

    class Meta:
        model = User
        fields = ('permissions',)


class ProvinceAccessSerializer(serializers.ModelSerializer):
    user_info = serializers.SerializerMethodField(read_only=True, required=False)
    province_info = serializers.SerializerMethodField(read_only=True, required=False)

    class Meta:
        model = ProvinceAccess
        fields = ['id', 'user', 'province', 'access_level', 'scope', 'user_info', 'province_info']

    def get_user_info(self, obj):
        return dict(id=obj.user.id,
                    first_name=obj.user.first_name,
                    last_name=obj.user.last_name,
                    username=obj.user.username,
                    email=obj.user.email)

    def get_province_info(self, obj):
        return dict(id=obj.province.id,
                    name=obj.province.name)


class InstallerSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)
    confirm_password = serializers.CharField(write_only=True, required=True)
    mobile_number = serializers.CharField(required=True)
    image = serializers.SerializerMethodField('get_image')
    city_info = CitySerializer(source="city", read_only=True, required=False)

    def get_image(self, obj):
        files = FileManagerFile.objects.filter(object_id=obj.id,
                                               content_type=ContentType.objects.get_for_model(obj)).order_by(
            '-id').first()
        return FileSerializer([files], many=True).data if files else None

            
    class Meta:
        model = User
        fields = (
            'id', 'username', 'email', 'first_name', 'last_name', 'type',
            'fa_first_name', 'fa_last_name', 'mobile_number', 'image',  'card_validity_date',
            'is_active', 'date_joined', 'confirm_password', 'password', 'city', 'city_info', 'crm_id'
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance:
            self.fields.pop('password', None)
            self.fields.pop('confirm_password', None)

    def validate_email(self, value):
        if self.instance is None:
            if User.objects.filter(email=value).exists():
                raise serializers.ValidationError("Email already exists")
        else:
            if User.objects.exclude(id=self.instance.id).filter(email=value).exists():
                raise serializers.ValidationError("Email already exists")
        return value

    def validate_username(self, value):
        if self.instance is None:
            if User.objects.filter(username=value).exists():
                raise serializers.ValidationError("A user with that username already exists.")
        else:
            if User.objects.exclude(id=self.instance.id).filter(username=value).exists():
                raise serializers.ValidationError("A user with that username already exists.")
        return value

    def validate(self, data):
        if 'password' in data and 'confirm_password' in data:
            if data['password'] != data['confirm_password']:
                raise serializers.ValidationError("Password mismatch")

            try:
                validate_password(data['password'])
            except serializers.ValidationError as e:
                raise serializers.ValidationError({"password": e.messages})

        if 'confirm_password' in data:
            del data['confirm_password']

        return data

    def create(self, validated_data):
        user = User.objects.create(**validated_data)
        user.set_password(validated_data['password'])
        user.save()
        return user
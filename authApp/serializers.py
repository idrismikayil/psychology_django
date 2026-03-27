from rest_framework import serializers
from .models import Contact, ContactInfo, About, Plan, Tag, Blog, SocialLink
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from django.contrib.auth import get_user_model
from psychologyApp.models import Test, Answer, Option 
User = get_user_model()

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # İstəyə görə əlavə məlumat əlavə edə bilərsən
        token['email'] = user.email
        return token

    def validate(self, attrs):
        # email ilə login
        credentials = {
            'email': attrs.get('email'),
            'password': attrs.get('password')
        }
        return super().validate(credentials)
    
class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone_number']

    def update(self, instance, validated_data):
        # Hər sahəni yoxla, boşdursa pass et
        for field in ['first_name', 'last_name', 'email', 'phone_number']:
            value = validated_data.get(field, None)
            if value is not None and str(value).strip() != '':
                setattr(instance, field, value)
        instance.save()
        return instance

class UserUpdatePPSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['image']

        
class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect")
        return value

    def validate_new_password(self, value):
        if len(value) < 6:
            raise serializers.ValidationError("New password must be at least 6 characters")
        return value

class AboutSerializer(serializers.ModelSerializer):
    class Meta:
        model = About
        fields = ['id', 'title', 'miniTitle', 'content']

class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = ['id', 'full_name', 'email', 'subject', 'message', 'created_at']
        read_only_fields = ['id', 'created_at']  # id və tarix client tərəfindən doldurulmayacaq

    # Hamısını tələb olunan etmək
    def validate(self, data):
        for field in ['full_name', 'email', 'subject', 'message']:
            if not data.get(field):
                raise serializers.ValidationError({field: "This field is required."})
        return data
    
class ContactInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactInfo
        fields = ['id', 'location', 'location_url', 'phone', 'email']



 # Test modeli testsApp-da olduğunu fərz edirəm



class OptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Option
        fields = ['id', 'text', 'value']

class AnswerSerializer(serializers.ModelSerializer):
    option = OptionSerializer(read_only=True)

    class Meta:
        model = Answer
        fields = ['id', 'option']

class TestSerializer(serializers.ModelSerializer):
    answers = AnswerSerializer(many=True, read_only=True)
    
    class Meta:
        model = Test
        fields = ['id', 'created_at', 'answers']


class SimpleTestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Test
        fields = ['id', 'created_at','result_values','result']

class UserProfileSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()
    tests = SimpleTestSerializer(many=True, read_only=True)
    reserved_test_count = serializers.SerializerMethodField()
    available_test_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'username', 'first_name', 'last_name', 'email',
            'phone_number', 'tests', 'active_test_count',
            'reserved_test_count', 'available_test_count', 'image'
        ]

    def get_reserved_test_count(self, obj):
        from licenses.models import TestInvitation
        from django.db.models import Sum
        return TestInvitation.objects.filter(
            sender=obj, status='PENDING'
        ).aggregate(total=Sum('credit_count'))['total'] or 0

    def get_available_test_count(self, obj):
        from licenses.models import TestInvitation
        from django.db.models import Sum
        reserved = TestInvitation.objects.filter(
            sender=obj, status='PENDING'
        ).aggregate(total=Sum('credit_count'))['total'] or 0
        return max(0, obj.active_test_count - reserved)

    def get_image(self, obj):
        request = self.context.get('request')
        if obj.image:
            return request.build_absolute_uri(obj.image.url)
        return None

class PlanListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plan
        fields = "__all__"

class TagListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['name']

class BlogListSerializer(serializers.ModelSerializer):
    tags = TagListSerializer(many=True) 
    class Meta:
        model = Blog
        fields = "__all__"




class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['email', 'password', 'phone_number']

    def create(self, validated_data):
        # User yaradılır, amma is_active=False edilir (Email təsdiqlənənə qədər)
        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            phone_number=validated_data.get('phone_number', ''),
            is_active=False  # Vacib: Kod təsdiqlənənə qədər deaktiv qalır
        )
        return user

# Təsdiq (OTP) Serializeri
class VerifyEmailSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(max_length=6)

class ResendCodeSerializer(serializers.Serializer):
    email = serializers.EmailField()

class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Bu email ilə istifadəçi tapılmadı.")
        return value

class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(max_length=6)
    new_password = serializers.CharField(min_length=6)

    def validate(self, data):
        email = data.get('email')
        code = data.get('code')
        
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError({"email": "İstifadəçi tapılmadı."})

        # Kodu yoxlayırıq
        from .models import VerificationCode
        verification = VerificationCode.objects.filter(user=user, code=code).last()
        
        if not verification or not verification.is_valid():
             raise serializers.ValidationError({"code": "Kod yanlışdır və ya vaxtı bitib."})
        
        return data

    
class SocialLinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = SocialLink
        fields = ['id', 'title', 'image','url']
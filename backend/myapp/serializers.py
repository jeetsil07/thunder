from rest_framework import serializers
from .models import Post, PostCategory, PostComments, UsersAccount
import uuid
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from django.conf import settings

def validate_image(image):
    if image.size > 1 * 1024 * 1024:
        raise serializers.ValidationError("The maximum file size that can be uploaded is 1MB.")
    if not image.name.lower().endswith(('.png', '.jpg', '.jpeg')):
        raise serializers.ValidationError("Unsupported file extension. Only PNG, JPG, and JPEG are allowed.")
    
class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    image = serializers.ImageField(required=False, allow_null=True)  # Optional image field

    class Meta:
        model = UsersAccount
        fields = '__all__'
    def get_image(self, obj):
        request = self.context.get('request')
        if obj.image:
            image_url = obj.image.url
            if request is not None:
                return request.build_absolute_uri(image_url)
            return f"{settings.MEDIA_URL}{image_url}"
        return None
    def create(self, validated_data):
        password = validated_data.pop('password')  # Extracts the password from the validated data
        user = UsersAccount.objects.create_user(**validated_data, password=password)  # Calls the create_user method in the manager to create the user
        return user
    
    def update(self, instance, validated_data):
        # Update user attributes except password
        for attr, value in validated_data.items():
            if attr != 'password':
                setattr(instance, attr, value)
        
        # Update password if provided
        password = validated_data.get('password')
        if password:
            instance.set_password(password)

        instance.save()
        return instance
        
    def validate_image(self, value):
        validate_image(value)  # Reuse the validate_image function for custom validation
        return value
    
class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()
    image = serializers.ImageField(read_only=True)  # Read-only image field for login response

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
        
        user = authenticate(email=email, password=password)  # Authenticate the user with email and password
        if user is None:
            raise serializers.ValidationError('Invalid email or password.')  # Raise error if authentication fails

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        tokens = {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                }

        return {
            'tokens': tokens,
            'user': user,
        }
    
class PostCategorySerializer(serializers.ModelSerializer):
    # user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    user = UserRegistrationSerializer(read_only=True)
    class Meta:
        model = PostCategory
        fields = '__all__'
class PostCommentSerializer(serializers.ModelSerializer):
    parent_comment = serializers.PrimaryKeyRelatedField(
        queryset=PostComments.objects.all(), 
        allow_null=True,
        required=False
    )
    
    related_post = serializers.PrimaryKeyRelatedField(
        queryset=Post.objects.all(), 
        required=True
    )

    # Use the nested UserRegistrationSerializer to return full user details
    user = UserRegistrationSerializer(read_only=True)
    
    children = serializers.SerializerMethodField()

    class Meta:
        model = PostComments
        fields = '__all__'
        
    comment_id = serializers.UUIDField(default=uuid.uuid4)
    comment = serializers.CharField()
    comment_likes = serializers.IntegerField(default=0)

    def get_children(self, obj):
        if obj.children.exists():
            return PostCommentSerializer(obj.children.all(), many=True, context=self.context).data
        return []

    def create(self, validated_data):
        return PostComments.objects.create(**validated_data)

    def update(self, instance, validated_data):
        instance.parent_comment = validated_data.get('parent_comment', instance.parent_comment)
        instance.comment = validated_data.get('comment', instance.comment)
        instance.comment_likes = validated_data.get('comment_likes', instance.comment_likes)
        instance.related_post = validated_data.get('related_post', instance.related_post)
        instance.save()
        return instance
    
class PostSerializer(serializers.ModelSerializer):
    post_category = serializers.PrimaryKeyRelatedField(queryset=PostCategory.objects.all(), required=True)
    user = UserRegistrationSerializer(read_only=True)  # Nested UserRegistrationSerializer
    
    class Meta:
        model = Post
        fields = '__all__'  # Include all fields in the response
    
    title = serializers.CharField(required=True, max_length=200)
    description = serializers.CharField(required=True)
    image = serializers.ImageField(required=True)
    post_ratings = serializers.IntegerField(default=0)
    rating_times = serializers.IntegerField(default=0)
    
     # Validate description field
    def validate_description(self, value):
        if not value or value.strip() == "":
            raise serializers.ValidationError("Description is required and cannot be empty.")
        if len(value) < 100:
            raise serializers.ValidationError("Description does not have enough content.")
        return value
    
    def validate_title(self, value):
        if len(value) > 200:
            raise serializers.ValidationError("Title length cannot exceed 50 characters.")
        return value

    def validate_image(self, value):
        if value is None:
            raise serializers.ValidationError("This field is required.")
        validate_image(value)
        return value
    
class MemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = UsersAccount
        fields = ['first_name', 'last_name', 'bio', 'image']  # Fields you want to expose   

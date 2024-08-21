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
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    class Meta:
        model = PostCategory
        fields = '__all__'
class PostCommentSerializer(serializers.ModelSerializer):
    # Define parent_comment as a related field
    parent_comment = serializers.PrimaryKeyRelatedField(
        queryset=PostComments.objects.all(), 
        allow_null=True,  # Allow null if the comment is a root comment
        required=False
    )
    
    # Define related_post as a related field
    related_post = serializers.PrimaryKeyRelatedField(
        queryset=Post.objects.all(), 
        required=True
    )

    # Define user_id as a related field
    user = serializers.PrimaryKeyRelatedField(queryset=UsersAccount.objects.all(), required=False)

    
    # Method field for nested children comments
    children = serializers.SerializerMethodField()
    
    class Meta:
        model = PostComments
        fields = '__all__'

        
    comment_id = serializers.UUIDField(default=uuid.uuid4)   
    comment = serializers.CharField()    
    comment_likes = serializers.IntegerField(default=0)

    def get_children(self, obj):
        # Serialize children comments
        if obj.children.exists():
            return PostCommentSerializer(obj.children.all(), many=True).data
        return []

    def create(self, validated_data):
        # Create a new comment instance
        return PostComments.objects.create(**validated_data)

    def update(self, instance, validated_data):
        # Update existing comment instance
        instance.parent_comment = validated_data.get('parent_comment', instance.parent_comment)
        instance.comment = validated_data.get('comment', instance.comment)
        instance.comment_likes = validated_data.get('comment_likes', instance.comment_likes)
        instance.related_post = validated_data.get('related_post', instance.related_post)
        instance.save()
        return instance
class PostSerializer(serializers.ModelSerializer):
    post_category = serializers.PrimaryKeyRelatedField(queryset=PostCategory.objects.all(), required=True)
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    # comments = PostCommentSerializer(many=True, read_only=True)
    class Meta:
        model = Post
        fields = '__all__'
    
    title = serializers.CharField(required=True, max_length=50)
    description = serializers.CharField(required=True)
    image = serializers.ImageField(required=True)
    post_ratings = serializers.IntegerField(default=0)
    rating_times = serializers.IntegerField(default=0)

    def create(self, validated_data):
        post = Post.objects.create(**validated_data)
        return post

    def update(self, instance, validated_data):
        instance.title = validated_data.get('title', instance.title)
        instance.description = validated_data.get('description', instance.description)
        instance.image = validated_data.get('image', instance.image)
        instance.post_category = validated_data.get('post_category', instance.post_category)
        instance.post_ratings = validated_data.get('post_ratings', instance.post_ratings)
        instance.rating_times = validated_data.get('rating_times', instance.rating_times)
        instance.save()
        return instance

    def validate_title(self, value):
        if len(value) > 50:
            raise serializers.ValidationError("Title length cannot exceed 50 characters.")
        return value

    def validate_image(self, value):
        if value is None:
            raise serializers.ValidationError("This field is required.")
        validate_image(value)
        return value
    

    

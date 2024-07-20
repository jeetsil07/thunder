from rest_framework import serializers
from .models import Post, PostCategory

def validate_image(image):
    if image.size > 1 * 1024 * 1024:
        raise serializers.ValidationError("The maximum file size that can be uploaded is 1MB.")
    if not image.name.lower().endswith(('.png', '.jpg', '.jpeg')):
        raise serializers.ValidationError("Unsupported file extension. Only PNG, JPG, and JPEG are allowed.")

class PostCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = PostCategory
        fields = ['id', 'name']

class PostSerializer(serializers.ModelSerializer):
    post_category = serializers.PrimaryKeyRelatedField(queryset=PostCategory.objects.all(), required=True)

    class Meta:
        model = Post
        fields = '__all__'
    
    title = serializers.CharField(required=True, max_length=50)
    description = serializers.CharField(required=True)
    image = serializers.ImageField(required=True)

    def create(self, validated_data):
        post = Post.objects.create(**validated_data)
        return post

    def update(self, instance, validated_data):
        instance.title = validated_data.get('title', instance.title)
        instance.description = validated_data.get('description', instance.description)
        instance.image = validated_data.get('image', instance.image)
        instance.post_category = validated_data.get('post_category', instance.post_category)
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

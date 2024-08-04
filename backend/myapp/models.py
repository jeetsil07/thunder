# myapp/models.py
from django.db import models
from django.core.exceptions import ValidationError
import uuid

# validation methods 
def validate_image(image):
    if image is None:
        raise ValidationError("This field is required.")
    # Validate file size (max 1 MB)
    if image.size > 1 * 1024 * 1024:
        raise ValidationError("The maximum file size that can be uploaded is 5MB.")
    # Validate file type
    if not image.name.lower().endswith(('.png', '.jpg', '.jpeg')):
        raise ValidationError("Unsupported file extension. Only PNG, JPG, and JPEG are allowed.")
def validate_title(self, value):
    if len(value) > 50:
        raise ValidationError("Title length cannot exceed 50 characters.")
    return value

# model classes

class PostCategory(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name
    
class Post(models.Model):
    title = models.CharField(
        max_length=50,
        validators=[validate_title]
    )
    description = models.TextField()
    image = models.ImageField(
        upload_to='posts/images/',
        validators=[validate_image]
    )
    post_category = models.ForeignKey(PostCategory, related_name='posts', on_delete=models.CASCADE)
    post_ratings = models.IntegerField(default=0)
    rating_times = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title
    
class PostComments(models.Model):
    comment_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    parent_comment = models.ForeignKey('self', null=True, blank=True, related_name='children', on_delete=models.CASCADE)
    comment = models.TextField()
    related_post = models.ForeignKey(Post, related_name='comments', on_delete=models.CASCADE)
    comment_likes = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.comment


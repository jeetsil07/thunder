# myapp/models.py
from django.db import models
from django.core.exceptions import ValidationError

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
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


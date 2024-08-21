# myapp/models.py
from django.db import models
from django.core.exceptions import ValidationError
import uuid
from django.utils import timezone
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin

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
class UsersAccountManager(BaseUserManager):
    def create_user(self, email, first_name, last_name, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        if not first_name:
            raise ValueError('The First Name field must be set')
        if not last_name:
            raise ValueError('The Last Name field must be set')

        email = self.normalize_email(email)
        
        # Extract the many-to-many data from extra_fields
        groups = extra_fields.pop('groups', None)
        user_permissions = extra_fields.pop('user_permissions', None)

        # Create the user instance without the many-to-many fields
        user = self.model(email=email, first_name=first_name, last_name=last_name, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)

        # Assign the many-to-many relationships after the user is saved
        if groups:
            user.groups.set(groups)
        
        if user_permissions:
            user.user_permissions.set(user_permissions)

        return user


class UsersAccount(AbstractBaseUser, PermissionsMixin):
    user_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    last_login = models.DateTimeField(null=True, blank=True, default=timezone.now)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(default=timezone.now)
    image = models.ImageField(
        upload_to='users/images/',
        validators=[validate_image],
        null=True,  # Allow image to be optional
        blank=True  # Allow image field to be empty
    )
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    objects = UsersAccountManager()

    def __str__(self):
        return self.email



class PostCategory(models.Model):
    name = models.CharField(max_length=50, unique=True)
    user = models.ForeignKey(UsersAccount, on_delete=models.SET_NULL, null=True, related_name='user_posts_category')

    def __str__(self):
        return self.name
    
class Post(models.Model):
    user = models.ForeignKey(UsersAccount, on_delete=models.SET_NULL, null=True, related_name='user_posts')
    title = models.CharField(
        max_length=50,
        validators=[validate_title]
    )
    description = models.TextField()
    image = models.ImageField(
        upload_to='posts/images/',
        validators=[validate_image]
    )
    post_category = models.ForeignKey(PostCategory, related_name='posts_in_category', on_delete=models.CASCADE)
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
    user = models.ForeignKey(UsersAccount, on_delete=models.SET_NULL, null=True, related_name='user_comments')


    def __str__(self):
        return self.comment


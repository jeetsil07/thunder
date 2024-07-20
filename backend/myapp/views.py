from django.shortcuts import render
from rest_framework import viewsets
from .models import Post, PostCategory
from .serializers import PostSerializer, PostCategorySerializer
import os
# Create your views here.

class PostCategoryModelViewSet(viewsets.ModelViewSet):
    queryset = PostCategory.objects.all()
    serializer_class = PostCategorySerializer

class PostModelViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.all()
    serializer_class = PostSerializer

    def perform_destroy(self, instance):
        # Delete the image file from the filesystem
        if instance.image:
            if os.path.isfile(instance.image.path):
                os.remove(instance.image.path)
        # Delete the Post instance
        instance.delete()

    def perform_update(self, serializer):
        # Check if the image is being updated
        instance = self.get_object()
        if 'image' in self.request.FILES and instance.image:
            # Delete the old image file from the filesystem
            if os.path.isfile(instance.image.path):
                os.remove(instance.image.path)
        # Save the new instance with the updated data
        serializer.save()

from django.shortcuts import render
from rest_framework import viewsets, status, generics
from .models import Post, PostCategory,PostComments,UsersAccount
from .serializers import PostSerializer, PostCategorySerializer, PostCommentSerializer, UserRegistrationSerializer, UserLoginSerializer, MemberSerializer
from django.contrib.auth import authenticate
from django.core.cache import cache
from rest_framework.response import Response
import os
from rest_framework.permissions import IsAuthenticatedOrReadOnly, BasePermission, SAFE_METHODS, IsAuthenticated
from rest_framework.exceptions import AuthenticationFailed
import jwt
from django.conf import settings
from django.contrib.auth import get_user_model
from django.http import FileResponse
# Create your views here.
import logging
class UserRegistrationView(generics.GenericAPIView):
    serializer_class = UserRegistrationSerializer

    def get_object(self):
        # Retrieve the current user
        return self.request.user

    def post(self, request, *args, **kwargs):
        # Handle user creation (no authentication required)
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({'status': 'User created'}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, *args, **kwargs):
        user = self.get_object()  # Get the current user
        serializer = self.get_serializer(user, data=request.data, partial=True)
        
        if serializer.is_valid():
            # Check if a new image is provided in the request
            new_image = request.data.get('image', None)
            print("New image received:", new_image)
            
            if new_image:
                # Delete the old image if it exists
                if user.image and hasattr(user.image, 'path'):
                    old_image_path = user.image.path
                    print("Old image path:", old_image_path)
                    
                    if os.path.exists(old_image_path):
                        print("Old image exists, deleting...")
                        os.remove(old_image_path)
                        print("Old image deleted.")
                    else:
                        print("Old image does not exist.")
            
            # Save the new data, including the new image
            user = serializer.save()

            updated_user_data = self.get_serializer(user).data
            
            return Response({
                'status': 'User updated',
                'user': updated_user_data
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class UserLoginView(generics.GenericAPIView):
    serializer_class = UserLoginSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            tokens = serializer.validated_data.get('tokens')
            user = serializer.validated_data.get('user')

             # Pass the request context to the serializer
            user_data = UserRegistrationSerializer(user, context={'request': request}).data
            
            response_data = {
                'tokens': tokens,
                'user': user_data,
            }
            # print(response_data)
            return Response(response_data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    # def patch(self, request, *args, **kwargs):
    #     # Update existing user
    #     user = self.get_object()  # Get the current user
    #     serializer = self.get_serializer(user, data=request.data, partial=True)
    #     if serializer.is_valid():
    #         user = serializer.save()
    #         return Response({'status': 'User updated'}, status=status.HTTP_200_OK)
    #     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
# logger = logging.getLogger(__name__)
class IsAuthenticatedOrReadOnlyForUpdateDelete(BasePermission):
    """
    Custom permission to only allow authenticated users to update or delete an object.
    """
    def has_permission(self, request, view):
        # Allow any user to add a comment (POST request)
        if request.method in SAFE_METHODS or request.method == 'POST':
            return True
        # Only allow authenticated users to delete or update comments
        return request.user and request.user.is_authenticated

class PostCommentsModelViewSet(viewsets.ModelViewSet):
    queryset = PostComments.objects.all()
    serializer_class = PostCommentSerializer
    permission_classes = [IsAuthenticatedOrReadOnlyForUpdateDelete]

    def list(self, request, *args, **kwargs):
        # Get the post_id from the query parameters
        post_id = request.query_params.get('post_id', None)

        # Create a cache key based on post_id
        if post_id:
            cache_key = f'post_comments_{post_id}'
        else:
            cache_key = 'all_root_comments'

        # Try to get data from cache
        cached_data = cache.get(cache_key)

        if cached_data is not None:
            # If data is cached, return it
            print('cache hit',cached_data,cache_key)
            return Response(cached_data)

        # If no cache, query the database
        if post_id:
            queryset = self.filter_queryset(self.get_queryset().filter(related_post_id=post_id, parent_comment__isnull=True))
        else:
            queryset = self.filter_queryset(self.get_queryset().filter(parent_comment__isnull=True))

        serializer = self.get_serializer(queryset, many=True)
        data = serializer.data

        # Cache the data for 2 minutes
        cache.set(cache_key, data, timeout=60*2)  # Cache for 2 minutes

        return Response(data)
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        related_post_id = serializer.data.get('related_post')
        cache_key = f'post_comments_{related_post_id}'
        cache.delete(cache_key)

        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    def perform_create(self, serializer):
        if self.request.user.is_authenticated:
            serializer.save(user=self.request.user)
        else:
            serializer.save(user=None)  # Save without assigning a user for anonymous comments

    def partial_update(self, request, *args, **kwargs):
        print('updating')
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        related_post_id = instance.related_post_id
        cache_key = f'post_comments_{related_post_id}'
        cache.delete(cache_key)
        return Response(serializer.data)
    
    def destroy(self, request, *args, **kwargs):
        print('deleting')
        instance = self.get_object()
        self.perform_destroy(instance)
        related_post_id = instance.related_post_id
        cache_key = f'post_comments_{related_post_id}'
        cache.delete(cache_key)
        return Response(status=status.HTTP_204_NO_CONTENT)

class PostCategoryModelViewSet(viewsets.ModelViewSet):
    queryset = PostCategory.objects.all()
    serializer_class = PostCategorySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
    # Pass the current user to the serializer's `save` method
        serializer.save(user=self.request.user)
    
class PostModelViewSet(viewsets.ModelViewSet):
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        queryset = Post.objects.all()
        category_id = self.request.query_params.get('category_id', None)
        
        if category_id:
            queryset = queryset.filter(post_category_id=category_id)
        
        return queryset

    def list(self, request, *args, **kwargs):
        category_id = request.query_params.get('category_id', None)
        
        if category_id:
            cache_key = f'post_category_{category_id}'
        else:
            cache_key = 'post_list'
        
        cached_data = cache.get(cache_key)
        
        if cached_data is not None:
            print('Cache hit', cached_data, cache_key)
            response = Response(cached_data)
        else:
            queryset = self.get_queryset()
            data = PostSerializer(queryset, many=True, context={'request': request}).data
            cache.set(cache_key, data, timeout=60*2)
            print('Cache miss')
            response = Response(data)
        
        return response
    
    def perform_create(self, serializer):
        instance = serializer.save(user=self.request.user)
        cache.delete('post_list')
        cache.delete(f'post_category_{instance.post_category_id}')

    def perform_destroy(self, instance):
        if instance.image:
            if os.path.isfile(instance.image.path):
                os.remove(instance.image.path)
        instance.delete()
        cache.delete('post_list')
        cache.delete(f'post_category_{instance.post_category_id}')

    def perform_update(self, serializer):
        instance = self.get_object()
        if 'image' in self.request.FILES and instance.image:
            if os.path.isfile(instance.image.path):
                os.remove(instance.image.path)
        serializer.save()
        cache.delete('post_list')
        cache.delete(f'post_category_{instance.post_category_id}')

def download_resume(request):
    pdf_path = os.path.join(settings.MEDIA_ROOT, 'resume', 'resume.pdf')
    return FileResponse(open(pdf_path, 'rb'), content_type='application/pdf', as_attachment=True, filename='resume.pdf')

class MemberView(generics.ListAPIView):
    """
    API view to list all users with only public information (image, first name, last name, and bio).
    """
    queryset = UsersAccount.objects.filter()  # Only active users
    serializer_class = MemberSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]  # Open for everyone (no authentication required)

class EnvView(generics.ListAPIView):
    """
    API view to list all users with only public information (image, first name, last name, and bio).
    """
    permission_classes = [IsAuthenticatedOrReadOnly]  # Open for everyone (no authentication required)
    def get_queryset(self):
        # This method is required by ListAPIView but not used in this case
        return []

    def list(self, request, *args, **kwargs):
        return Response({"message": "QA ENVIRONMENT showing"})

class Addstaging(generics.ListAPIView):
    """
    API view to list all users with only public information (image, first name, last name, and bio).
    """
    permission_classes = [IsAuthenticatedOrReadOnly]  # Open for everyone (no authentication required)
    def get_queryset(self):
        # This method is required by ListAPIView but not used in this case
        return []

    def list(self, request, *args, **kwargs):
        return Response({"message": "staging added"})
from django.shortcuts import render
from rest_framework import viewsets, status, generics
from .models import Post, PostCategory,PostComments
from .serializers import PostSerializer, PostCategorySerializer, PostCommentSerializer, UserRegistrationSerializer, UserLoginSerializer
from django.contrib.auth import authenticate
from django.core.cache import cache
from rest_framework.response import Response
import os
from rest_framework.permissions import IsAuthenticatedOrReadOnly, BasePermission, SAFE_METHODS
from rest_framework.exceptions import AuthenticationFailed
import jwt
from django.conf import settings
# Create your views here.
import logging
# def extract_user_id_from_jwt(request):
#     """Extracts the user ID from the JWT token in the request's Authorization header."""
#     auth_header = request.headers.get('Authorization')
    
#     if auth_header and auth_header.startswith('Bearer '):
#         jwt_token = auth_header.split(' ')[1]  # Extract the token part
        
#         try:
#             # Decode the JWT to extract the payload
#             decoded_payload = jwt.decode(jwt_token, settings.SECRET_KEY, algorithms=["HS256"])
            
#             # Extract the user ID from the payload
#             user_id = decoded_payload.get('user_id')
#             return user_id
        
#         except jwt.ExpiredSignatureError:
#             raise AuthenticationFailed("Token has expired")
        
#         except jwt.InvalidTokenError:
#             raise AuthenticationFailed("Invalid token")
    
#     raise AuthenticationFailed("Authorization header missing or invalid")

class UserRegistrationView(generics.GenericAPIView):
    serializer_class = UserRegistrationSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({'status': 'User created'}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserLoginView(generics.GenericAPIView):
    serializer_class = UserLoginSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            tokens = serializer.validated_data.get('tokens')
            user = serializer.validated_data.get('user')

            user_data = UserRegistrationSerializer(user).data
            
            response_data = {
                'tokens': tokens,
                'user': user_data,
            }
            return Response(response_data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

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
        # This method is still responsible for querying
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
        
        # Check if the data is in cache
        cached_data = cache.get(cache_key)
        
        if cached_data is not None:
            print('Cache hit',cached_data,cache_key)
            # Create a Response object with the cached data
            response = Response(cached_data)
        else:
            # Fetch data from the database
            queryset = self.get_queryset()
            data = PostSerializer(queryset, many=True, context={'request': request}).data
            
            # Cache the data
            cache.set(cache_key, data, timeout=60*2)  # Cache for 2 minutes
            print('Cache miss')
            
            # Create a Response object with the fetched data
            response = Response(data)
        
        return response
    
    # def retrieve(self, request, *args, **kwargs):
    #     print("Request:", request)
    #     print("Arguments:", args)
    #     print("Keyword Arguments:", kwargs)
    #     cache_key = f'post_{kwargs["pk"]}'
    #     data = cache.get(cache_key)
    #     if not data:
    #         response = super().retrieve(request, *args, **kwargs)
    #         data = response.data
    #         cache.set(cache_key, data, timeout=60 * 15)  # Cache for 15 minutes
    #     else:
    #         response = Response(data)
    #     return response
    
    def perform_create(self, serializer):
        # Save the new post
        instance = serializer.save(user=self.request.user)
        
        # Invalidate the cache
        cache.delete('post_list')  # Invalidate the cache for the post list
        cache.delete(f'post_category_{instance.post_category_id}')  # Invalidate category-specific cache

    def perform_destroy(self, instance):
        # Delete the image file from the filesystem
        if instance.image:
            if os.path.isfile(instance.image.path):  
                os.remove(instance.image.path)
        # Delete the Post instance
        instance.delete()
        # Invalidate the cache
        cache.delete('post_list')  # Invalidate the cache for the post list
        cache.delete(f'post_category_{instance.post_category_id}')  # Invalidate category-specific cache

    def perform_update(self, serializer):
        # Check if the image is being updated
        instance = self.get_object() 
        if 'image' in self.request.FILES and instance.image:
            # Delete the old image file from the filesystem
            if os.path.isfile(instance.image.path):
                os.remove(instance.image.path)
        # Save the new instance with the updated data
        serializer.save()
        # Invalidate the cache
        cache.delete('post_list')  # Invalidate the cache for the post list
        cache.delete(f'post_category_{instance.post_category_id}')  # Invalidate category-specific cache

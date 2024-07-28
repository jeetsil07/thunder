from django.shortcuts import render
from rest_framework import viewsets
from .models import Post, PostCategory,PostComments
from .serializers import PostSerializer, PostCategorySerializer, PostCommentSerializer
from django.core.cache import cache
from rest_framework.response import Response
import os
# Create your views here.
import logging

# logger = logging.getLogger(__name__)
class PostCommentsModelViewSet(viewsets.ModelViewSet):
    queryset = PostComments.objects.all()
    serializer_class = PostCommentSerializer

    def list(self, request, *args, **kwargs):
        # Get the post_id from the query parameters
        post_id = request.query_params.get('post_id', None)

        # Create a cache key based on post_id
        # if post_id:
        #     cache_key = f'post_comments_{post_id}'
        # else:
        #     cache_key = 'all_root_comments'

        # # Try to get data from cache
        # cached_data = cache.get(cache_key)

        # if cached_data is not None:
        #     # If data is cached, return it
        #     print('cache hit',cached_data,cache_key)
        #     return Response(cached_data)

        # If no cache, query the database
        if post_id:
            queryset = self.filter_queryset(self.get_queryset().filter(related_post_id=post_id, parent_comment__isnull=True))
        else:
            queryset = self.filter_queryset(self.get_queryset().filter(parent_comment__isnull=True))

        # Paginate the results if necessary
        # page = self.paginate_queryset(queryset)
        # if page is not None:
        #     serializer = self.get_serializer(page, many=True)
        #     data = self.get_paginated_response(serializer.data).data
        # else:
        #     serializer = self.get_serializer(queryset, many=True)
        #     data = serializer.data
        serializer = self.get_serializer(queryset, many=True)
        data = serializer.data

        # Cache the data for 2 minutes
        # cache.set(cache_key, data, timeout=60*2)  # Cache for 2 minutes

        return Response(data)

class PostCategoryModelViewSet(viewsets.ModelViewSet):
    queryset = PostCategory.objects.all()
    serializer_class = PostCategorySerializer
    
class PostModelViewSet(viewsets.ModelViewSet):
    serializer_class = PostSerializer

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

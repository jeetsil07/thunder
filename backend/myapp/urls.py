from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PostModelViewSet, PostCategoryModelViewSet, PostCommentsModelViewSet

# Create a router and register our viewset with it.
router = DefaultRouter()
router.register(r'posts', PostModelViewSet,basename='post')
router.register(r'postscategory', PostCategoryModelViewSet)
router.register(r'postcomment', PostCommentsModelViewSet)

# The API URLs are now determined automatically by the router.
urlpatterns = [
    path('', include(router.urls)),
]
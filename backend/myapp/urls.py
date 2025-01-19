from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PostModelViewSet, PostCategoryModelViewSet, PostCommentsModelViewSet, download_resume
from .views import UserRegistrationView, UserLoginView, MemberView, EnvView, Addproduction
# Create a router and register our viewset with it.
router = DefaultRouter()
router.register(r'posts', PostModelViewSet,basename='post')
router.register(r'postscategory', PostCategoryModelViewSet)
router.register(r'postcomment', PostCommentsModelViewSet)

# The API URLs are now determined automatically by the router.
urlpatterns = [
    path('', include(router.urls)),
    path('register/', UserRegistrationView.as_view(), name='user-register'),
    path('login/', UserLoginView.as_view(), name='user-login'),
    path('resume/', download_resume, name='download_resume'),
    path('members/', MemberView.as_view(), name='public-users'),
    path('env/', EnvView.as_view(), name='env-view'),
    path('production/', Addproduction.as_view(), name='production'),
]

# add produvtion
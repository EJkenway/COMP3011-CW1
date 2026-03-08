"""
Authentication and User Management Views
"""
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from drf_spectacular.utils import extend_schema, extend_schema_view

from api.serializers.auth import (
    UserRegistrationSerializer,
    UserSerializer,
    UserProfileUpdateSerializer,
    ChangePasswordSerializer,
)


@extend_schema_view(
    post=extend_schema(
        summary="Register a new user",
        description="""
Register a new user account.

Returns JWT tokens (access and refresh) upon successful registration.

**Password Requirements:**
- Minimum 8 characters
- Cannot be entirely numeric
- Cannot be too similar to other personal information
- Cannot be a commonly used password
        """,
        tags=['Authentication'],
        responses={
            201: {
                'type': 'object',
                'properties': {
                    'user': {'type': 'object'},
                    'tokens': {
                        'type': 'object',
                        'properties': {
                            'access': {'type': 'string'},
                            'refresh': {'type': 'string'},
                        }
                    },
                    'message': {'type': 'string'}
                }
            }
        }
    )
)
class RegisterView(generics.CreateAPIView):
    """
    User registration endpoint.
    
    Creates a new user account and returns JWT tokens for immediate authentication.
    """
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'user': UserSerializer(user).data,
            'tokens': {
                'access': str(refresh.access_token),
                'refresh': str(refresh),
            },
            'message': 'Registration successful. Welcome to Smart Productivity!'
        }, status=status.HTTP_201_CREATED)


@extend_schema_view(
    get=extend_schema(
        summary="Get current user profile",
        description="Retrieve the authenticated user's profile information.",
        tags=['Authentication'],
    ),
    put=extend_schema(
        summary="Update user profile",
        description="Update the authenticated user's profile information.",
        tags=['Authentication'],
    ),
    patch=extend_schema(
        summary="Partially update user profile",
        description="Partially update the authenticated user's profile.",
        tags=['Authentication'],
    ),
)
class ProfileView(generics.RetrieveUpdateAPIView):
    """
    User profile endpoint.
    
    GET: Retrieve current user's profile
    PUT/PATCH: Update current user's profile
    """
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        return self.request.user
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return UserProfileUpdateSerializer
        return UserSerializer


@extend_schema_view(
    post=extend_schema(
        summary="Change password",
        description="""
Change the authenticated user's password.

Requires the current password for verification.
        """,
        tags=['Authentication'],
        responses={
            200: {
                'type': 'object',
                'properties': {
                    'message': {'type': 'string'},
                    'tokens': {
                        'type': 'object',
                        'description': 'New JWT tokens after password change',
                        'properties': {
                            'access': {'type': 'string'},
                            'refresh': {'type': 'string'},
                        }
                    }
                }
            }
        }
    )
)
class ChangePasswordView(generics.GenericAPIView):
    """
    Password change endpoint.
    
    Changes the user's password and returns new JWT tokens.
    """
    serializer_class = ChangePasswordSerializer
    permission_classes = [IsAuthenticated]
    
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        # Generate new tokens after password change
        refresh = RefreshToken.for_user(request.user)
        
        return Response({
            'message': 'Password changed successfully.',
            'tokens': {
                'access': str(refresh.access_token),
                'refresh': str(refresh),
            }
        }, status=status.HTTP_200_OK)

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny, IsAuthenticated
from .serializers import RegistrationSerializer, LoginSerializer, EmailCheckSerializer 
from django.contrib.auth import get_user_model


User = get_user_model()

class RegistrationView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    
    def post(self, request):
        serializer = RegistrationSerializer(data=request.data)
        
        if serializer.is_valid():
            user = serializer.save()
            
            token, created = Token.objects.get_or_create(user=user)
            
            return Response({
                'token': token.key,
                'fullname': user.username,
                'email': user.email,
                'user_id': user.id
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    

class LoginView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        
        if serializer.is_valid():
            user = serializer.validated_data['user']
            
            # Token holen oder erstellen
            token, created = Token.objects.get_or_create(user=user)
            
            return Response({
                'token': token.key,
                'fullname': user.username,
                'email': user.email,
                'user_id': user.id
            }, status=status.HTTP_200_OK)
        
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )



class EmailCheckView(APIView):
    """
    GET /api/email-check/?email=<email>
    Checks if an email address is already registered
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        email = request.query_params.get('email', None)
        
        if not email:
            return Response(
                {'detail': 'Email parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate email format
        serializer = EmailCheckSerializer(data={'email': email})
        if not serializer.is_valid():
            return Response(
                {'detail': 'Invalid email format'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if user exists
        try:
            user = User.objects.get(email=email)
            return Response(
                {
                    'id': user.id,
                    'email': user.email,
                    'fullname': user.username
                },
                status=status.HTTP_200_OK
            )
        except User.DoesNotExist:
            return Response(
                {'detail': 'Email not found'},
                status=status.HTTP_404_NOT_FOUND
            )
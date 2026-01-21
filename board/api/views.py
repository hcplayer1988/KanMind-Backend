"""API views for board endpoints."""
from django.db import models
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from board.models import Board
from .serializers import BoardSerializer, BoardDetailSerializer


class BoardPatchResponseSerializer:
    """Custom serializer for PATCH response with minimal fields."""
    
    @staticmethod
    def serialize(board):
        """Serialize board for PATCH response."""
        members_list = board.members.all()
        members_data = [
            {
                'id': member.id,
                'email': member.email,
                'fullname': member.username
            }
            for member in members_list
        ]
        
        return {
            'id': board.id,
            'title': board.title,
            'owner_data': {
                'id': board.owner.id,
                'email': board.owner.email,
                'fullname': board.owner.username
            },
            'members_data': members_data
        }


class BoardViewSet(viewsets.ModelViewSet):
    """ViewSet for managing boards."""
    
    serializer_class = BoardSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Return only boards where the user is either owner or member."""
        user = self.request.user
        return Board.objects.filter(
            models.Q(owner=user) | models.Q(members=user)
        ).distinct()

    def list(self, request, *args, **kwargs):
        """GET /api/boards/ - List all accessible boards."""
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        """POST /api/boards/ - Create a new board."""
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            board = serializer.save(owner=request.user)
            response_serializer = self.get_serializer(board)
            return Response(
                response_serializer.data,
                status=status.HTTP_201_CREATED
            )
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

    def retrieve(self, request, *args, **kwargs):
        """GET /api/boards/{board_id}/ - Retrieve a single board."""
        user = request.user
        board_id = kwargs.get('pk')
        
        # First check if board exists at all
        try:
            board = Board.objects.get(pk=board_id)
        except Board.DoesNotExist:
            # Board doesn't exist - but check if user would have permission first
            # If board existed but user has no access to any boards, it's still 404
            # because we can't determine permissions on non-existent resource
            return Response(
                {'detail': 'Board not found. The specified Board-ID does not exist.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Board exists - now check permissions (403 before 404 for existing resources)
        if (board.owner != user and
                not board.members.filter(id=user.id).exists()):
            return Response(
                {'detail': 'Forbidden. User must be either owner or member of the board.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = BoardDetailSerializer(board)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def partial_update(self, request, *args, **kwargs):
        """PATCH /api/boards/{board_id}/ - Update board title and members."""
        # Check if board exists (will raise 404 if not found)
        try:
            board = Board.objects.get(pk=kwargs.get('pk'))
        except Board.DoesNotExist:
            return Response(
                {'detail': 'Board not found. The specified Board-ID does not exist.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        user = request.user
        
        # 403: Check permissions - user must be owner or member
        if (board.owner != user and
                not board.members.filter(id=user.id).exists()):
            return Response(
                {'detail': 'Forbidden. User must be either owner or member of the board to update it.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Validate request data
        serializer = self.get_serializer(
            board,
            data=request.data,
            partial=True
        )
        
        # 400: Invalid data
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Save the board
            board = serializer.save()
            
            # Return custom minimal response
            response_data = BoardPatchResponseSerializer.serialize(board)
            return Response(
                response_data,
                status=status.HTTP_200_OK
            )
        except Exception as e:
            # 500: Internal server error
            return Response(
                {'detail': f'Internal server error: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def destroy(self, request, *args, **kwargs):
        """DELETE /api/boards/{board_id}/ - Delete a board (owner only)."""
        user = request.user
        board_id = kwargs.get('pk')
        
        # Check if board exists
        try:
            board = Board.objects.get(pk=board_id)
        except Board.DoesNotExist:
            return Response(
                {'detail': 'Board not found. The specified Board-ID does not exist.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Board exists - check permissions (must be owner OR member to get 403, not 404)
        if (board.owner != user and
                not board.members.filter(id=user.id).exists()):
            return Response(
                {'detail': 'Forbidden. You do not have permission to access this board.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # User is member or owner - check if owner (only owner can delete)
        if board.owner != user:
            return Response(
                {'detail': 'Forbidden. Only the owner can delete this board.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        board.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
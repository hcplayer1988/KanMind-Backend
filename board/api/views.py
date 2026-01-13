from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import models
from django.shortcuts import get_object_or_404
from board.models import Board
from .serializers import BoardSerializer

class BoardViewSet(viewsets.ModelViewSet):
    serializer_class = BoardSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """
        Returns only boards where the user is either owner or member
        """
        user = self.request.user
        return Board.objects.filter(
            models.Q(owner=user) | models.Q(members=user)
        ).distinct()
    
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def create(self, request, *args, **kwargs):
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
        """
        GET /api/boards/{board_id}/
        Retrieves a single board
        """
        board = self.get_object()
        user = request.user
        
        # Check if user has access (owner or member)
        if board.owner != user and not board.members.filter(id=user.id).exists():
            return Response(
                {'detail': 'You do not have permission to access this board.'},
                status=status.HTTP_403_FORBIDDEN
            )
    
        from .serializers import BoardDetailSerializer
        serializer = BoardDetailSerializer(board)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def partial_update(self, request, *args, **kwargs):
        """
        PATCH /api/boards/{board_id}/
        Updates board members and/or title
        """
        board = self.get_object()
        user = request.user
        
        # Check if user is owner or member of the board
        if board.owner != user and not board.members.filter(id=user.id).exists():
            return Response(
                {'detail': 'You do not have permission to modify this board.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = self.get_serializer(
            board,
            data=request.data,
            partial=True
        )
        
        if serializer.is_valid():
            board = serializer.save()
            response_serializer = self.get_serializer(board)
            return Response(
                response_serializer.data,
                status=status.HTTP_200_OK
            )
        
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )
    
    def destroy(self, request, *args, **kwargs):
        """
        DELETE /api/boards/{board_id}/
        Deletes a board. Only the owner can delete the board.
        """
        board = self.get_object()
        user = request.user
        
        # Check if user is the owner
        if board.owner != user:
            return Response(
                {'detail': 'Only the owner can delete this board.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Delete the board (will also delete all associated tasks and comments)
        board.delete()
        
        return Response(
            status=status.HTTP_204_NO_CONTENT
        )


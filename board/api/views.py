"""API views for board endpoints."""

from django.db import models
from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from board.models import Board

from .serializers import BoardSerializer


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
        board = self.get_object()
        user = request.user

        if (board.owner != user and
                not board.members.filter(id=user.id).exists()):
            return Response(
                {'detail': 'You do not have permission to access this '
                           'board.'},
                status=status.HTTP_403_FORBIDDEN
            )

        from .serializers import BoardDetailSerializer
        serializer = BoardDetailSerializer(board)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def partial_update(self, request, *args, **kwargs):
        """PATCH /api/boards/{board_id}/ - Update board title and members."""
        board = self.get_object()
        user = request.user

        if (board.owner != user and
                not board.members.filter(id=user.id).exists()):
            return Response(
                {'detail': 'You do not have permission to modify this '
                           'board.'},
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
        """DELETE /api/boards/{board_id}/ - Delete a board (owner only)."""
        board = self.get_object()
        user = request.user

        if board.owner != user:
            return Response(
                {'detail': 'Only the owner can delete this board.'},
                status=status.HTTP_403_FORBIDDEN
            )

        board.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)


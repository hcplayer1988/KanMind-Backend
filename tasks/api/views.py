"""API views for task endpoints."""

from django.db import models
from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from board.models import Board
from tasks.models import Comment, Task

from .serializers import CommentSerializer, TaskSerializer


class TaskViewSet(viewsets.ModelViewSet):
    """ViewSet for managing tasks."""

    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Return only tasks from boards where user is owner or member."""
        user = self.request.user
        return Task.objects.filter(
            models.Q(board__owner=user) | models.Q(board__members=user)
        ).distinct()

    def create(self, request, *args, **kwargs):
        """POST /api/tasks/ - Create a new task within a board."""
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            task = serializer.save()
            response_serializer = self.get_serializer(task)
            return Response(
                response_serializer.data,
                status=status.HTTP_201_CREATED
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

    def partial_update(self, request, *args, **kwargs):
        """PATCH /api/tasks/{task_id}/ - Update an existing task."""
        task = self.get_object()
        user = request.user
        board = task.board

        if (board.owner != user and
                not board.members.filter(id=user.id).exists()):
            return Response(
                {'detail': 'You must be a member of the board to update '
                           'this task.'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = self.get_serializer(
            task,
            data=request.data,
            partial=True
        )

        if serializer.is_valid():
            task = serializer.save()
            response_serializer = self.get_serializer(task)
            return Response(
                response_serializer.data,
                status=status.HTTP_200_OK
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

    def destroy(self, request, *args, **kwargs):
        """DELETE /api/tasks/{task_id}/ - Delete a task (owner only)."""
        task = self.get_object()
        user = request.user
        board = task.board

        if board.owner != user:
            return Response(
                {'detail': 'Only the task creator or board owner can '
                           'delete this task.'},
                status=status.HTTP_403_FORBIDDEN
            )

        task.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['get', 'post'], url_path='comments')
    def comments(self, request, pk=None):
        """
        GET/POST /api/tasks/{task_id}/comments/
        Get all comments or create a new comment for a task.
        """
        task = self.get_object()
        user = request.user
        board = task.board

        if (board.owner != user and
                not board.members.filter(id=user.id).exists()):
            return Response(
                {'detail': 'You must be a member of the board.'},
                status=status.HTTP_403_FORBIDDEN
            )

        if request.method == 'GET':
            comments_list = task.comments.all()
            serializer = CommentSerializer(comments_list, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        elif request.method == 'POST':
            serializer = CommentSerializer(data=request.data)

            if serializer.is_valid():
                comment = serializer.save(task=task, author=user)
                response_serializer = CommentSerializer(comment)
                return Response(
                    response_serializer.data,
                    status=status.HTTP_201_CREATED
                )

            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['delete'],
            url_path='comments/(?P<comment_id>[^/.]+)')
    def delete_comment(self, request, pk=None, comment_id=None):
        """DELETE /api/tasks/{task_id}/comments/{comment_id}/"""
        task = self.get_object()
        user = request.user
        board = task.board

        if (board.owner != user and
                not board.members.filter(id=user.id).exists()):
            return Response(
                {'detail': 'You must be a member of the board.'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        try:
            comment = Comment.objects.get(id=comment_id, task=task)
        except Comment.DoesNotExist:
            return Response(
                {'detail': 'Comment not found.'},
                status=status.HTTP_404_NOT_FOUND
            )

        if comment.author != user:
            return Response(
                {'detail': 'Only the comment author can delete it.'},
                status=status.HTTP_403_FORBIDDEN
            )

        comment.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'], url_path='assigned-to-me')
    def assigned_to_me(self, request):
        """GET /api/tasks/assigned-to-me/ - Tasks assigned to current user."""
        user = request.user
        tasks = self.get_queryset().filter(assignee=user)
        serializer = self.get_serializer(tasks, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='reviewing')
    def reviewing(self, request):
        """GET /api/tasks/reviewing/ - Tasks user is reviewing."""
        user = request.user
        tasks = self.get_queryset().filter(reviewer=user)
        serializer = self.get_serializer(tasks, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    
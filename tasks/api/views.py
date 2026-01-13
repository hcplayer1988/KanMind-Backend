from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import models
from django.shortcuts import get_object_or_404
from tasks.models import Task, Comment
from board.models import Board
from .serializers import TaskSerializer, CommentSerializer

class TaskViewSet(viewsets.ModelViewSet):
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """
        Returns only tasks from boards where the user is owner or member
        """
        user = self.request.user
        return Task.objects.filter(
            models.Q(board__owner=user) | models.Q(board__members=user)
        ).distinct()
    
    def create(self, request, *args, **kwargs):
        """
        POST /api/tasks/
        Creates a new task within a board
        """
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
        """
        PATCH /api/tasks/{task_id}/
        Updates an existing task
        """
        task = self.get_object()
        user = request.user
        board = task.board
        
        # Check if user is member of the board
        if board.owner != user and not board.members.filter(id=user.id).exists():
            return Response(
                {'detail': 'You must be a member of the board to update this task.'},
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
        """
        DELETE /api/tasks/{task_id}/
        Deletes a task. Only the task creator or board owner can delete the task.
        """
        task = self.get_object()
        user = request.user
        board = task.board
        
        # Check if user is the board owner
        if board.owner != user:
            return Response(
                {'detail': 'Only the task creator or board owner can delete this task.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Delete the task (will also cascade delete all comments)
        task.delete()
        
        return Response(
            status=status.HTTP_204_NO_CONTENT
        )
    
    @action(detail=True, methods=['get', 'post'], url_path='comments')
    def comments(self, request, pk=None):
        """
        GET/POST /api/tasks/{task_id}/comments/
        Get all comments or create a new comment for a task
        """
        task = self.get_object()
        user = request.user
        board = task.board
        
        # Check if user is member of the board
        if board.owner != user and not board.members.filter(id=user.id).exists():
            return Response(
                {'detail': 'You must be a member of the board.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if request.method == 'GET':
            # Get all comments for this task (sorted chronologically)
            comments_list = task.comments.all()
            serializer = CommentSerializer(comments_list, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        elif request.method == 'POST':
            # Create new comment
            serializer = CommentSerializer(data=request.data)
            
            if serializer.is_valid():
                # Create comment with author automatically set
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
    
    @action(detail=True, methods=['delete'], url_path='comments/(?P<comment_id>[^/.]+)')
    def delete_comment(self, request, pk=None, comment_id=None):
        """
        DELETE /api/tasks/{task_id}/comments/{comment_id}/
        Deletes a comment. Only the comment author can delete it.
        """
        task = self.get_object()
        user = request.user
        board = task.board
        
        # Check if user is member of the board
        if board.owner != user and not board.members.filter(id=user.id).exists():
            return Response(
                {'detail': 'You must be a member of the board.'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Get the comment
        try:
            comment = Comment.objects.get(id=comment_id, task=task)
        except Comment.DoesNotExist:
            return Response(
                {'detail': 'Comment not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if user is the author of the comment
        if comment.author != user:
            return Response(
                {'detail': 'Only the comment author can delete it.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Delete the comment
        comment.delete()
        
        return Response(
            status=status.HTTP_204_NO_CONTENT
        )
    
    @action(detail=False, methods=['get'], url_path='assigned-to-me')
    def assigned_to_me(self, request):
        """
        GET /api/tasks/assigned-to-me/
        Returns all tasks assigned to the current user
        """
        user = request.user
        tasks = self.get_queryset().filter(assignee=user)
        serializer = self.get_serializer(tasks, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'], url_path='reviewing')
    def reviewing(self, request):
        """
        GET /api/tasks/reviewing/
        Returns all tasks where the current user is the reviewer
        """
        user = request.user
        tasks = self.get_queryset().filter(reviewer=user)
        serializer = self.get_serializer(tasks, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    
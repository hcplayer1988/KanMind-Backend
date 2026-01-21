"""API views for task endpoints."""

from django.db import models
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from tasks.models import Comment, Task

from .serializers import CommentSerializer, TaskSerializer


class TaskPatchResponseSerializer:
    """Custom serializer for PATCH response with complete task data."""
    
    @staticmethod
    def serialize(task):
        """Serialize task for PATCH response."""
        assignee_data = None
        if task.assignee:
            assignee_data = {
                'id': task.assignee.id,
                'email': task.assignee.email,
                'fullname': task.assignee.username
            }
        
        reviewer_data = None
        if task.reviewer:
            reviewer_data = {
                'id': task.reviewer.id,
                'email': task.reviewer.email,
                'fullname': task.reviewer.username
            }
        
        return {
            'id': task.id,
            'title': task.title,
            'description': task.description,
            'status': task.status,
            'priority': task.priority,
            'assignee': assignee_data,
            'reviewer': reviewer_data,
            'due_date': task.due_date.isoformat() if task.due_date else None
        }


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
        # Check if task exists
        try:
            task = Task.objects.get(pk=kwargs.get('pk'))
        except Task.DoesNotExist:
            return Response(
                {'detail': 'Task not found. The specified Task-ID does not exist.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        user = request.user
        board = task.board

        # 403: Check permissions - user must be board member
        if (board.owner != user and
                not board.members.filter(id=user.id).exists()):
            return Response(
                {'detail': 'Forbidden. User must be a member of the board to update this task.'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Validate request data
        serializer = self.get_serializer(
            task,
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
            # Save the task
            task = serializer.save()
            
            # Return custom response with complete task data
            response_data = TaskPatchResponseSerializer.serialize(task)
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
        """DELETE /api/tasks/{task_id}/ - Delete a task (board owner only)."""
        user = request.user
        task_id = kwargs.get('pk')
        
        # Check if task exists
        try:
            task = Task.objects.get(pk=task_id)
        except Task.DoesNotExist:
            return Response(
                {'detail': 'Task not found. The specified Task-ID does not exist.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        board = task.board
        
        # Check if user is board member (403 if not)
        if (board.owner != user and
                not board.members.filter(id=user.id).exists()):
            return Response(
                {'detail': 'Forbidden. You must be a member of the board.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # User is board member - check if owner (only owner can delete)
        if board.owner != user:
            return Response(
                {'detail': 'Forbidden. Only the board owner can delete this task.'},
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
        user = request.user
        task_id = pk
        
        # Check if task exists
        try:
            task = Task.objects.get(pk=task_id)
        except Task.DoesNotExist:
            return Response(
                {'detail': 'Task not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        board = task.board

        # Check if user is board member (403 if not)
        if (board.owner != user and
                not board.members.filter(id=user.id).exists()):
            return Response(
                {'detail': 'Forbidden. You must be a member of the board.'},
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
        user = request.user
        task_id = pk
        
        # Check if task exists
        try:
            task = Task.objects.get(pk=task_id)
        except Task.DoesNotExist:
            return Response(
                {'detail': 'Task not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        board = task.board
        
        # Check if user is board member (403 if not)
        if (board.owner != user and
                not board.members.filter(id=user.id).exists()):
            return Response(
                {'detail': 'Forbidden. You must be a member of the board.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check if comment exists
        try:
            comment = Comment.objects.get(id=comment_id, task=task)
        except Comment.DoesNotExist:
            return Response(
                {'detail': 'Comment not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if user is comment author (403 if not)
        if comment.author != user:
            return Response(
                {'detail': 'Forbidden. Only the comment author can delete it.'},
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

"""Admin configuration for task app."""

from django.contrib import admin

from .models import Comment, Task


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    """Admin interface for Task model."""

    list_display = ['title', 'board', 'status', 'priority', 'assignee',
                    'due_date']
    list_filter = ['status', 'priority', 'board']
    search_fields = ['title', 'description']


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    """Admin interface for Comment model."""

    list_display = ['task', 'author', 'created_at', 'content']
    list_filter = ['created_at']
    search_fields = ['content', 'author__username']
    
    

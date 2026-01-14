"""Serializers for task API endpoints."""

from django.contrib.auth import get_user_model
from rest_framework import serializers

from board.models import Board
from tasks.models import Comment, Task

User = get_user_model()


class UserMinimalSerializer(serializers.ModelSerializer):
    """Minimal user data for assignee/reviewer."""

    fullname = serializers.CharField(source='username')

    class Meta:
        model = User
        fields = ['id', 'email', 'fullname']


class TaskSerializer(serializers.ModelSerializer):
    """Serializer for task operations."""

    assignee = UserMinimalSerializer(read_only=True)
    reviewer = UserMinimalSerializer(read_only=True)
    comments_count = serializers.SerializerMethodField()

    assignee_id = serializers.IntegerField(
        write_only=True,
        required=False,
        allow_null=True
    )
    reviewer_id = serializers.IntegerField(
        write_only=True,
        required=False,
        allow_null=True
    )

    class Meta:
        model = Task
        fields = [
            'id',
            'board',
            'title',
            'description',
            'status',
            'priority',
            'assignee',
            'assignee_id',
            'reviewer',
            'reviewer_id',
            'due_date',
            'comments_count'
        ]
        read_only_fields = ['id', 'comments_count']

    def to_representation(self, instance):
        """Convert 'reviewing' to 'review' for frontend compatibility."""
        data = super().to_representation(instance)
        if data['status'] == 'reviewing':
            data['status'] = 'review'
        return data

    def get_comments_count(self, obj):
        """Return the number of comments for this task."""
        if hasattr(obj, 'comments'):
            return obj.comments.count()
        return 0

    def validate_board(self, value):
        """Validate that the board exists and user has access."""
        user = self.context['request'].user

        try:
            board = Board.objects.get(id=value.id)
        except Board.DoesNotExist:
            raise serializers.ValidationError("Board does not exist")

        if (board.owner != user and
                not board.members.filter(id=user.id).exists()):
            raise serializers.ValidationError(
                "You must be a member of the board to create a task"
            )

        return value

    def validate_status(self, value):
        """Validate status field."""
        valid_statuses = ['to-do', 'in-progress', 'review', 'done']
        if value not in valid_statuses:
            raise serializers.ValidationError(
                f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
            )
        return value

    def validate_priority(self, value):
        """Validate priority field."""
        valid_priorities = ['low', 'medium', 'high']
        if value not in valid_priorities:
            raise serializers.ValidationError(
                f"Invalid priority. Must be one of: "
                f"{', '.join(valid_priorities)}"
            )
        return value

    def validate_assignee_id(self, value):
        """Validate that assignee exists."""
        if value is None:
            return value

        try:
            User.objects.get(id=value)
        except User.DoesNotExist:
            raise serializers.ValidationError(
                "Assignee user does not exist"
            )

        return value

    def validate_reviewer_id(self, value):
        """Validate that reviewer exists."""
        if value is None:
            return value

        try:
            User.objects.get(id=value)
        except User.DoesNotExist:
            raise serializers.ValidationError(
                "Reviewer user does not exist"
            )

        return value

    def validate(self, attrs):
        """Cross-field validation."""
        board = attrs.get('board')
        assignee_id = attrs.get('assignee_id')
        reviewer_id = attrs.get('reviewer_id')

        if assignee_id:
            assignee = User.objects.get(id=assignee_id)
            if (board.owner != assignee and
                    not board.members.filter(id=assignee.id).exists()):
                raise serializers.ValidationError({
                    'assignee_id': 'Assignee must be a member of the board'
                })

        if reviewer_id:
            reviewer = User.objects.get(id=reviewer_id)
            if (board.owner != reviewer and
                    not board.members.filter(id=reviewer.id).exists()):
                raise serializers.ValidationError({
                    'reviewer_id': 'Reviewer must be a member of the board'
                })

        return attrs

    def create(self, validated_data):
        """Create task with assignee and reviewer."""
        assignee_id = validated_data.pop('assignee_id', None)
        reviewer_id = validated_data.pop('reviewer_id', None)

        task = Task.objects.create(**validated_data)

        if assignee_id:
            task.assignee = User.objects.get(id=assignee_id)

        if reviewer_id:
            task.reviewer = User.objects.get(id=reviewer_id)

        task.save()
        return task

    def update(self, instance, validated_data):
        """Update task fields."""
        assignee_id = validated_data.pop('assignee_id', None)
        reviewer_id = validated_data.pop('reviewer_id', None)

        instance.title = validated_data.get('title', instance.title)
        instance.description = validated_data.get(
            'description',
            instance.description
        )
        instance.status = validated_data.get('status', instance.status)
        instance.priority = validated_data.get('priority', instance.priority)
        instance.due_date = validated_data.get('due_date', instance.due_date)

        if assignee_id is not None:
            if assignee_id == 0 or assignee_id == '':
                instance.assignee = None
            else:
                instance.assignee = User.objects.get(id=assignee_id)

        if reviewer_id is not None:
            if reviewer_id == 0 or reviewer_id == '':
                instance.reviewer = None
            else:
                instance.reviewer = User.objects.get(id=reviewer_id)

        instance.save()
        return instance


class CommentSerializer(serializers.ModelSerializer):
    """Serializer for comment operations."""

    author = serializers.CharField(source='author.username', read_only=True)

    class Meta:
        model = Comment
        fields = ['id', 'created_at', 'author', 'content']
        read_only_fields = ['id', 'created_at', 'author']
        

    
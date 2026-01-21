"""Serializers for board API endpoints."""

from django.contrib.auth import get_user_model
from rest_framework import serializers

from board.models import Board

User = get_user_model()


class BoardSerializer(serializers.ModelSerializer):
    """Serializer for board list and create operations."""

    member_count = serializers.SerializerMethodField()
    ticket_count = serializers.SerializerMethodField()
    tasks_to_do_count = serializers.SerializerMethodField()
    tasks_high_prio_count = serializers.SerializerMethodField()
    owner_id = serializers.IntegerField(source='owner.id', read_only=True)
    members = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False,
        allow_empty=True
    )

    class Meta:
        model = Board
        fields = [
            'id',
            'title',
            'member_count',
            'ticket_count',
            'tasks_to_do_count',
            'tasks_high_prio_count',
            'owner_id',
            'members'
        ]
        read_only_fields = ['id', 'owner_id']

    def get_member_count(self, obj):
        """Return the number of board members."""
        return obj.members.count()

    def get_ticket_count(self, obj):
        """Return the total number of tasks."""
        try:
            from tasks.models import Task
            return Task.objects.filter(board=obj).count()
        except Exception:
            return 0

    def get_tasks_to_do_count(self, obj):
        """Return the number of tasks with 'to-do' status."""
        try:
            from tasks.models import Task
            return Task.objects.filter(board=obj, status='to-do').count()
        except Exception:
            return 0

    def get_tasks_high_prio_count(self, obj):
        """Return the number of high priority tasks."""
        try:
            from tasks.models import Task
            return Task.objects.filter(board=obj, priority='high').count()
        except Exception:
            return 0

    def create(self, validated_data):
        """Create a new board with members."""
        member_ids = validated_data.pop('members', [])
        board = Board.objects.create(**validated_data)
        board.members.add(board.owner)

        if member_ids:
            valid_users = User.objects.filter(id__in=member_ids)
            if valid_users.count() != len(member_ids):
                invalid_ids = (
                    set(member_ids) -
                    set(valid_users.values_list('id', flat=True))
                )
                raise serializers.ValidationError(
                    f"Invalid user IDs: {list(invalid_ids)}"
                )
            board.members.add(*valid_users)

        return board

    def validate_members(self, value):
        """Validate members list."""
        if not isinstance(value, list):
            raise serializers.ValidationError(
                "Members must be a list of user IDs"
            )
        
        # Check if all member IDs exist
        if value:  # Only check if list is not empty
            valid_users = User.objects.filter(id__in=value)
            if valid_users.count() != len(value):
                invalid_ids = (
                    set(value) -
                    set(valid_users.values_list('id', flat=True))
                )
                raise serializers.ValidationError(
                    f"Invalid user IDs: {list(invalid_ids)}"
                )
        
        return value

    def update(self, instance, validated_data):
        """Update board title and/or members."""
        instance.title = validated_data.get('title', instance.title)
        instance.save()

        if 'members' in validated_data:
            member_ids = validated_data['members']
            # Members are already validated in validate_members
            valid_users = User.objects.filter(id__in=member_ids)

            instance.members.clear()
            instance.members.add(instance.owner)
            if valid_users.exists():
                instance.members.add(*valid_users)

        return instance


class BoardDetailSerializer(serializers.ModelSerializer):
    """Serializer for detailed board view with tasks and members."""

    member_count = serializers.SerializerMethodField()
    ticket_count = serializers.SerializerMethodField()
    tasks_to_do_count = serializers.SerializerMethodField()
    tasks_high_prio_count = serializers.SerializerMethodField()
    owner_id = serializers.IntegerField(source='owner.id', read_only=True)
    owner_data = serializers.SerializerMethodField()
    tasks = serializers.SerializerMethodField()
    members = serializers.SerializerMethodField()
    members_data = serializers.SerializerMethodField()

    class Meta:
        model = Board
        fields = [
            'id',
            'title',
            'member_count',
            'ticket_count',
            'tasks_to_do_count',
            'tasks_high_prio_count',
            'owner_id',
            'owner_data',
            'tasks',
            'members',
            'members_data'
        ]
        read_only_fields = ['id', 'owner_id']

    def get_member_count(self, obj):
        """Return the number of board members."""
        return obj.members.count()
    
    def get_owner_data(self, obj):
        """Return owner details."""
        return {
            'id': obj.owner.id,
            'email': obj.owner.email,
            'fullname': obj.owner.username
        }

    def get_members(self, obj):
        """Return full member details (for backward compatibility)."""
        members_list = obj.members.all()
        return [
            {
                'id': member.id,
                'email': member.email,
                'fullname': member.username
            }
            for member in members_list
        ]

    def get_members_data(self, obj):
        """Return full member details."""
        members_list = obj.members.all()
        return [
            {
                'id': member.id,
                'email': member.email,
                'fullname': member.username
            }
            for member in members_list
        ]

    def get_tasks(self, obj):
        """Return all tasks for this board."""
        try:
            from tasks.models import Task
            from tasks.api.serializers import TaskSerializer
            tasks = Task.objects.filter(board=obj)
            return TaskSerializer(tasks, many=True).data
        except Exception as e:
            print(f"Error getting tasks: {e}")
            return []

    def get_ticket_count(self, obj):
        """Return the total number of tasks."""
        try:
            from tasks.models import Task
            return Task.objects.filter(board=obj).count()
        except Exception as e:
            print(f"Error in ticket_count: {e}")
            return 0

    def get_tasks_to_do_count(self, obj):
        """Return the number of tasks with 'to-do' status."""
        try:
            from tasks.models import Task
            return Task.objects.filter(board=obj, status='to-do').count()
        except Exception as e:
            print(f"Error in tasks_to_do_count: {e}")
            return 0

    def get_tasks_high_prio_count(self, obj):
        """Return the number of high priority tasks."""
        try:
            from tasks.models import Task
            return Task.objects.filter(
                board=obj,
                priority='high'
            ).count()
        except Exception as e:
            print(f"Error in tasks_high_prio_count: {e}")
            return 0

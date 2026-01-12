from rest_framework import serializers
from board.models import Board
from django.contrib.auth import get_user_model

User = get_user_model()

class BoardSerializer(serializers.ModelSerializer):
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
        return obj.members.count()
    
    def get_ticket_count(self, obj):
        if hasattr(obj, 'tasks'):
            return obj.tasks.count()
        return 0
    
    def get_tasks_to_do_count(self, obj):
        if hasattr(obj, 'tasks'):
            return obj.tasks.filter(status='to-do').count()
        return 0
    
    def get_tasks_high_prio_count(self, obj):
        if hasattr(obj, 'tasks'):
            return obj.tasks.filter(priority='high').count()
        return 0
    
    def create(self, validated_data):
        member_ids = validated_data.pop('members', [])
        board = Board.objects.create(**validated_data)
        board.members.add(board.owner)
        
        if member_ids:
            valid_users = User.objects.filter(id__in=member_ids)
            if valid_users.count() != len(member_ids):
                invalid_ids = set(member_ids) - set(valid_users.values_list('id', flat=True))
                raise serializers.ValidationError(
                    f"Invalid user IDs: {list(invalid_ids)}"
                )
            board.members.add(*valid_users)
        
        return board
    
    def update(self, instance, validated_data):
        """
        Update board title and/or members
        """
        # Update title if provided
        instance.title = validated_data.get('title', instance.title)
        instance.save()
        
        # Update members if provided
        if 'members' in validated_data:
            member_ids = validated_data['members']
            
            # Validate that all user IDs exist
            valid_users = User.objects.filter(id__in=member_ids)
            if valid_users.count() != len(member_ids):
                invalid_ids = set(member_ids) - set(valid_users.values_list('id', flat=True))
                raise serializers.ValidationError(
                    f"Invalid user IDs: {list(invalid_ids)}"
                )
            
            # Replace members (keep owner in members)
            instance.members.clear()
            instance.members.add(instance.owner)  # Owner stays as member
            instance.members.add(*valid_users)
        
        return instance
    
    def validate_members(self, value):
        """Validate members list"""
        if not isinstance(value, list):
            raise serializers.ValidationError("Members must be a list of user IDs")
        return value
        
        

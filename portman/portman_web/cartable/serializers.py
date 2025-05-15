from rest_framework import serializers
from .models import Ticket, TicketComment, TicketReplication, Poll, PollChoice, PollVote, TaskList, Task, Reminder, Widget, TicketType
from users.models import User
from olt.serializers import OLTCabinetSerializerMini, FATSerializerMini, MicroductMapSerializer, CableMapSerializer, HandholeSerializer, BuildingSerializer
from filemanager.models import File as FileManagerFile
from filemanager.serializers import FileSerializer
from django.contrib.contenttypes.models import ContentType
import random
from django.utils import timezone
from datetime import timedelta
from django.utils.translation import gettext_lazy as _

class TicketTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = TicketType
        fields = ["id","name","title","en_title"]

class TaskSerializer(serializers.ModelSerializer):
    is_editable = serializers.CharField(read_only=True)
    assigned_users = serializers.SerializerMethodField(read_only=True)
    completed_by = serializers.SerializerMethodField(read_only=True)
    related_content = serializers.SerializerMethodField(read_only=True)
    files = serializers.SerializerMethodField('get_files', read_only=True)

    class Meta:
        model = Task
        fields = ['id', 'title', 'description', 'task_list', 'status', 'is_editable', 'due_date', 'done_date',
                  'created_at', 'assigned_users', 'completed_by', 'related_content', 'files']

    def get_files(self, task):
        files = FileManagerFile.objects.filter(object_id=task.id, content_type=ContentType.objects.get_for_model(task))
        return FileSerializer(files, many=True).data

    def get_assigned_users(self, obj):
        assigned_users = []
        for assignment in obj.taskassignment_set.all():
            assigned_users.append({
                'id': assignment.user.id,
                'username': assignment.user.username
            })
        return assigned_users

    def get_completed_by(self, obj):
        completed_by = []
        for assignment in obj.taskassignment_set.filter(status='completed'):
            completed_by.append({
                'id': assignment.user.id,
                'username': assignment.user.username
            })
        return completed_by

    def get_related_content(self, task):
        if task == None:
            return None
        contentType = task.content_object if task.object_id else None
        if contentType != None:
            result = None
            type =(task.content_type.model).replace("oltcabinet", "cabinet")
            if type == "cabinet" or type == "odc":
                result = OLTCabinetSerializerMini(contentType).data
            elif type == "fat":
                result = FATSerializerMini(contentType).data
                type = 'ffat' if (contentType.parent and contentType.is_otb == False) else ('otb' if contentType.is_otb else type)
                type = 'tb' if contentType.is_tb else type
            elif type == "microduct":
                result = MicroductMapSerializer(contentType).data
            elif type == "cable":
                result = CableMapSerializer(contentType).data
            elif type == "handhole":
                result = HandholeSerializer(contentType).data
            elif type == "building":
                result = BuildingSerializer(contentType).data

            if result:
                result['_type_'] = type
            return result
        return None


class TaskListSerializer(serializers.ModelSerializer):
    tasks = serializers.SerializerMethodField(read_only=True, source='get_tasks')

    class Meta:
        model = TaskList
        fields = ['id', 'title', 'created_by', 'created_at', 'tasks']

    def get_tasks(self, obj):
        tasks = obj.task_set.filter(deleted_at__isnull=True)
        return TaskSerializer(tasks, many=True).data


class UserSerializer(serializers.ModelSerializer):
    online_status = serializers.SerializerMethodField('get_online_status', read_only=True, required=False)
    full_name = serializers.SerializerMethodField('get_full_name', read_only=True, required=False)
    fa_full_name = serializers.SerializerMethodField('get_fa_full_name', read_only=True, required=False)

    def get_full_name(self, obj):
        return str(obj.first_name) + " " + str(obj.last_name)

    def get_fa_full_name(self, obj):
        if obj.fa_first_name == None:
            return self.get_full_name(obj=obj)
        return str(obj.fa_first_name) + " " + str(obj.fa_last_name)

    def get_online_status(self, obj):

        if obj.last_login and (timezone.now() - obj.last_login) < timedelta(days=1):
            return 'on'
        return 'off'  

    class Meta:
        model = User
        fields = (
            'id', 'email', 'first_name', 'last_name', 'online_status', 'full_name', 'fa_first_name', 'fa_last_name', 'fa_full_name'
        )


class FilteredListSerializer(serializers.ListSerializer):
    def to_representation(self, data):
        data = data.filter(deleted_at__isnull=True)
        return super().to_representation(data)


class TicketCommentReplySerializer(serializers.ModelSerializer):
    commentor = UserSerializer(source='user', read_only=True)

    class Meta:
        model = TicketComment
        fields = "__all__"
        list_serializer_class = FilteredListSerializer


class TicketCommentSerializer(serializers.ModelSerializer):
    commentor = UserSerializer(source='user', read_only=True)
    in_reply_comment = TicketCommentReplySerializer(source='in_reply_to', read_only=True, allow_null=True)

    class Meta:
        model = TicketComment
        fields = "__all__"


class TicketReplicationSerializer(serializers.ModelSerializer):
    receiver_info = UserSerializer(source='receiver', read_only=True)

    class Meta:
        model = TicketReplication
        fields = "__all__"


class VoterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username']


class PollChoiceSerializer(serializers.ModelSerializer):
    vote_count = serializers.IntegerField(read_only=True)
    voters = serializers.SerializerMethodField(source='get_voters')

    class Meta:
        model = PollChoice
        fields = ['id', 'text', 'poll', 'vote_count', 'voters']

    def get_voters(self, obj):
        return VoterSerializer(User.objects.filter(pollvote__choice=obj), many=True).data


class PollVoteSerializer(serializers.ModelSerializer):
    voter_info = VoterSerializer(read_only=True, source='voter')
    created_at = serializers.DateTimeField(read_only=True)

    class Meta:
        model = PollVote
        fields = ['id', 'voter', 'choice', 'voter_info', 'created_at']


class PollSerializer(serializers.ModelSerializer):
    creator_info = VoterSerializer(read_only=True, source='creator')
    total_votes = serializers.ReadOnlyField(read_only=True)
    winning_choices = PollChoiceSerializer(many=True, read_only=True)
    choice_set = PollChoiceSerializer(many=True, read_only=True, source='pollchoice_set')
    is_expired = serializers.SerializerMethodField()

    class Meta:
        model = Poll
        fields = ['id', 'title', 'question_text', 'creator', 'is_active', 'is_anonymous', 'allow_revote',
                  'max_choices', 'type', 'results_visibility', 'start_date', 'end_date', 'creator_info', 'choice_set',
                  'total_votes', 'winning_choices', 'is_expired']

    def get_is_expired(self, obj):
        return obj.end_date < timezone.now() if obj.end_date else False

    # def get_is_vote_allowed(self, obj):
    #     user = self.context['request'].user
    #     return obj.is_vote_allowed(user)
    #
    # def get_can_view_results(self, obj):
    #     user = self.context['request'].user
    #     return obj.can_view_results(user)


class ReminderSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Reminder
        fields = ['id', 'user', 'title', 'description', 'reminder_time', 'sending_methods', 'status', 'status_display',
                  'is_complete']
        read_only_fields = ['is_complete']

    def validate_reminder_time(self, value):
        if value <= timezone.now():
            raise serializers.ValidationError(_("Reminder time must be in the future."))
        return value


class TicketSerializer(serializers.ModelSerializer):

    creator_info = UserSerializer(source='creator', read_only=True)
    replications = TicketReplicationSerializer(many=True, read_only=True, source='ticketreplication_set')
    comments = TicketCommentSerializer(many=True, read_only=True, source='ticketcomment_set')
    properties = serializers.SerializerMethodField('get_properties', read_only=True, required=False)
    status_label = serializers.CharField(read_only=True)
    files = serializers.SerializerMethodField('get_files', read_only=True)
    tasklists = serializers.SerializerMethodField(read_only=True)
    polls = serializers.SerializerMethodField(read_only=True)
    type_info = TicketTypeSerializer(source='type', read_only=True)
    permissions = serializers.SerializerMethodField(read_only=True)

    def get_permissions(self, ticket):
        request = self.context.get('request', None)
        canEdit = request.user.id == ticket.creator.id if request else False
        return {
            'can_edit': canEdit,
            'can_done': canEdit,
            'can_delete': canEdit,
            'can_poll': canEdit,
            'can_tasklist': canEdit
        }

    def get_files(self, ticket):
        files = FileManagerFile.objects.filter(object_id=ticket.id, content_type=ContentType.objects.get_for_model(ticket))
        return FileSerializer(files, many=True).data

    def get_properties(self, ticket):
        request = self.context.get('request', None)
        user = request.user if request else ticket.creator
        replication = TicketReplication.objects.filter(ticket=ticket, receiver=user).first()
        return dict(pin_at=replication.pin_at, bookmark_at=replication.bookmark_at, read_at=replication.read_at) if replication else {}

    def get_tasklists(self, ticket):
        tasklistIds = Widget.objects.filter(ticket=ticket, content_type=ContentType.objects.get_for_model(TaskList), deleted_at__isnull=True).values_list('object_id', flat=True)
        if len(tasklistIds) == 0:
            return [] 

        tasklists = TaskList.objects.filter(id__in=tasklistIds, deleted_at__isnull=True)
        return TaskListSerializer(tasklists, many=True).data

    def get_polls(self, ticket):
        pollIds = Widget.objects.filter(ticket=ticket, content_type=ContentType.objects.get_for_model(Poll), deleted_at__isnull=True).values_list('object_id', flat=True)
        if len(pollIds) == 0:
            return [] 

        polls = Poll.objects.filter(id__in=pollIds, deleted_at__isnull=True)
        return PollSerializer(polls, many=True).data

    class Meta:
        model = Ticket
        fields = "__all__"

from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from rest_framework import pagination, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from .models import *
from .serializers import *
# from .signals import *
from django.db.models import Q, F
from django.db import transaction
from datetime import datetime
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import PermissionDenied
from users.models import User
from rest_framework.exceptions import ValidationError
from django.utils.translation import gettext as _


class TicketViewSet(ModelViewSet):

    permission_classes = (IsAuthenticated,)
    serializer_class = TicketSerializer

    def make_queryset(self):
        #created_tickets = Q(creator=self.request.user)
        received_tickets = Q(ticketreplication__receiver=self.request.user)
        queryset = Ticket.objects.filter(received_tickets).distinct().exclude(deleted_at__isnull=False)
        return queryset

    def get_queryset(self):
        id = self.request.query_params.get('id', None)
        criteria = self.request.query_params.get('criteria', None)
        searchPhrase = self.request.query_params.get('search_phrase', None)
        page_size = self.request.query_params.get('page_size', 10)
        if int(page_size) < 1 or int(page_size) > 100:
            page_size = 10
        pagination.PageNumberPagination.page_size = page_size

        queryset = self.make_queryset()
        if id is not None and int(id) > 0:
            queryset = queryset.filter(pk=id)
        
        if criteria in ('not-read', 'not-done', 'bookmarks'):
            if (criteria == 'not-read'):
                queryset = queryset.filter(ticketreplication__read_at__isnull=True, ticketreplication__receiver=self.request.user)
            elif (criteria == "not-done"):
                queryset = queryset.filter(done_at__isnull=True)
            else:
                queryset = queryset.filter(ticketreplication__bookmark_at__isnull=False, ticketreplication__receiver=self.request.user)

        if searchPhrase:
            queryset = queryset.filter(pk=searchPhrase) if searchPhrase.isnumeric() else queryset
            queryset = queryset.filter(Q(subject__icontains=searchPhrase)| Q(body__icontains=searchPhrase))

        return queryset 

    def create(self, request, *args, **kwargs):
        request.data['creator'] = request.user.id
        receivers = request.data.get('receivers', [])
        serializer = TicketSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        def mapContentType(objectType):
            if objectType in ['fat', 'ffat', 'otb', 'tb']:
                return 'fat'
            elif objectType in ['cabinet', 'oltcabinet']:
                return 'oltcabinet'
            elif objectType in ['t']:
                return 'handhole'
            return objectType

        def addTaskListToTicket(ticket):
            taskList = None
            if request.data.get('task_list_title', False):
                taskListSerializer = TaskListSerializer(data={'title': request.data.get('task_list_title', ""), 'created_by': request.user.id})
                taskListSerializer.is_valid(raise_exception=True)
                taskList = taskListSerializer.save()
                taskList.add_to_widget(ticket)
            
            if taskList is not None and request.data.get('task_list_items'):
                for taskListItem in request.data.get('task_list_items'):
                    taskListItem['task_list'] = taskList.id
                    taskListItemSerializer = TaskSerializer(data=taskListItem)
                    taskListItemSerializer.is_valid(raise_exception=True)

                    taskObjectType = mapContentType(taskListItem['object_type'])
                    if taskObjectType != None:
                        taskListItemSerializer.validated_data['object_id'] = taskListItem['object_id']
                        taskListItemSerializer.validated_data['content_type'] = ContentType.objects.get(model=taskObjectType)
                        
                    taskListItemSerializer.save()

        with transaction.atomic():
            objectType = mapContentType(request.data.get('object_type', None))
            if objectType != None:
                serializer.validated_data['content_type'] = ContentType.objects.get(model=objectType)
            self.perform_create(serializer)

            for receiverId in receivers:
                if isinstance(receiverId, int) and receiverId != request.user.id:
                    TicketReplication.objects.create(ticket=serializer.instance, receiver=User.objects.get(pk=receiverId))
            
            TicketReplication.objects.create(ticket=serializer.instance, receiver=request.user, read_at=datetime.now()) # a copy for creator

            addTaskListToTicket(serializer.instance)

        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=self.get_success_headers(serializer.data))
    
    def update(self, request, *args, **kwargs):
        instance = self.get_object()

        # Check for user permissions
        if instance.creator.id != request.user.id:
            raise ValidationError({'results': "Access Denied"})

        request.data['creator'] = request.user.id
        serializer = self.serializer_class(instance, data=request.data)
        receivers = request.data.get('receivers', [])
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            self.perform_update(serializer)
            allReplications = TicketReplication.objects.filter(ticket=instance).exclude(receiver=instance.creator)
            deletedReplications = allReplications.exclude(receiver__in=receivers)
            deletedReplications.delete()

            newReceivers = list(set(receivers) - set(list(allReplications.values_list('receiver_id', flat=True))))
            for receiverId in newReceivers:
                if isinstance(receiverId, int) and receiverId != request.user.id:
                    TicketReplication.objects.create(ticket=instance, receiver=User.objects.get(pk=receiverId))

        return Response(serializer.data, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        # Check for user permissions
        if instance.creator.id != request.user.id:
            raise ValidationError({'results': "Access Denied"})
        instance.deleted_at = datetime.now()
        instance.save()
        return Response({'results': _("Ticket deleted"), 'status': status.HTTP_204_NO_CONTENT})
        #return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=["get"])
    def stats(self, request):
        queryset = TicketReplication.objects.filter(receiver=request.user, ticket__deleted_at__isnull=True)
        unreadTicketsCount = queryset.filter(read_at__isnull=True).count()
        unreadTickets = self.make_queryset().filter(ticketreplication__receiver=request.user, ticketreplication__read_at__isnull=True) [0:5]
        bookmarkedTicketsCount = queryset.filter(bookmark_at__isnull=True).count()
        return Response({'results': {
            "unread_tickets_count" : unreadTicketsCount,
            "unread_tickets": TicketSerializer(unreadTickets, many=True).data,
            "bookmarked_tickets_count" : bookmarkedTicketsCount,
            "x": request.user.id,
        }, 'status': status.HTTP_200_OK})


    @action(detail=True, methods=["post"])
    def read(self, request, pk=None):
        ticket = self.get_object()
        try:
            replication = TicketReplication.objects.get(ticket=ticket, receiver=request.user)
            replication.read_at = datetime.now()
            replication.save()
            
        except TicketReplication.DoesNotExist:
            pass
        
        return Response(_("Marked as read"), status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=["post"])
    def bookmark(self, request, pk=None):
        ticket = self.get_object()
        try:
            replication = TicketReplication.objects.get(ticket=ticket, receiver=request.user)
            replication.bookmark_at = datetime.now() if replication.bookmark_at == None else None
            replication.save()
            
        except TicketReplication.DoesNotExist:
            pass
        
        return Response(_("Bookmarked"), status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def pin(self, request, pk=None):
        ticket = self.get_object()
        try:
            replication = TicketReplication.objects.get(ticket=ticket, receiver=request.user)
            replication.pin_at = datetime.now() if replication.pin_at == None else None
            replication.save()
            
        except TicketReplication.DoesNotExist:
            pass
        
        return Response(_("Pinned"), status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def done(self, request, pk=None):
        ticket = self.get_object()
        if ticket.status == Ticket.STATUS_OPEN:
            ticket.status = Ticket.STATUS_DONE
            ticket.done_at = datetime.now()
            ticket.updated_at = datetime.now()
            ticket.save()
        
        return Response(_("Marked as done"), status=status.HTTP_201_CREATED)

    ## COMMENTS ...

    @action(detail=True, methods=["post"])
    def comment(self, request, pk=None):
        ticket = self.get_object()
        request.data['ticket'] = ticket.id
        request.data['user'] = request.user.id
        serializer = TicketCommentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            ticket.updated_at = datetime.now()
            ticket.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['delete'], url_path='delete_comment/(?P<comment_pk>[^/.]+)')
    def delete_comment(self, request, pk=None, comment_pk=None):
        ticket = self.get_object()
        try:
            comment = TicketComment.objects.get(pk=comment_pk, ticket=ticket, user=request.user)
            comment.deleted_at = datetime.now()
            comment.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except TicketComment.DoesNotExist:
            return Response(status=status.HTTP_403_FORBIDDEN)


class PollViewSet(ModelViewSet):
    permission_classes = (IsAuthenticated,)
    serializer_class = PollSerializer

    def make_queryset(self):
        poll_content_type = ContentType.objects.get_for_model(Poll)
        queryset = Poll.objects.filter(id__in=Widget.objects.filter(content_type=poll_content_type,
                                                                    ticket__id=self.kwargs.get('ticket_id')).exclude(
                                                                    deleted_at__isnull=False).values_list('object_id', flat=True))
        queryset = queryset.exclude(deleted_at__isnull=False)
        return queryset

    def get_queryset(self):
        page_size = self.request.query_params.get('page_size', 10)
        if int(page_size) < 1 or int(page_size) > 30:
            page_size = 10
        pagination.PageNumberPagination.page_size = page_size
        queryset = self.make_queryset()
        if self.request.user.id in self.allowed_users() or self.request.user.is_superuser:
            return queryset
        else:
            return queryset.none()

    def create(self, request, *args, **kwargs):
        request.data['creator'] = self.request.user.id
        serializer = PollSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        self.has_permission(instance.creator)
        if instance.total_votes > 0:
            end_date = request.data.get('end_date', None)
            if end_date:
                end_date = datetime.fromisoformat(end_date)
                instance.end_date = end_date
                instance.save()
            serializer = self.serializer_class(instance)
        else:
            request.data['creator'] = self.request.user.id
            partial = kwargs.pop('partial', True)
            instance = self.get_object()
            serializer = self.serializer_class(instance, data=request.data, partial=partial)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.has_permission(instance.creator)
        instance.soft_delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def perform_create(self, serializer):
        ticket = get_object_or_404(Ticket, pk=self.kwargs.get('ticket_id'))
        self.has_permission(ticket.creator)
        instance = serializer.save()
        instance.add_to_widget(ticket)
        self.create_choice(instance)

    def perform_update(self, serializer):
        instance = serializer.save()
        self.create_choice(instance)

    @action(detail=True, methods=['post'])
    def vote(self, request, *args, **kwargs):
        poll = self.get_object()
        self.can_vote()
        choice_ids = request.data.get('choice_ids')

        choices = PollChoice.objects.filter(id__in=choice_ids, poll=poll)

        if len(choices) != len(choice_ids):
            return Response({'error': _('One or more invalid choice_ids.')}, status=status.HTTP_400_BAD_REQUEST)

        previous_votes = PollVote.objects.filter(choice__poll=poll, voter=request.user)

        if previous_votes and not poll.allow_revote:
            return Response({'error': _("You have already voted in this poll, so you can't revote.")},
                            status=status.HTTP_400_BAD_REQUEST)

        PollChoice.objects.filter(id__in=list(previous_votes.values_list('choice', flat=True))).update(
            vote_count=F('vote_count') - 1)

        previous_votes.delete()
        votes = [PollVote(choice=choice, voter=request.user) for choice in choices]
        PollVote.objects.bulk_create(votes)

        # Update the vote counts for the chosen choices
        choices.update(vote_count=F('vote_count') + 1)

        serializer = PollVoteSerializer(votes, many=True)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def create_choice(self, poll):
        text_choices = self.request.data.get('choices')
        poll.pollchoice_set.all().delete()
        choices = []
        for text in text_choices:
            choices.append(PollChoice.objects.create(poll=poll, text=text))
        serializer = PollChoiceSerializer(choices, many=True)
        return serializer.data

    def has_permission(self, creator=None):
        if creator and (creator == self.request.user or self.request.user.is_superuser):
            return True
        else:
            raise PermissionDenied(_("You do not have permission."))

    def can_vote(self):
        poll = self.get_object()
        choice_ids = self.request.data.get('choice_ids')
        allowed_users = self.allowed_users()
        if self.request.user.id not in allowed_users:
            raise PermissionDenied(_("You do not have permission to vote in this poll."))

        if not choice_ids:
            return Response({'error': _('No choices selected.')}, status=status.HTTP_400_BAD_REQUEST)

        if len(choice_ids) > 1 and poll.type == 'single_choice':
            return Response({'error': _('You can vote just one choice.')}, status=status.HTTP_400_BAD_REQUEST)

    def allowed_users(self):
        ticket = get_object_or_404(Ticket, pk=self.kwargs.get('ticket_id'))
        allowed_users = TicketReplication.objects.filter(ticket=ticket).values_list(
            'receiver', flat=True)
        allowed_users = list(allowed_users) + [ticket.creator.id]
        return allowed_users


class CartableTaskListViewSet(ModelViewSet):
    permission_classes = (IsAuthenticated,)
    serializer_class = TaskListSerializer

    def make_queryset(self):
        task_list_content_type = ContentType.objects.get_for_model(TaskList)
        queryset = TaskList.objects.filter(id__in=Widget.objects.filter(content_type=task_list_content_type,
                                                                        ticket__id=self.kwargs.get('ticket_id')).exclude(
                                                                        deleted_at__isnull=False).values_list('object_id', flat=True))
        queryset = queryset.exclude(deleted_at__isnull=False)
        return queryset

    def get_queryset(self):
        page_size = self.request.query_params.get('page_size', 10)
        if int(page_size) < 1 or int(page_size) > 30:
            page_size = 10
        pagination.PageNumberPagination.page_size = page_size
        queryset = self.make_queryset()
        return queryset

    def create(self, request, *args, **kwargs):
        request.data['created_by'] = self.request.user.id
        serializer = TaskListSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        request.data['created_by'] = self.request.user.id
        partial = kwargs.pop('partial', True)
        instance = self.get_object()
        serializer = self.serializer_class(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        creator = get_object_or_404(Ticket, pk=self.kwargs.get('ticket_id')).creator
        self.is_valid(creator)
        instance.soft_delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def perform_create(self, serializer):
        ticket = get_object_or_404(Ticket, pk=self.kwargs.get('ticket_id'))
        self.is_valid(ticket.creator)
        instance = serializer.save()
        instance.add_to_widget(ticket)

    def perform_update(self, serializer):
        instance = self.get_object()
        self.is_valid(instance.created_by)
        serializer.save()

    def is_valid(self, creator=None):
        if creator and (creator == self.request.user or self.request.user.is_superuser):
            return True
        else:
            raise PermissionDenied(_("You do not have permission."))


class CartableTaskViewSet(ModelViewSet):
    permission_classes = (IsAuthenticated,)
    serializer_class = TaskSerializer

    def get_queryset(self):
        page_size = self.request.query_params.get('page_size', 10)
        if int(page_size) < 1 or int(page_size) > 30:
            page_size = 10
        pagination.PageNumberPagination.page_size = page_size
        queryset = Task.objects.filter(task_list__id=self.kwargs.get('task_list_id')).exclude(deleted_at__isnull=False)
        return queryset

    def create(self, request, *args, **kwargs):
        request.data['task_list'] = self.kwargs.get('task_list_id')
        serializer = TaskSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', True)
        instance = self.get_object()
        serializer = self.serializer_class(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        creator = get_object_or_404(TaskList, pk=self.kwargs.get('task_list_id')).created_by
        self.is_valid(creator)
        instance.soft_delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def perform_create(self, serializer):
        creator = get_object_or_404(TaskList, pk=self.kwargs.get('task_list_id')).created_by
        self.is_valid(creator)
        task = Task(**serializer.validated_data)
        task.clean()
        serializer.save()

    def perform_update(self, serializer):
        instance = self.get_object()
        self.is_valid(instance.task_list.created_by)
        task = Task(**serializer.validated_data)
        task.clean()
        serializer.save()

    @action(detail=True, methods=["post"], url_path='mark-done')
    def mark_as_done(self, request, *args, **kwargs):
        self.can_mark()
        task = self.get_object()
        task.mark_as_done()
        TaskAssignment.objects.filter(task=task).update(status='completed')
        return Response(_("Marked as done."), status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], url_path='mark-in-progress')
    def mark_as_in_progress(self, request, *args, **kwargs):
        self.can_mark()
        task = self.get_object()
        task.mark_as_in_progress()
        TaskAssignment.objects.filter(task=task).update(status='in_progress')

        return Response(_("Marked as in progress."), status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], url_path='mark-to-do')
    def mark_as_to_do(self, request, *args, **kwargs):
        self.can_mark()
        task = self.get_object()
        task.mark_as_to_do()
        TaskAssignment.objects.filter(task=task).update(status='assigned')
        # if request.user == task.task_list.created_by or request.user.is_superuser:
        #     task.mark_as_to_do()
        #     TaskAssignment.objects.filter(task=task).update(status='assigned')
        # else:
        #     TaskAssignment.objects.filter(task=task, user=request.user).update(status='assigned')

        return Response(_("Marked as to do."), status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], url_path='assign-to-user')
    def assign_to_user(self, request, *args, **kwargs):
        creator = get_object_or_404(TaskList, pk=self.kwargs.get('task_list_id')).created_by
        self.is_valid(creator)
        task = self.get_object()
        users_id = request.data.get('users_id')
        users = User.objects.filter(id__in=users_id)
        for user in users:
            task.assign_to_user(user)
        return Response(_("Assigned to users."), status=status.HTTP_201_CREATED)

    def is_valid(self, creator=None):
        if creator and (creator == self.request.user or self.request.user.is_superuser):
            return True
        else:
            raise PermissionDenied(_("You do not have permission."))

    def can_mark(self):
        task = self.get_object()
        assigned_users_id = task.taskassignment_set.all().values_list('user', flat=True)
        widget = Widget.objects.filter(content_type=ContentType.objects.get_for_model(task.task_list),
                                       object_id=task.task_list.id,
                                       deleted_at__isnull=True
                                       ).first()
        if widget:
            ticket = widget.ticket
            allowed_users_id = TicketReplication.objects.filter(ticket=ticket).values_list('receiver_id', flat=True)
            assigned_users_id = list(assigned_users_id) + list(allowed_users_id)
        owner = task.task_list.created_by
        allowed_users_id = list(assigned_users_id) + [owner.id]

        if self.request.user.id in allowed_users_id or self.request.user.is_superuser:
            # if self.request.user is not owner and task.status is not TaskStatus.DONE and not self.request.user.is_superuser:
            #     raise ValidationError(dict(ditail=_("Because the task's status was changed to Done by its owner, you cannot change it.")))
            return True
        else:
            raise PermissionDenied(_("You do not have permission."))
        

class ReminderViewSet(ModelViewSet):
    permission_classes = (IsAuthenticated,)
    serializer_class = ReminderSerializer

    def make_queryset(self):
        reminder_content_type = ContentType.objects.get_for_model(Reminder)
        queryset = Reminder.objects.filter(id__in=Widget.objects.filter(content_type=reminder_content_type,
                                                                        ticket__id=self.kwargs.get(
                                                                            'ticket_id')).exclude(
            deleted_at__isnull=False).values_list('object_id', flat=True))
        queryset = queryset.exclude(deleted_at__isnull=False)
        return queryset

    def get_queryset(self):
        page_size = self.request.query_params.get('page_size', 10)
        if int(page_size) < 1 or int(page_size) > 30:
            page_size = 10
        pagination.PageNumberPagination.page_size = page_size
        queryset = self.make_queryset()
        if self.request.user.id in self.allowed_users() or self.request.user.is_superuser:
            return queryset
        else:
            return queryset.none()
        
    def create(self, request, *args, **kwargs):

        request.data['user'] = self.request.user.id
        serializer = ReminderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', True)
        instance = self.get_object()
        self.has_permission(instance.user)
        serializer = self.serializer_class(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.has_permission(instance.user)
        instance.soft_delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def perform_create(self, serializer):
        ticket = get_object_or_404(Ticket, pk=self.kwargs.get('ticket_id'))
        self.has_permission(ticket.creator)
        self.is_reminder_time_valid(self.request.data.get('reminder_time'))
        instance = serializer.save()
        instance.add_to_widget(ticket)

    def perform_update(self, serializer):
        self.is_reminder_time_valid(self.request.data.get('reminder_time'))
        serializer.save()



    def is_reminder_time_valid(self, reminder_time):
        if reminder_time and datetime.fromisoformat(reminder_time) <= timezone.now():
            raise ValidationError({'reminder_time': _("Reminder time must be in the future.")})

    def allowed_users(self):
        ticket = get_object_or_404(Ticket, pk=self.kwargs.get('ticket_id'))
        allowed_users = TicketReplication.objects.filter(ticket=ticket).values_list(
            'receiver', flat=True)
        allowed_users = list(allowed_users) + [ticket.creator.id]
        return allowed_users

    def has_permission(self, creator=None):
        if creator and (creator == self.request.user or self.request.user.is_superuser):
            return True
        else:
            raise PermissionDenied(_("You do not have permission."))

class TicketTypeViewSet(ModelViewSet):
    permission_classes = (IsAuthenticated,)
    serializer_class = TicketTypeSerializer

    def get_queryset(self):
        queryset = TicketType.objects.all()
        return queryset
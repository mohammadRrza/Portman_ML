from django.db import models
from users.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from rest_framework.exceptions import ValidationError
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from datetime import datetime
from django.db import transaction
from django.utils.translation import gettext_lazy as _


class TimeFields(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    deleted_at = models.DateTimeField(blank=True, null=True, db_index=True)

    class Meta:
        abstract = True

class TicketType(models.Model):
    TYPE_PUBLIC = 'public'
    TYPE_FTTH_USER_INSTALL = 'ftth_user_install'
    TYPE_FTTH_PLAN_IMPLEMENTATION = 'ftth_plan_imp'
    TYPE_FTTH_PLAN_CHANGES = 'ftth_plan_changes'

    name = models.CharField(max_length=64)
    title = models.CharField(max_length=128)
    en_title = models.CharField(max_length=128, blank=True, null=True)


class Ticket(TimeFields):
    STATUS_OPEN  = 0
    STATUS_DONE = 20

    type = models.ForeignKey(TicketType, on_delete=models.DO_NOTHING, blank=True, null=True)
    subject = models.CharField(max_length=256)
    body = models.TextField(null=True, blank=True)
    creator = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    status = models.IntegerField(db_index=True, default=STATUS_OPEN, blank=True)
    done_at = models.DateTimeField(blank=True, null=True)
    content_type = models.ForeignKey(ContentType, on_delete=models.SET_NULL, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')

    @property
    def status_label(self):
        if self.status == self.STATUS_OPEN:
            return "Open"
        elif self.status == self.STATUS_DONE:
            return "Done"
        return "Unkonwn"

    class Meta:
        ordering = ['ticketreplication__pin_at', '-created_at']


class TicketReplication(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE)
    receiver = models.ForeignKey(User, on_delete=models.DO_NOTHING, db_index=True)
    read_at = models.DateTimeField(blank=True, null=True)
    bookmark_at = models.DateTimeField(blank=True, null=True)
    pin_at = models.DateTimeField(blank=True, null=True)


class TicketCommentManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=True)


class TicketComment(TimeFields):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING, db_index=True)
    in_reply_to = models.ForeignKey('self', on_delete=models.DO_NOTHING, blank=True, null=True)
    body = models.TextField(null=True, blank=True)

    objects = TicketCommentManager()

class Poll(TimeFields):
    title = models.CharField(max_length=200, null=True, blank=True)
    question_text = models.CharField(max_length=200)
    creator = models.ForeignKey(User, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    is_anonymous = models.BooleanField(default=True)
    allow_revote = models.BooleanField(default=True)
    max_choices = models.PositiveIntegerField(default=5, validators=[MinValueValidator(1), MaxValueValidator(10)])
    type = models.CharField(max_length=20,
                            choices=[('single_choice', 'Single Choice'), ('multiple_choice', 'Multiple Choice')])
    results_visibility = models.CharField(max_length=20,
                                          choices=[('immediate', 'Immediate'), ('after_end_date', 'After End Date'),
                                                   ('custom', 'Custom')],  default='immediate')
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.title

    def add_to_widget(self, ticket):
        Widget.objects.create(ticket=ticket, content_type=ContentType.objects.get_for_model(self), object_id=self.id)

    @property
    def total_votes(self):
        return self.pollchoice_set.aggregate(models.Sum('vote_count'))['vote_count__sum'] or 0

    def winning_choices(self):
        poll_choices = self.pollchoice_set.all()
        if not poll_choices:
            return []

        if self.type == 'single_choice':
            return [max(poll_choices, key=lambda c: c.vote_count)]
        else:
            max_votes = max(pc.vote_count for pc in poll_choices)
            return [pc for pc in poll_choices if pc.vote_count == max_votes]

    def is_vote_allowed(self, user):
        if not self.is_active:
            return False
        if self.allow_revote:
            return True
        return not PollVote.objects.filter(user=user, choice__poll=self).exists()

    def can_view_results(self, user):
        if self.results_visibility == 'immediate':
            return True
        elif self.results_visibility == 'after_end_date':
            return self.end_date < timezone.now()
        elif self.results_visibility == 'custom':
            # Implement custom result visibility logic here
            return False
        else:
            return False

    def soft_delete(self):
        with transaction.atomic():
            widgets = Widget.objects.filter(content_type=ContentType.objects.get_for_model(self), object_id=self.id)
            for widget in widgets:
                widget.soft_delete()

            self.deleted_at = datetime.now()
            self.save()


class PollChoice(models.Model):
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE)
    text = models.CharField(max_length=200)
    vote_count = models.IntegerField(default=0)

    def __str__(self):
        return self.text


class PollVote(models.Model):
    voter = models.ForeignKey(User, on_delete=models.CASCADE)
    choice = models.ForeignKey(PollChoice, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.voter.username} voted for {self.choice.text}"

    def clean(self):
        if not self.choice.poll.is_vote_allowed(self.voter):
            raise ValidationError(dict(error=_("You are not allowed to vote for this poll.")))

    class Meta:
        unique_together = ('voter', 'choice')
        ordering = ('-created_at',)


class TaskStatus(models.TextChoices):
    TO_DO = 'to do'
    IN_PROGRESS = 'in progress'
    DONE = 'done'


class TaskList(TimeFields):
    title = models.CharField(max_length=100)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return self.title

    def add_to_widget(self, ticket):
        Widget.objects.create(ticket=ticket, content_type=ContentType.objects.get_for_model(self), object_id=self.id)

    def soft_delete(self):
        with transaction.atomic():
            tasks = self.task_set.all().exclude(deleted_at__isnull=False)
            for task in tasks:
                task.soft_delete()

            widgets = Widget.objects.filter(content_type=ContentType.objects.get_for_model(self), object_id=self.id)
            for widget in widgets:
                widget.soft_delete()

            self.deleted_at = datetime.now()
            self.save()


class Task(TimeFields):
    title = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)
    task_list = models.ForeignKey(TaskList, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=TaskStatus.choices, default=TaskStatus.TO_DO)
    due_date = models.DateTimeField(null=True, blank=True)
    done_date = models.DateTimeField(null=True, blank=True)
    content_type = models.ForeignKey(ContentType, on_delete=models.SET_NULL, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return self.title

    def clean(self):
        if self.due_date and self.due_date < timezone.now():
            raise ValidationError(dict(error=_("Due date must be in the future.")))

    def mark_as_done(self):
        self.status = TaskStatus.DONE
        self.done_date = timezone.now()
        self.save()

    def mark_as_in_progress(self):
        self.status = TaskStatus.IN_PROGRESS
        self.done_date = None
        self.save()

    def mark_as_to_do(self):
        self.status = TaskStatus.TO_DO
        self.done_date = None
        self.save()

    def days_until_due(self):
        return (self.due_date - timezone.now()).days

    def is_editable(self):
        return False if self.done_date else True

    def assign_to_user(self, user):
        TaskAssignment.objects.create(task=self, user=user)

    def soft_delete(self):
        with transaction.atomic():
            task_assignments = self.taskassignment_set.all().exclude(deleted_at__isnull=False)
            for instance in task_assignments:
                instance.soft_delete()
            self.deleted_at = datetime.now()
            self.save()


class TaskAssignmentStatus(models.TextChoices):
    ASSIGNED = 'assigned'
    IN_PROGRESS = 'in_progress'
    COMPLETED = 'completed'


class TaskAssignment(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    assigned_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=TaskAssignmentStatus.choices,
                              default=TaskAssignmentStatus.ASSIGNED)
    deleted_at = models.DateTimeField(blank=True, null=True, db_index=True)

    def mark_as_complete(self):
        self.status = TaskAssignmentStatus.COMPLETED
        self.save()

    def soft_delete(self):
        self.deleted_at = datetime.now()
        self.save()


class Reminder(TimeFields):

    STATUS_INCOMPLETE = 0
    STATUS_COMPLETE = 10

    STATUS_CHOICES = (
        (STATUS_INCOMPLETE, 'Incomplete'),
        (STATUS_COMPLETE, 'Complete'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True,  related_name='reminders')
    title = models.CharField(max_length=200)
    description = models.TextField(null=True, blank=True)
    reminder_time = models.DateTimeField()
    sending_methods = models.CharField(max_length=20)
    status = models.IntegerField(choices=STATUS_CHOICES, default=STATUS_INCOMPLETE)
    meta = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"

    @property
    def is_complete(self):
        return self.status == self.STATUS_COMPLETE

    def mark_as_complete(self):
        self.status = self.STATUS_COMPLETE
        self.save()

    def mark_as_incomplete(self):
        self.status = self.STATUS_INCOMPLETE
        self.save()

    def add_to_widget(self, ticket):
        Widget.objects.create(ticket=ticket, content_type=ContentType.objects.get_for_model(self), object_id=self.id)

    def soft_delete(self):
        with transaction.atomic():
            widgets = Widget.objects.filter(content_type=ContentType.objects.get_for_model(self), object_id=self.id)
            for widget in widgets:
                widget.soft_delete()

            self.deleted_at = datetime.now()
            self.save()


class Widget(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    deleted_at = models.DateTimeField(blank=True, null=True, db_index=True)

    def soft_delete(self):
        self.deleted_at = datetime.now()
        self.save()

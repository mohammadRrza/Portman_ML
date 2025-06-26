from django.db import models
from django.utils import timezone
from users.models import User


class DeleteManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=True)


class TimeFields(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    deleted_at = models.DateTimeField(blank=True, null=True, db_index=True)

    objects = DeleteManager()

    class Meta:
        abstract = True

    def soft_delete(self):
        self.deleted_at = timezone.now()
        self.save()


class KnowledgeGraph(TimeFields):
    name = models.CharField(max_length=128)
    description = models.TextField(null=True, blank=True)

    def soft_delete(self):
        subgraph = self.subgraph_set.all()
        for item in subgraph:
            item.soft_delete()
        self.deleted_at = timezone.now()
        self.save()

    def __str__(self):
        return self.name


class Subgraph(TimeFields):
    name = models.CharField(max_length=128)
    description = models.TextField(null=True, blank=True)
    knowledge_graph = models.ForeignKey(KnowledgeGraph, on_delete=models.DO_NOTHING, null=True, blank=True)

    def soft_delete(self):
        nodes = self.node_set.all()
        for node in nodes:
            node.soft_delete()
        self.deleted_at = timezone.now()
        self.save()

    def __str__(self):
        return self.name


class Node(TimeFields):
    context = models.CharField(max_length=256)
    description = models.TextField(null=True, blank=True)
    subgraph = models.ForeignKey(Subgraph, on_delete=models.DO_NOTHING, null=True, blank=True)
    is_root = models.BooleanField(default=False)

    def soft_delete(self):
        outgoing_edges = self.outgoing_edges.all()
        for item in outgoing_edges:
            item.soft_delete()
        incoming_edges = self.incoming_edges.all()
        for item in incoming_edges:
            item.soft_delete()
        self.deleted_at = timezone.now()
        self.save()

    def __str__(self):
        return self.context


class Edge(TimeFields):
    from_node = models.ForeignKey(Node, related_name='outgoing_edges', on_delete=models.DO_NOTHING, null=True, blank=True)
    to_node = models.ForeignKey(Node, related_name='incoming_edges', on_delete=models.DO_NOTHING, null=True, blank=True)
    relation = models.CharField(max_length=128)
    description = models.TextField(null=True, blank=True)

    def soft_delete(self):
        self.deleted_at = timezone.now()
        self.save()

    def __str__(self):
        return f"{self.from_node} -> {self.to_node} ({self.relation})"


class Call(TimeFields):
    previous_call = models.ForeignKey('self', on_delete=models.DO_NOTHING, blank=True, null=True)
    customer_phone = models.CharField(max_length=15)
    description = models.TextField(null=True, blank=True)
    finished_at = models.DateTimeField(blank=True, null=True,)
    need_tracking = models.BooleanField(null=True, blank=True)


    def soft_delete(self):
        self.deleted_at = timezone.now()
        self.save()

    def __str__(self):
        return f"Call {self.id} - {self.customer_phone}"


class CallHistory(TimeFields):
    operator = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    call = models.ForeignKey(Call, on_delete=models.DO_NOTHING)
    question = models.ForeignKey(Node, on_delete=models.DO_NOTHING, null=True, blank=True)
    answer = models.ForeignKey(Edge, on_delete=models.DO_NOTHING, null=True, blank=True)
    description = models.TextField(null=True, blank=True)

    def soft_delete(self):
        self.deleted_at = timezone.now()
        self.save()

    def __str__(self):
        return f"History for Call {self.call.id} - Question {self.question.id}"

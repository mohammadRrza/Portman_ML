from rest_framework import serializers
from .models import KnowledgeGraph, Subgraph, Node, Edge, Call, CallHistory


class EdgeSerializer(serializers.ModelSerializer):
    from_node_info = serializers.SerializerMethodField()
    to_node_info = serializers.SerializerMethodField()

    def get_from_node_info(self, obj):
        if obj.from_node:
            return dict(id=obj.from_node.id,
                        context=obj.from_node.context,
                        description=obj.from_node.description,)

    def get_to_node_info(self, obj):
        if obj.to_node:
            return dict(id=obj.to_node.id,
                        context=obj.to_node.context,
                        description=obj.to_node.description,)
    class Meta:
        model = Edge
        fields = ['id', 'relation', 'description', 'from_node', 'to_node', 'from_node_info', 'to_node_info']


class NodeSerializer(serializers.ModelSerializer):
    outgoing_edges = EdgeSerializer(many=True, read_only=True)
    incoming_edges = EdgeSerializer(many=True, read_only=True)

    class Meta:
        model = Node
        fields = ['id', 'context', 'description', 'subgraph', 'incoming_edges', 'outgoing_edges', 'is_root']


class SubgraphSerializer(serializers.ModelSerializer):

    # nodes = NodeSerializer(many=True, read_only=True, source='node_set')
    node_count = serializers.SerializerMethodField()

    def get_node_count(self, obj):
        return obj.node_set.all().count()

    class Meta:
        model = Subgraph
        fields = ['id', 'name', 'description', 'knowledge_graph', 'node_count']


class KnowledgeGraphSerializer(serializers.ModelSerializer):
    # subgraphs = SubgraphSerializer(many=True, read_only=True, source='subgraph_set')
    subgraph_count = serializers.SerializerMethodField()

    def get_subgraph_count(self, obj):
        return obj.subgraph_set.all().count()

    class Meta:
        model = KnowledgeGraph
        fields = ['id', 'name', 'description', 'subgraph_count']


class CallSerializer(serializers.ModelSerializer):
    duration = serializers.SerializerMethodField()

    def get_duration(self, obj):
        if obj.finished_at:
            return obj.finished_at - obj.created_at
    class Meta:
        model = Call
        fields = ['id', 'previous_call', 'customer_phone', 'description', 'created_at', 'finished_at', 'duration', 'need_tracking']


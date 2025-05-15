from  datetime import datetime
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from .serializers import *
from .permissions import KnowledgeGraphPermissions
from .services.call_history_service import get_call_history


class KnowledgeGraphViewSet(ModelViewSet):
    permission_classes = (IsAuthenticated, KnowledgeGraphPermissions)
    serializer_class = KnowledgeGraphSerializer

    def get_queryset(self):
        page_size = self.request.query_params.get('page_size', 50)
        name = self.request.query_params.get('name', None)
        try:
            page_size = int(page_size)
        except ValueError:
            page_size = 50

        queryset = KnowledgeGraph.objects.all().order_by('-id')
        self.pagination_class.page_size = page_size if page_size else len(queryset)
        if name:
            queryset = queryset.filter(name__icontains=name)
        return queryset

    def create(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
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
        return Response(serializer.data, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        having_subgraph = instance.subgraph_set.all().exists()
        if having_subgraph:
            raise ValidationError(dict(results=_("The deletion was unsuccessful because the selected item has sub-items. Please first remove the sub-items.")))
        instance.soft_delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class SubgraphViewSet(ModelViewSet):
    permission_classes = (IsAuthenticated, KnowledgeGraphPermissions)
    serializer_class = SubgraphSerializer

    def get_queryset(self):
        page_size = self.request.query_params.get('page_size', 50)
        name = self.request.query_params.get('name', None)
        try:
            page_size = int(page_size)
        except ValueError:
            page_size = 50
        queryset = Subgraph.objects.filter(knowledge_graph__id=self.kwargs.get('knowledge_graph_id')).order_by('-id')
        self.pagination_class.page_size = page_size if page_size else len(queryset)
        if name:
            queryset = queryset.filter(name__icontains=name)
        return queryset

    def create(self, request, *args, **kwargs):
        request.data['knowledge_graph'] = self.kwargs.get('knowledge_graph_id')
        serializer = self.serializer_class(data=request.data)
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
        having_node = instance.node_set.all().exists()
        if having_node:
            raise ValidationError(dict(results=_(
                "The deletion was unsuccessful because the selected item has sub-items. Please first remove the sub-items.")))
        instance.soft_delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class NodeViewSet(ModelViewSet):
    permission_classes = (IsAuthenticated, KnowledgeGraphPermissions)
    serializer_class = NodeSerializer

    def get_queryset(self):
        page_size = self.request.query_params.get('page_size', 50)
        context = self.request.query_params.get('context', None)
        try:
            page_size = int(page_size)
        except ValueError:
            page_size = 50
        queryset = Node.objects.filter(subgraph__id=self.kwargs.get('subgraph_id')).order_by('-is_root')
        self.pagination_class.page_size = page_size if page_size else len(queryset)
        if context:
            queryset = queryset.filter(context__icontains=context)
        return queryset

    def create(self, request, *args, **kwargs):
        request.data['subgraph'] = self.kwargs.get('subgraph_id')
        serializer = self.serializer_class(data=request.data)
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
        return Response(serializer.data, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        outgoing_edges = instance.outgoing_edges.all().exists()
        incoming_edges = instance.incoming_edges.all().exists()

        if outgoing_edges or incoming_edges:
            raise ValidationError(dict(results=_(
                "The deletion was unsuccessful because the selected item has sub-items. Please first remove the sub-items.")))
        instance.soft_delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class EdgeViewSet(ModelViewSet):
    permission_classes = (IsAuthenticated, KnowledgeGraphPermissions)
    serializer_class = EdgeSerializer

    def get_queryset(self):
        page_size = self.request.query_params.get('page_size', 50)
        relation = self.request.query_params.get('relation', None)
        from_node_id = self.request.query_params.get('from_node_id', None)
        to_node_id = self.request.query_params.get('to_node_id', None)
        try:
            page_size = int(page_size)
        except ValueError:
            page_size = 50
        queryset = Edge.objects.filter(Q(from_node__subgraph__id=self.kwargs.get('subgraph_id')) |
                                       Q(to_node__subgraph_id=self.kwargs.get('subgraph_id'))).order_by('-id')
        self.pagination_class.page_size = page_size if page_size else len(queryset)
        if relation:
            queryset = queryset.filter(relation__icontains=relation)

        if from_node_id:
            queryset = queryset.filter(from_node_id=from_node_id)
        if to_node_id:
            queryset = queryset.filter(to_node_id=to_node_id)
        return queryset

    def create(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
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
        instance.soft_delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CallViewSet(ModelViewSet):
    permission_classes = (IsAuthenticated, )
    serializer_class = CallSerializer

    def get_queryset(self):
        page_size = self.request.query_params.get('page_size', 50)
        customer_phone = self.request.query_params.get('customer_phone', None)
        try:
            page_size = int(page_size)
        except ValueError:
            page_size = 50
        queryset = Call.objects.all().order_by('-id')
        self.pagination_class.page_size = page_size if page_size else len(queryset)
        if customer_phone:
            queryset = queryset.filter(customer_phone__icontains=customer_phone)
        return queryset

    def create(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        call_obj = serializer.save()

        previous_call = self.request.data.get('previous_call')
        if previous_call:
            previous_histories = CallHistory.objects.filter(call__id=previous_call).order_by('-id')
            histories_to_create = [
                CallHistory(
                    call=call_obj,
                    operator=self.request.user,
                    question=history.question,
                    answer=history.answer,
                    description=history.description
                )
                for history in previous_histories
            ]

            CallHistory.objects.bulk_create(histories_to_create)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.soft_delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def partial_update(self, request, *args, **kwargs):
        data = request.data.copy()
        data['finished_at'] = datetime.now()
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['POST'], url_path='answer-question')
    def answer_question(self, request, pk=None):
        operator = request.user
        call = get_object_or_404(Call, pk=pk)
        question_id = request.data.get('question_id')
        answer_id = request.data.get('answer_id')
        description = request.data.get('description')
        question = get_object_or_404(Node, pk=question_id)
        if not answer_id:
            CallHistory.objects.create(operator=operator, call=call, question=question, answer=None, description=description)
            return Response({'message': 'Call completed. No more questions.'}, status=status.HTTP_200_OK)
        answer = get_object_or_404(Edge, pk=answer_id)
        CallHistory.objects.create(operator=operator, call=call, question=question, answer=answer, description=description)
        next_question = answer.to_node
        if next_question:
            return Response({
                'message': 'Answer saved.',
                'next_question': NodeSerializer(next_question).data,
            }, status=status.HTTP_201_CREATED)
        return Response({'message': 'Call completed. No more questions.'}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['POST'], url_path='go-back')
    def go_back(self, request, pk=None):
        call = get_object_or_404(Call, pk=pk)
        question_id = request.data.get('question_id')
        target_question = get_object_or_404(Node, pk=question_id)
        target_question_history = CallHistory.objects.filter(call=call, question=target_question).order_by('created_at')
        for history in target_question_history:
            history.soft_delete()
            should_be_deleted_history = CallHistory.objects.filter(call=call, created_at__gt=history.created_at)
            for item in should_be_deleted_history:
                item.soft_delete()

        return Response({
            'message': 'Returned to selected question',
            'question': NodeSerializer(target_question).data
        })

    @action(detail=False, methods=['GET'], url_path='history')
    def history(self, request):
        customer_phone = self.request.query_params.get('customer_phone', None)
        page_size = request.query_params.get('page_size', 10)
        get_call_history(customer_phone)
        paginator = PageNumberPagination()
        paginator.page_size = page_size
        all_histories = get_call_history(customer_phone)
        paginated_histories = paginator.paginate_queryset(all_histories, request)
        response_data = {
            "count": len(all_histories),
            "next": paginator.get_next_link(),
            "previous": paginator.get_previous_link(),
            "results": paginated_histories
        }
        return Response(response_data, status=status.HTTP_200_OK)


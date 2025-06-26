from rest_framework.viewsets import ModelViewSet
from django.http import JsonResponse, HttpResponse
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .permissions import CanViewMapPoints
from .models import MapPoint, MapPointComment
from .serializers  import MapPointSerializer
from classes.base_permissions import ADMIN, SUPPORT, LTE_MAP_ADMIN, BASIC
from rest_framework import pagination, status
from rest_framework.decorators import action
from datetime import datetime


class MapPointViewSet(ModelViewSet):

    queryset = MapPoint.objects.all()
    permission_classes = (IsAuthenticated, CanViewMapPoints)
    serializer_class = MapPointSerializer

    def get_queryset(self):
        queryset = self.queryset
        page_size = self.request.query_params.get('page_size', 2000)
        if int(page_size) < 1 or int(page_size) > 3000:
            page_size = 10

        queryset = queryset.exclude(deleted_at__isnull=False).order_by('-id')
        pagination.PageNumberPagination.page_size = page_size
        return queryset  

    def create(self, request, *args, **kwargs):
        request.data['user'] = request.user.id
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        MapPointComment.objects.create(point=serializer.instance, comment=request.data.get('comment'), user=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=self.get_success_headers(serializer.data))

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', True)
        instance = self.get_object()
        serializer = self.serializer_class(instance, data=request.data, request=self.request, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.deleted_at = datetime.now()
        instance.save()
        return Response({'results': "Point deleted", 'status': status.HTTP_204_NO_CONTENT})
        #return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["post"])
    def comment(self, request, pk=None):
        mapPoint = self.get_object()
        newComment = MapPointComment.objects.create(comment=request.data.get('comment'), point=mapPoint, user=self.request.user)
        if newComment:
            instance = MapPoint.objects.get(pk=mapPoint.id)
            serializer = self.serializer_class(instance)
            return Response(serializer.data)
        
        return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=["delete"])
    def delete_comment(self, request, pk=None):
        mapPoint = self.get_object()
        comment = MapPointComment.objects.get(pk=request.GET.get('comment_id'))
        if comment:
            comment.deleted_at = datetime.now()
            comment.save()
            instance = MapPoint.objects.get(pk=mapPoint.id)
            serializer = self.serializer_class(instance)
            return Response(serializer.data)
        
        return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)


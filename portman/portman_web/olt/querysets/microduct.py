from ..models import Microduct
from dslam.models import City
from django.db.models import Q
from ..permissions import ADMIN,  FTTH_ADMIN, FTTH_OPERATOR, FTTH_SUPPORT, SUPPORT


class MicroductQueryset:
    def __init__(self, request):
        self.request = request

    def get_queryset(self):
        queryset = Microduct.objects.all().exclude(deleted_at__isnull=False).order_by('-id')
        id = self.request.query_params.get('id', None)
        code = self.request.query_params.get('code', None)
        type_title = self.request.query_params.get('type_title', None)
        type_id = self.request.query_params.get('type_id', None)
        province_id = self.request.query_params.get('province_id', None)
        city_id = self.request.query_params.get('city_id', None)
        city_name = self.request.query_params.get('city_name', None)
        province_name = self.request.query_params.get('province_name', None)
        sort_by_column_name = self.request.query_params.get('sort_by', None)
        sort_order = self.request.query_params.get('sort_order', None)
        province_access = self.request.user.ftth_province_access

        
        if province_id:
            province = City.objects.get(id=province_id)
            cities = City.objects.filter(parent=province)
            queryset = queryset.filter(city__in=cities)

        if city_id:
            queryset = queryset.filter(city__id=city_id)

        if province_name:
            provinces = City.objects.filter(name__icontains=province_name)
            cities = City.objects.filter(parent__in=provinces)
            queryset = queryset.filter(city__in=cities)

        if city_name:
            queryset = queryset.filter(city__name__icontains=city_name)

        if id:
            queryset = queryset.filter(pk=id)

        if code:
            queryset = queryset.filter(code__icontains=code)

        if type_title:
            queryset = queryset.filter(type__title__icontains=type_title)

        if type_id:
            queryset = queryset.filter(type__id=type_id)

        if not self.request.user.type_contains([ADMIN,  FTTH_ADMIN, FTTH_OPERATOR, FTTH_SUPPORT, SUPPORT]):
            queryset = queryset.filter(Q(city__parent__id__in=province_access.get('read')) |
                                       Q(city__parent__id__in=province_access.get('read_write')))
        if sort_by_column_name:
            if sort_by_column_name == 'id':
                if sort_order == 'Asc':
                    queryset = queryset.order_by('id')
                else:
                    queryset = queryset.order_by('-id')

            elif sort_by_column_name == 'length':
                if sort_order == 'Asc':
                    queryset = queryset.order_by('length')
                else:
                    queryset = queryset.order_by('-length')

            elif sort_by_column_name == 'size':
                if sort_order == 'Asc':
                    queryset = queryset.order_by('size')
                else:
                    queryset = queryset.order_by('-size')

            elif sort_by_column_name == 'channel_count':
                if sort_order == 'Asc':
                    queryset = queryset.order_by('channel_count')
                else:
                    queryset = queryset.order_by('-channel_count')

        return queryset


class ContractorQueryset(MicroductQueryset):
    def get_queryset(self):
        queryset = super().get_queryset()
        #queryset.filter
        return queryset


class MicroductQuerysetFactory:
    def __init__(self, request):
        self.request = request

    def make(self):
        return ContractorQueryset(self.request).get_queryset()

from ..models import Splitter
from dslam.models import City
from django.db.models import Q
from ..permissions import ADMIN,  FTTH_ADMIN, FTTH_OPERATOR, FTTH_SUPPORT, SUPPORT


class SplitterQueryset:
    def __init__(self, request):
        self.request = request

    def get_queryset(self):
        queryset = Splitter.objects.all().exclude(deleted_at__isnull=False).order_by('-id')
        splitter_type = self.request.query_params.get('type_id', None)
        name = self.request.query_params.get('name', None)
        exclude_id = self.request.query_params.get('exclude_id', None)
        FAT_id = self.request.query_params.get('FAT_id', None)
        province_id = self.request.query_params.get('province_id', None)
        city_id = self.request.query_params.get('city_id', None)
        city_name = self.request.query_params.get('city_name', None)
        province_name = self.request.query_params.get('province_name', None)
        is_active = self.request.query_params.get('is_active', None)
        sort_by_column_name = self.request.query_params.get('sort_by', None)
        sort_order = self.request.query_params.get('sort_order', None)
        province_access = self.request.user.ftth_province_access


        if exclude_id != None and exclude_id != 'null':
            queryset = queryset.exclude(id=exclude_id)

        if splitter_type:
            queryset = queryset.filter(splitter_type__id=splitter_type)

        if name:
            queryset = queryset.filter(name__icontains=name)

        if FAT_id:
            queryset = queryset.filter(FAT__id=FAT_id)

        if province_id:
            province_obj = City.objects.get(id=province_id)
            cities = province_obj.city_set.all()
            queryset = queryset.filter(FAT__olt__cabinet__city__in=cities)
        if city_id:
            queryset = queryset.filter(FAT__olt__cabinet__city__id=city_id)

        if province_name:
            provinces = City.objects.filter(name__icontains=province_name)
            cities = City.objects.filter(parent__in=provinces)
            queryset = queryset.filter(FAT__olt__cabinet__city__in=cities)

        if city_name:
            queryset = queryset.filter(FAT__olt__cabinet__city__name__icontains=city_name)

        if is_active:
            queryset = queryset.filter(is_active=True)

        if not self.request.user.type_contains([ADMIN,  FTTH_ADMIN, FTTH_OPERATOR, FTTH_SUPPORT, SUPPORT]):
            queryset = queryset.filter(Q(fat__olt__cabinet__city__parent__id__in=province_access.get('read')) |
                                       Q(fat__olt__cabinet__city__parent__id__in=province_access.get('read_write')))

        if sort_by_column_name:
            if sort_by_column_name == 'id':
                if sort_order == 'Asc':
                    queryset = queryset.order_by('id')
                else:
                    queryset = queryset.order_by('-id')

            elif sort_by_column_name == 'name':
                if sort_order == 'Asc':
                    queryset = queryset.order_by('name')
                else:
                    queryset = queryset.order_by('-name')

            elif sort_by_column_name == 'leg_count':
                if sort_order == 'Asc':
                    queryset = queryset.order_by('splitter_type__legs_count')
                else:
                    queryset = queryset.order_by('-splitter_type__legs_count')

        return queryset


class ContractorQueryset(SplitterQueryset):
    def get_queryset(self):
        queryset = super().get_queryset()
        #queryset.filter
        return queryset


class SplitterQuerysetFactory:
    def __init__(self, request):
        self.request = request

    def make(self):
        return ContractorQueryset(self.request).get_queryset()

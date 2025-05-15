from ..models import Handhole
from dslam.models import City
from django.db.models import Q
from ..permissions import ADMIN,  FTTH_ADMIN, FTTH_OPERATOR, FTTH_SUPPORT, SUPPORT


class HandholeQueryset:
    def __init__(self, request):
        self.request = request

    def get_queryset(self):
        queryset = Handhole.objects.extra(
            select={'casted_number': 'CAST(number AS INTEGER)'}
        ).exclude(deleted_at__isnull=False).order_by('-casted_number')
        filter_mode = self.request.query_params.get('filter_mode', None)
        number = self.request.query_params.get('number', None)
        city_id = self.request.query_params.get('city_id', None)
        province_id = self.request.query_params.get('province_id', None)
        city_name = self.request.query_params.get('city_name', None)
        province_name = self.request.query_params.get('province_name', None)
        urban_district = self.request.query_params.get('urban_district', None)
        handhole_type_id = self.request.query_params.get('handhole_type_id', None)
        sort_by_column_name = self.request.query_params.get('sort_by', None)
        sort_order = self.request.query_params.get('sort_order', None)
        province_access = self.request.user.ftth_province_access

        if handhole_type_id:
            queryset = queryset.filter(type__id=handhole_type_id)

        if number:
            queryset = queryset.filter(number=number)

        if city_id:
            queryset = queryset.filter(city__id=city_id)

        if city_name:
            queryset = queryset.filter(city__name__icontains=city_name)

        if province_id:
            province_obj = City.objects.get(id=province_id)
            cities = province_obj.city_set.all()
            queryset = queryset.filter(city__in=cities)

        if province_name:
            provinces = City.objects.filter(name__icontains=province_name)
            cities = City.objects.filter(parent__in=provinces)
            queryset = queryset.filter(city__in=cities)

        if urban_district:
            queryset = queryset.filter(urban_district=urban_district)

        if not self.request.user.type_contains([ADMIN,  FTTH_ADMIN, FTTH_OPERATOR, FTTH_SUPPORT, SUPPORT]):
            queryset = queryset.filter(Q(city__parent__id__in=province_access.get('read')) |
                                       Q(city__parent__id__in=province_access.get('read_write')))

        if sort_by_column_name:
            if sort_by_column_name == 'id':
                if sort_order == 'Asc':
                    queryset = queryset.order_by('id')
                else:
                    queryset = queryset.order_by('-id')

            elif sort_by_column_name == 'number':
                if sort_order == 'Asc':
                    queryset = queryset.order_by('number')
                else:
                    queryset = queryset.order_by('-number')

            elif sort_by_column_name == 'model':
                if sort_order == 'Asc':
                    queryset = queryset.order_by('type__model')
                else:
                    queryset = queryset.order_by('-type__model')

            elif sort_by_column_name == 'material':
                if sort_order == 'Asc':
                    queryset = queryset.order_by('type__material')
                else:
                    queryset = queryset.order_by('-type__material')

            elif sort_by_column_name == 'type':
                if sort_order == 'Asc':
                    queryset = queryset.order_by('type__type')
                else:
                    queryset = queryset.order_by('-type__type')

        return queryset


class ContractorQueryset(HandholeQueryset):
    def __init__(self, request):
        self.request = request

    def get_queryset(self):
        queryset = super().get_queryset()
        #queryset.filter 
        return queryset


class HandholeQuerysetFactory:
    def __init__(self, request):
        self.request = request

    def make(self):
        return ContractorQueryset(self.request).get_queryset()

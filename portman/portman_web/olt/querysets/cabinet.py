from django.db.models import Q
from ..models import OLTCabinet
from dslam.models import City
from ..permissions import ADMIN,  FTTH_ADMIN, FTTH_OPERATOR, FTTH_SUPPORT, SUPPORT

class CabinetQueryset:
    def __init__(self, request):
        self.request = request

    def get_queryset(self):
        queryset = OLTCabinet.objects.all().exclude(deleted_at__isnull=False).order_by('-id')
        filter_mode = self.request.query_params.get('filter_mode', None)
        cabinet_name = self.request.query_params.get('name', None)
        search_text = self.request.query_params.get('search_text', None)
        without_odc = self.request.query_params.get('without_odc', None)
        province_name = self.request.query_params.get('province_name', None)
        city_name = self.request.query_params.get('city_name', None)
        cabinet_type = self.request.query_params.get('type_id', None)
        province_id = self.request.query_params.get('province_id', None)
        city_id = self.request.query_params.get('city_id', None)
        urban_district = self.request.query_params.get('urban_district', None)
        sort_by_column_name = self.request.query_params.get('sort_by', None)
        sort_order = self.request.query_params.get('sort_order', None)
        province_access = self.request.user.ftth_province_access

        if cabinet_name:
            if filter_mode == 'exact':
                queryset = queryset.filter(name__iexact=cabinet_name)
            else:
                queryset = queryset.filter(name__icontains=cabinet_name)

        if province_name:
            queryset = queryset.filter(city__parent__name__icontains=province_name)

        if city_name:
            queryset = queryset.filter(city__name__icontains=city_name)

        if province_id:
            queryset = queryset.filter(city__parent__id=province_id)

        if city_id:
            queryset = queryset.filter(city__id=city_id)

        if cabinet_type:
            queryset = queryset.filter(type__id=cabinet_type)

        if urban_district:
            queryset = queryset.filter(urban_district=urban_district)

        if search_text:
            queryset = queryset.filter(name__icontains=search_text)

        if without_odc != None:
            queryset = queryset.filter(is_odc=False)

        if not self.request.user.type_contains([ADMIN,  FTTH_ADMIN, FTTH_OPERATOR, FTTH_SUPPORT, SUPPORT]):
            queryset = queryset.filter(Q(city__parent__id__in=province_access.get('read')) |
                                       Q(city__parent__id__in=province_access.get('read_write')))

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

        return queryset


class ContractorQueryset(CabinetQueryset):
    def get_queryset(self):
        queryset = super().get_queryset()
        #queryset.filter
        return queryset


class CabinetQuerysetFactory:
    def __init__(self, request):
        self.request = request

    def make(self):
        return ContractorQueryset(self.request).get_queryset()

from django.db.models import Q
from ..models import OLTCabinet
from dslam.models import City
from ..permissions import ADMIN,  FTTH_ADMIN, FTTH_OPERATOR, FTTH_SUPPORT, SUPPORT


class OdcQueryset:
    def __init__(self, request):
        self.request = request

    def get_queryset(self):
        queryset = OLTCabinet.objects.filter(is_odc=True).exclude(deleted_at__isnull=False).order_by('-id')
        filter_mode = self.request.query_params.get('filter_mode', None)
        odc_name = self.request.query_params.get('name', None)
        odc_code = self.request.query_params.get('code', None)
        search_text = self.request.query_params.get('search_text', None)
        province_name = self.request.query_params.get('province_name', None)
        city_name = self.request.query_params.get('city_name', None)
        province_id = self.request.query_params.get('province_id', None)
        city_id = self.request.query_params.get('city_id', None)
        sort_by_column_name = self.request.query_params.get('sort_by', None)
        sort_order = self.request.query_params.get('sort_order', None)
        province_access = self.request.user.ftth_province_access


        if odc_name:
            if filter_mode == 'exact':
                queryset = queryset.filter(name__iexact=odc_name)
            else:
                queryset = queryset.filter(name__icontains=odc_name)

        if odc_code:
            queryset = queryset.filter(code__icontains=odc_code)

        if province_name:
            provinces = City.objects.filter(name__icontains=province_name)
            cities = City.objects.filter(parent__in=provinces)
            queryset = queryset.filter(city__in=cities)

        if city_name:
            queryset = queryset.filter(city__name__icontains=city_name)

        if province_id:
            province = City.objects.get(id=province_id)
            cities = City.objects.filter(parent=province)
            queryset = queryset.filter(city__in=cities)

        if city_id:
            queryset = queryset.filter(city__id=city_id)

        if search_text:
            queryset = queryset.filter(Q(name__icontains=search_text) | Q(code__icontains=search_text))

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


class ContractorQueryset(OdcQueryset):
    def get_queryset(self):
        queryset = super().get_queryset()
        #queryset.filter
        return queryset


class OdcQuerysetFactory:
    def __init__(self, request):
        self.request = request

    def make(self):
        return ContractorQueryset(self.request).get_queryset()

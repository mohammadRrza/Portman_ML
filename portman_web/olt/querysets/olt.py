from ..models import OLT
from dslam.models import City
from django.db.models import Q
from ..permissions import ADMIN,  FTTH_ADMIN, FTTH_OPERATOR, FTTH_SUPPORT, SUPPORT


class OltQueryset:
    def __init__(self, request):
        self.request = request

    def get_queryset(self):
        queryset = OLT.objects.all().exclude(deleted_at__isnull=False).order_by('-id')
        search_text = self.request.query_params.get('search_text', None)
        olt_name = self.request.query_params.get('search_olt', None)
        ip = self.request.query_params.get('search_ip', None)
        olt_type_id = self.request.query_params.get('search_type', None)
        cabinet_code = self.request.query_params.get('cabinet_code', None)
        cabinet_id = self.request.query_params.get('cabinet_id', None)
        province_id = self.request.query_params.get('province_id', None)
        city_id = self.request.query_params.get('city_id', None)
        city_name = self.request.query_params.get('city_name', None)
        province_name = self.request.query_params.get('province_name', None)
        sort_by_column_name = self.request.query_params.get('sort_by', None)
        sort_order = self.request.query_params.get('sort_order', None)
        province_access = self.request.user.ftth_province_access


        if olt_type_id:
            queryset = queryset.filter(olt_type__id=olt_type_id)

        if olt_name:
            queryset = queryset.filter(name__icontains=olt_name)

        if search_text:
            queryset = queryset.filter(name__icontains=search_text)

        if cabinet_code:
            queryset = queryset.filter(cabinet__code__icontains=cabinet_code)
        if cabinet_id:
            queryset = queryset.filter(cabinet__id=cabinet_id)
        if ip:
            ip = ip.strip()
            if len(ip.split('.')) != 4:
                queryset = queryset.filter(ip__icontains=ip)
            else:
                queryset = queryset.filter(ip=ip)

        if province_id:
            province = City.objects.get(id=province_id)
            cities = City.objects.filter(parent=province)
            queryset = queryset.filter(cabinet__city__in=cities)

        if city_id:
            queryset = queryset.filter(cabinet__city__id=city_id)

        if province_name:
            provinces = City.objects.filter(name__icontains=province_name)
            cities = City.objects.filter(parent__in=provinces)
            queryset = queryset.filter(cabinet__city__in=cities)

        if city_name:
            queryset = queryset.filter(cabinet__city__name__icontains=city_name)

        if not self.request.user.type_contains([ADMIN,  FTTH_ADMIN, FTTH_OPERATOR, FTTH_SUPPORT, SUPPORT]):
            queryset = queryset.filter(Q(cabinet__city__parent__id__in=province_access.get('read')) |
                                       Q(cabinet__city__parent__id__in=province_access.get('read_write')))

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

            elif sort_by_column_name == 'ip':
                if sort_order == 'Asc':
                    queryset = queryset.order_by('ip')
                else:
                    queryset = queryset.order_by('-ip')

            elif sort_by_column_name == 'type':
                if sort_order == 'Asc':
                    queryset = queryset.order_by('olt_type__name')
                else:
                    queryset = queryset.order_by('-olt_type__name')

        return queryset


class ContractorQueryset(OltQueryset):
    def get_queryset(self):
        queryset = super().get_queryset()
        #queryset.filter
        return queryset


class OltQuerysetFactory:
    def __init__(self, request):
        self.request = request

    def make(self):
        return ContractorQueryset(self.request).get_queryset()
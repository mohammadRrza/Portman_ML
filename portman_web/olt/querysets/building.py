from ..models import Building
from dslam.models import City
from django.db.models import Q
from ..permissions import ADMIN,  FTTH_ADMIN, FTTH_SUPPORT, SUPPORT, FTTH_OPERATOR


class BuildingQueryset:
    def __init__(self, request):
        self.request = request

    def get_queryset(self):
        queryset = Building.objects.all().exclude(deleted_at__isnull=False).order_by('-id')
        name = self.request.query_params.get('name', None)
        phone = self.request.query_params.get('phone', None)
        postal_code = self.request.query_params.get('postal_code', None)
        urban_district = self.request.query_params.get('urban_district', None)
        province_id = self.request.query_params.get('province_id', None)
        city_id = self.request.query_params.get('city_id', None)
        province_name = self.request.query_params.get('province_name', None)
        city_name = self.request.query_params.get('city_name', None)
        postal_address = self.request.query_params.get('postal_address', None)

        province_access = self.request.user.ftth_province_access

        if name:
            queryset = queryset.filter(name__icontains=name)

        if phone:
            queryset = queryset.filter(phone__icontains=phone)

        if postal_code:
            queryset = queryset.filter(postal_code__icontains=postal_code)

        if urban_district:
            queryset = queryset.filter(urban_district=urban_district)

        if province_id:
            queryset = queryset.filter(city__parent__id=province_id)
        if city_id:
            queryset = queryset.filter(city__id=city_id)

        if province_name:
            queryset = queryset.filter(city__parent__name__icontains=province_name)

        if city_name:
            queryset = queryset.filter(city__name__icontains=city_name)

        if postal_address:
            queryset = queryset.filter(postal_address=postal_address)

        if not self.request.user.type_contains([ADMIN,  FTTH_ADMIN, FTTH_OPERATOR, FTTH_SUPPORT, SUPPORT]):
            queryset = queryset.filter(Q(city__parent__id__in=province_access.get('read')) |
                                       Q(city__parent__id__in=province_access.get('read_write')))

        return queryset


class ContractorQueryset(BuildingQueryset):
    def get_queryset(self):
        queryset = super().get_queryset()
        #queryset.filter
        return queryset


class BuildingQuerysetFactory:
    def __init__(self, request):
        self.request = request

    def make(self):
        return ContractorQueryset(self.request).get_queryset()

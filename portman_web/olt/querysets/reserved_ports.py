from ..models import ReservedPorts, OLT, Splitter
from dslam.models import City
from django.db.models import Q


class ReservedPortsQueryset:
    def __init__(self, request):
        self.request = request

    def get_queryset(self):
        queryset = ReservedPorts.objects.all().order_by('-id')
        crm_id = self.request.query_params.get('crm_id', None)
        splitter_id = self.request.query_params.get('splitter_id', None)
        fat_id = self.request.query_params.get('fat_id', None)
        olt_id = self.request.query_params.get('olt_id', None)
        leg_number = self.request.query_params.get('leg_number', None)
        customer = self.request.query_params.get('customer', None)
        crm_username = self.request.query_params.get('crm_username', None)
        operator_id = self.request.query_params.get('operator_id', None)
        status = self.request.query_params.get('status', None)
        province_id = self.request.query_params.get('province_id', None)
        city_id = self.request.query_params.get('city_id', None)
        province_name = self.request.query_params.get('province_name', None)
        city_name = self.request.query_params.get('city_name', None)

        if crm_id:
            queryset = queryset.filter(crm_id__icontains=crm_id)

        if olt_id:
            queryset = queryset.filter(fat__olt__id=olt_id)

        if fat_id:
            queryset = queryset.filter(fat__id=fat_id)

        if splitter_id:
            queryset = queryset.filter(splitter__id=splitter_id)

        if leg_number:
            queryset = queryset.filter(leg_number=leg_number)

        if crm_username:
            queryset = queryset.filter(crm_username=crm_username)

        if customer:
            queryset = queryset.filter(Q(customer_name__icontains=customer) | Q(customer_name_en__icontains=customer))

        if operator_id:
            queryset = queryset.filter(operator__id=operator_id)

        if status:
            queryset = queryset.filter(status__icontains=status)

        if province_id:
            queryset = queryset.filter(fat__olt__cabinet__city__parent__id=province_id)
        if city_id:
            queryset = queryset.filter(fat__olt__cabinet__city__id=city_id)

        if province_name:
            queryset = queryset.filter(fat__olt__cabinet__city__parent__name__icontains=province_name)

        if city_name:
            queryset = queryset.filter(fat__olt__cabinet__city__name__icontains=city_name)

        return queryset


class ContractorQueryset(ReservedPortsQueryset):
    def get_queryset(self):
        queryset = super().get_queryset()
        #queryset.filter
        return queryset


class ReservedPortsQuerysetFactory:
    def __init__(self, request):
        self.request = request

    def make(self):
        return ContractorQueryset(self.request).get_queryset()

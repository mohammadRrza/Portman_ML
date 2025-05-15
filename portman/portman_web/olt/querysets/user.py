from ..models import User, FAT
from dslam.models import City
from django.db.models import Q


class UserQueryset:
    def __init__(self, request):
        self.request = request

    def get_queryset(self):
        queryset = User.objects.all()
        ont_id = self.request.query_params.get('ont_id', None)
        crm_id = self.request.query_params.get('crm_id', None)
        serial_number = self.request.query_params.get('serial_number', None)
        sort_by_column_name = self.request.query_params.get('sort_by', None)
        sort_order = self.request.query_params.get('sort_order', None)
        province_id = self.request.query_params.get('province_id', None)
        city_id = self.request.query_params.get('city_id', None)

        if ont_id:
            queryset = queryset.filter(ont__id=ont_id)
        if serial_number:
            queryset = queryset.filter(ont__serial_number__contains=serial_number)
        if crm_id:
            queryset = queryset.filter(crm_id__contains=crm_id)

        if sort_by_column_name:
            if sort_by_column_name == 'id':
                if sort_order == 'Asc':
                    queryset = queryset.order_by('id')
                else:
                    queryset = queryset.order_by('-id')

            elif sort_by_column_name == 'crm_id':
                if sort_order == 'Asc':
                    queryset = queryset.order_by('crm_id')
                else:
                    queryset = queryset.order_by('-crm_id')

            elif sort_by_column_name == 'lable':
                if sort_order == 'Asc':
                    queryset = queryset.order_by('cable_type__label')
                else:
                    queryset = queryset.order_by('-cable_type__label')

            elif sort_by_column_name == 'atb':
                if sort_order == 'Asc':
                    queryset = queryset.order_by('atb_type__name')
                else:
                    queryset = queryset.order_by('-atb_type__name')

        if province_id:
            province = City.objects.get(id=province_id)
            cities = City.objects.filter(parent=province)
            fat_ids = FAT.objects.filter(olt__cabinet__city__in=cities).values_list('id', flat=True)
            queryset = queryset.filter(Q(reservedports__splitter__FAT__id__in=fat_ids) |
                                       Q(reservedports__patch_panel_port__terminal__content_type__model='fat',
                                         reservedports__patch_panel_port__terminal__object_id__in=fat_ids))

        if city_id:
            fat_ids = FAT.objects.filter(olt__cabinet__city__id=city_id).values_list('id', flat=True)
            queryset = queryset.filter(Q(reservedports__splitter__FAT__id__in=fat_ids) |
                                       Q(reservedports__patch_panel_port__terminal__content_type__model='fat',
                                         reservedports__patch_panel_port__terminal__object_id__in=fat_ids))

        queryset = queryset.exclude(deleted_at__isnull=False).order_by('-id')
        return queryset


class ContractorQueryset(UserQueryset):
    def get_queryset(self):
        queryset = super().get_queryset()
        #queryset.filter
        return queryset


class UserQuerysetFactory:
    def __init__(self, request):
        self.request = request

    def make(self):
        return ContractorQueryset(self.request).get_queryset()

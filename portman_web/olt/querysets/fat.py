from ..models import FAT
from dslam.models import City
from django.db.models import Q
from ..permissions import ADMIN,  FTTH_ADMIN, FTTH_OPERATOR, FTTH_SUPPORT, SUPPORT, FTTH_WEB_SERVICE


class FatQueryset:
    def __init__(self, request):
        self.request = request

    def get_queryset(self):
        queryset = FAT.objects.all().exclude(deleted_at__isnull=False).order_by('-id')
        filter_mode = self.request.query_params.get('filter_mode', None)
        fat_name = self.request.query_params.get('name', None)
        olt_id = self.request.query_params.get('olt_id', None)
        type_id = self.request.query_params.get('type_id', None)
        parent_code = self.request.query_params.get('parent_code', None)
        patch_panel_port = self.request.query_params.get('patch_panel_port', None)
        olt_name = self.request.query_params.get('olt_name', None)
        sort_by_column_name = self.request.query_params.get('sort_by', None)
        sort_order = self.request.query_params.get('sort_order', None)
        f_fat = self.request.query_params.get('f_fat', None)
        province_id = self.request.query_params.get('province_id', None)
        city_id = self.request.query_params.get('city_id', None)
        is_otb = self.request.query_params.get('is_otb', None)
        is_tb = self.request.query_params.get('is_tb', None)
        city_name = self.request.query_params.get('city_name', None)
        province_name = self.request.query_params.get('province_name', None)
        urban_district = self.request.query_params.get('urban_district', None)
        province_access = self.request.user.ftth_province_access

        if province_name:
            provinces = City.objects.filter(name__icontains=province_name)
            cities = City.objects.filter(parent__in=provinces)
            queryset = queryset.filter(olt__cabinet__city__in=cities)

        if city_name:
            queryset = queryset.filter(olt__cabinet__city__name__icontains=city_name)

        if urban_district:
            queryset = queryset.filter(urban_district=urban_district)

        if is_otb:
            queryset = queryset.filter(is_otb=True)

        if is_tb:
            queryset = queryset.filter(is_tb=True)

        if fat_name:
            if filter_mode == 'exact':
                queryset = queryset.filter(name__iexact=fat_name)
            else:
                queryset = queryset.filter(name__icontains=fat_name)

        if olt_id:
            queryset = queryset.filter(olt__id=olt_id)

        if type_id:
            queryset = queryset.filter(fat_type__id=type_id)

        if parent_code:
            queryset = queryset.filter(parent__code__icontains=parent_code)

        if patch_panel_port:
            queryset = queryset.filter(patch_panel_port=patch_panel_port)

        if olt_name:
            queryset = queryset.filter(olt__name__icontains=olt_name)

        if province_id:
            province_obj = City.objects.get(id=province_id)
            cities = province_obj.city_set.all()
            queryset = queryset.filter(olt__cabinet__city__in=cities)
        if city_id:
            queryset = queryset.filter(olt__cabinet__city__id=city_id)

        if f_fat == 'True':
            queryset = queryset.filter(parent__isnull=False, is_otb=False)

        elif f_fat == 'False':
            queryset = queryset.filter(parent__isnull=True)

        if not self.request.user.type_contains([ADMIN,  FTTH_ADMIN, FTTH_OPERATOR, FTTH_SUPPORT, FTTH_WEB_SERVICE, SUPPORT]):
            queryset = queryset.filter(Q(olt__cabinet__city__parent__id__in=province_access.get('read')) |
                                       Q(olt__cabinet__city__parent__id__in=province_access.get('read_write')))

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

            elif sort_by_column_name == 'code':
                if sort_order == 'Asc':
                    queryset = queryset.order_by('code')
                else:
                    queryset = queryset.order_by('-code')

            elif sort_by_column_name == 'is_active':
                if sort_order == 'Asc':
                    queryset = queryset.order_by('is_active')
                else:
                    queryset = queryset.order_by('-is_active')

            elif sort_by_column_name == 'type':
                if sort_order == 'Asc':
                    queryset = queryset.order_by('fat_type__name')
                else:
                    queryset = queryset.order_by('-fat_type__name')

            elif sort_by_column_name == 'patch_panel_port':
                if sort_order == 'Asc':
                    queryset = queryset.order_by('patch_panel_port')
                else:
                    queryset = queryset.order_by('-patch_panel_port')

            elif sort_by_column_name == 'olt':
                if sort_order == 'Asc':
                    queryset = queryset.order_by('olt__name')
                else:
                    queryset = queryset.order_by('-olt__name')

            elif sort_by_column_name == 'size':
                if sort_order == 'Asc':
                    queryset = queryset.order_by('size')
                else:
                    queryset = queryset.order_by('-size')

            elif sort_by_column_name == 'capacity':
                if sort_order == 'Asc':
                    queryset = queryset.order_by('max_capacity')
                else:
                    queryset = queryset.order_by('-max_capacity')
        return queryset


class ContractorQueryset(FatQueryset):
    def get_queryset(self):
        queryset = super().get_queryset()
        #queryset.filter
        return queryset


class FatQuerysetFactory:
    def __init__(self, request):
        self.request = request

    def make(self):
        return ContractorQueryset(self.request).get_queryset()

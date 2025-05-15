from ..models import Cable, OLTCabinet
from dslam.models import City
from rest_framework.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from django.db.models import Q
from ..permissions import ADMIN,  FTTH_ADMIN, FTTH_OPERATOR, FTTH_SUPPORT, SUPPORT



class CableQueryset:
    def __init__(self, request):
        self.request = request

    def get_queryset(self):
        queryset = Cable.objects.all().exclude(deleted_at__isnull=False).order_by('-id')
        id = self.request.query_params.get('id', None)
        uplink = self.request.query_params.get('uplink', None)
        src_type = self.request.query_params.get('src_type', None)
        src_id = self.request.query_params.get('src_id', None)
        code = self.request.query_params.get('code', None)
        usage = self.request.query_params.get('usage', None)
        type_id = self.request.query_params.get('type_id', None)
        province_id = self.request.query_params.get('province_id', None)
        city_id = self.request.query_params.get('city_id', None)
        city_name = self.request.query_params.get('city_name', None)
        province_name = self.request.query_params.get('province_name', None)
        is_filter = self.request.query_params.get('filter', None)
        sort_by_column_name = self.request.query_params.get('sort_by', None)
        sort_order = self.request.query_params.get('sort_order', None)
        province_access = self.request.user.ftth_province_access

        if uplink:
            if not src_type:
                raise ValidationError(dict(results="src_type can't be null."))
            if not src_id:
                raise ValidationError(dict(results="src_id can't be null."))
            if src_type == 'cabinet':
                cabinet_obj = get_object_or_404(OLTCabinet, pk=src_id)
                if cabinet_obj.parent:
                    queryset = queryset.filter(src_device_type='cabinet', src_device_id=cabinet_obj.parent.id)
            else:
                input_cables = queryset.filter(dst_device_type=src_type, dst_device_id=src_id)
                cables_id = []
                for cable in input_cables:
                    if cable.src_device_type == 'cabinet':
                        cables_id.append(cable.id)
                    elif cable.uplink:
                        cables_id.append(cable.uplink.id)
                queryset = queryset.filter(id__in=cables_id)

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

        if usage:
            queryset = queryset.filter(usage=usage)

        if id:
            queryset = queryset.filter(pk=id)

        if code:
            queryset = queryset.filter(code__icontains=code)

        if type_id:
            queryset = queryset.filter(type__id=type_id)

        if is_filter and is_filter.lower() == 'true':
            queryset = self.filter(queryset)

        if not self.request.user.type_contains([ADMIN,  FTTH_ADMIN, FTTH_OPERATOR, FTTH_SUPPORT, SUPPORT]):
            queryset = queryset.filter(Q(city__parent__id__in=province_access.get('read')) |
                                       Q(city__parent__id__in=province_access.get('read_write')))

        if sort_by_column_name:
            if sort_by_column_name == 'id':
                if sort_order == 'Asc':
                    queryset = queryset.order_by('id')
                else:
                    queryset = queryset.order_by('-id')

            elif sort_by_column_name == 'code':
                if sort_order == 'Asc':
                    queryset = queryset.order_by('code')
                else:
                    queryset = queryset.order_by('-code')

            elif sort_by_column_name == 'usage':
                if sort_order == 'Asc':
                    queryset = queryset.order_by('usage')
                else:
                    queryset = queryset.order_by('-usage')

            elif sort_by_column_name == 'length':
                if sort_order == 'Asc':
                    queryset = queryset.order_by('length')
                else:
                    queryset = queryset.order_by('-length')

        return queryset

    def filter(self, queryset):
        usage_set = ['microfiber']
        queryset = queryset.exclude(usage__in=usage_set)
        return queryset


class ContractorQueryset(CableQueryset):
    def get_queryset(self):
        queryset = super().get_queryset()
        #queryset.filter
        return queryset


class CableQuerysetFactory:
    def __init__(self, request):
        self.request = request

    def make(self):
        return ContractorQueryset(self.request).get_queryset()

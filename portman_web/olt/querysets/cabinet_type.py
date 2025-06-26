from ..models import OLTCabinetType


class CabinetTypeQueryset:
    def __init__(self, request):
        self.request = request

    def get_queryset(self):
        queryset = OLTCabinetType.objects.all()
        name = self.request.query_params.get('name', None)
        model = self.request.query_params.get('model', None)
        if name:
            queryset = queryset.filter(name__icontains=name)

        if model:
            queryset = queryset.filter(code__icontains=model)

        queryset = queryset.exclude(deleted_at__isnull=False).order_by('-id')
        return queryset


class ContractorQueryset(CabinetTypeQueryset):
    def get_queryset(self):
        queryset = super().get_queryset()
        #queryset.filter
        return queryset


class CabinetTypeQuerysetFactory:
    def __init__(self, request):
        self.request = request

    def make(self):
        return ContractorQueryset(self.request).get_queryset()

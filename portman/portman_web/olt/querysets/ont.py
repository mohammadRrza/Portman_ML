from ..models import ONT

class OntQueryset:
    def __init__(self, request):
        self.request = request

    def get_queryset(self):
        queryset = ONT.objects.all()
        type_id = self.request.query_params.get('type_id', None)
        splitter_id = self.request.query_params.get('splitter_id', None)
        patch_cord_type_id = self.request.query_params.get('patch_cord_type_id', None)

        if type_id:
            queryset = queryset.filter(ont_type__id=type_id)

        if splitter_id:
            queryset = queryset.filter(splitter__id=splitter_id)

        if patch_cord_type_id:
            queryset.filter(patch_cord_type__id=patch_cord_type_id)

        queryset = queryset.exclude(deleted_at__isnull=False).order_by('-id')
        return queryset


class ContractorQueryset(OntQueryset):
    def get_queryset(self):
        queryset = super().get_queryset()
        #queryset.filter
        return queryset


class OntQuerysetFactory:
    def __init__(self, request):
        self.request = request

    def make(self):
        return ContractorQueryset(self.request).get_queryset()

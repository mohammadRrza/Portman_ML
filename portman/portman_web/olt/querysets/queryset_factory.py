from .cabinet import CabinetQuerysetFactory
from .cabinet_type import CabinetTypeQuerysetFactory
from .odc import OdcQuerysetFactory
from .olt import OltQuerysetFactory
from .fat import FatQuerysetFactory
from .splitter import SplitterQuerysetFactory
from .ont import OntQuerysetFactory
from .user import UserQuerysetFactory
from .handhole import HandholeQuerysetFactory
from .microduct import MicroductQuerysetFactory
from .cable import CableQuerysetFactory
from .building import BuildingQuerysetFactory
from .reserved_ports import ReservedPortsQuerysetFactory

class QuerysetFactoryMap:
    def __init__(self):
        self.__resource_types = {}

    def register_type(self, name, klass):
        if name in self.__resource_types:
            raise Exception(f'Queryset Type {name} Already Registered!')
        self.__resource_types[name] = klass

    def get_type(self, name):
        if name in self.__resource_types:
            return self.__resource_types[name]
        raise Exception(f'Queryset Type {name} is Not Registered!')


class QuerysetFactory:
    queryset_factory = QuerysetFactoryMap()
    queryset_factory.register_type('cabinet', CabinetQuerysetFactory)
    queryset_factory.register_type('cabinet_type', CabinetTypeQuerysetFactory)
    queryset_factory.register_type('odc', OdcQuerysetFactory)
    queryset_factory.register_type('olt', OltQuerysetFactory)
    queryset_factory.register_type('fat', FatQuerysetFactory)
    queryset_factory.register_type('splitter', SplitterQuerysetFactory)
    queryset_factory.register_type('ont', OntQuerysetFactory)
    queryset_factory.register_type('user', UserQuerysetFactory)
    queryset_factory.register_type('handhole', HandholeQuerysetFactory)
    queryset_factory.register_type('microduct', MicroductQuerysetFactory)
    queryset_factory.register_type('cable', CableQuerysetFactory)
    queryset_factory.register_type('building', BuildingQuerysetFactory)
    queryset_factory.register_type('reserved_ports', ReservedPortsQuerysetFactory)


    @classmethod
    def make(cls, type_name, request):
        queryset_class = cls.queryset_factory.get_type(type_name)
        return queryset_class(request).make()

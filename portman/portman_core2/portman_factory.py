class PortmanFactory:
    def __init__(self):
        self.__resource_types = {}  # name:class

    def register_type(self, name, klass):


        if name in self.__resource_types:
            raise Exception('Resource Type {0} Already Registered!'.format(name))

        self.__resource_types[name] = klass

    def get_type(self, name):

        if name in self.__resource_types:
            return self.__resource_types[name]

        raise Exception('Resource Type "%s" is Not Registered!' % name)

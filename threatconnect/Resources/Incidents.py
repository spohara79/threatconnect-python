""" standard """
import types

""" custom modules """
from threatconnect import FilterMethods
from threatconnect.Properties.IncidentsProperties import IncidentsProperties
from threatconnect.Resource import Resource
from threatconnect.FilterObject import FilterObject

""" Note: PEP 8 intentionally ignored for variable/methods to match API standard. """


class Incidents(Resource):
    """ """

    def __init__(self, tc_obj):
        """ """
        super(Incidents, self).__init__(tc_obj)
        self._filter_class = IncidentFilterObject

        # set properties
        properties = IncidentsProperties()
        self._http_method = properties.http_method
        self._owner_allowed = properties.base_owner_allowed
        self._resource_pagination = properties.resource_pagination
        self._request_uri = properties.base_path
        self._resource_type = properties.resource_type


class IncidentFilterObject(FilterObject):
    """ """
    def __init__(self):
        """ """
        super(IncidentFilterObject, self).__init__()
        self._owners = []

        # define properties for resource type
        self._properties = IncidentsProperties()
        self._owner_allowed = self._properties.base_owner_allowed
        self._resource_pagination = self._properties.resource_pagination
        self._request_uri = self._properties.base_path
        self._resource_type = self._properties.resource_type

        #
        # add_obj filter methods
        #
        for method_name in self._properties.filters:
            method = getattr(FilterMethods, method_name)
            setattr(self, method_name, types.MethodType(method, self))


""" standard """
import types

""" custom """
from threatconnect import FilterMethods
from threatconnect.Properties.OwnersProperties import OwnersProperties
from threatconnect.FilterObject import FilterObject
from threatconnect.Resource import Resource

""" Note: PEP 8 intentionally ignored for variable/methods to match API standard. """


class Owners(Resource):
    """ """
    def __init__(self, tc_obj):
        """ """
        super(Owners, self).__init__(tc_obj)
        self._filter_class = OwnerFilterObject

        # set properties
        properties = OwnersProperties()
        self._http_method = properties.http_method
        self._owner_allowed = properties.indicator_owner_allowed
        self._resource_pagination = properties.resource_pagination
        self._request_uri = properties.base_path
        self._resource_type = properties.resource_type

    def get_owner_by_id(self, data):
        for obj in self._objects:
            if obj.get_id() == data:
                return obj
        return None

    def get_owner_by_name(self, data):
        for obj in self._objects:
            if obj.get_name() == data:
                return obj
        return None

    def get_owner_names(self):
        owner_names = []
        for obj in self._objects:
            owner_names.append(obj.get_name())
        return owner_names


class OwnerFilterObject(FilterObject):
    """ """

    def __init__(self):
        """ """
        super(OwnerFilterObject, self).__init__()
        self._property_class = OwnersProperties
        self._properties_class = OwnersProperties

        # define properties for resource type
        self._properties = self._properties_class()
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

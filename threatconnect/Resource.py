""" standard """
import dateutil.parser
import sys
import time
import uuid

""" custom """
from threatconnect.Config.FilterOperator import FilterOperator
from threatconnect.Config.PropertiesAction import PropertiesAction
from threatconnect.Config.PropertiesEnums import ApiStatus
from threatconnect.Config.ResourceProperties import ResourceProperties
from threatconnect.Config.ResourceType import ResourceType
from threatconnect.DataFormatter import (format_header, format_item)
from threatconnect.Properties.GroupProperties import GroupProperties
from threatconnect.Properties.IndicatorProperties import IndicatorProperties
from threatconnect.RequestObject import RequestObject
from threatconnect.Validate import get_resource_type


class Resource(object):
    """ """

    def __init__(self, tc_obj):
        """ """
        self._tc = tc_obj

        # filtered resource object list
        self._objects = []

        # master resource object list
        self._master_objects = []

        # filtered resource indexes
        self._object_res_id_idx = {}
        self._object_res_name_idx = {}

        # master resource indexes
        self._master_res_id_idx = {}
        self._master_object_id_idx = {}

        # master resource indexes for post filtering
        self._date_added_idx = {}
        self._file_type_idx = {}

        # defaults
        self._api_response = []
        self._current_filter = None
        self._error = False
        self._error_messages = []
        self._filter_class = None
        self._filter_objects = []
        self._http_method = None
        self._max_results = None
        self._method = None
        self._object_class = None
        self._owners = []
        self._owner_allowed = False
        self._request_object = None
        self._request_uri = None
        self._resource_object = None
        self._resource_pagination = False
        self._resource_type = None
        self._result_count = 0
        self._status = ApiStatus.SUCCESS
        self._status_code = []
        self._uris = []

    def add(self, resource_name):
        """add resource using writable api"""
        # switch any multiple resource request to single result request
        if self._resource_type.value % 10:
            self._resource_type = ResourceType(self._resource_type.value - 5)
        # get properties for the object
        properties = ResourceProperties[self._resource_type.name].value(PropertiesAction.POST)

        # generate unique temporary id
        resource_id = uuid.uuid4().int

        # resource object
        resource_object = properties.resource_object
        # set resource id
        resource_object.set_id(resource_id)
        # set resource name
        resource_object.set_name(resource_name)
        # set resource api action
        resource_object.set_api_action('add')

        # build request object
        request_object = RequestObject(self._resource_type.name, resource_id)
        request_object.set_description(
            'Adding %s resource (%s)' % (self._resource_type.name.lower(), resource_name))
        request_object.set_http_method(properties.http_method)
        request_object.set_request_uri(properties.post_path)
        request_object.set_owner_allowed(False)
        request_object.set_resource_pagination(False)
        request_object.set_resource_type(self._resource_type)

        # add to temporary object storage
        self.add_master_resource_obj(resource_object, resource_id)

        res = self.get_resource_by_id(resource_id)
        request_object.set_resource_object_id(id(res))
        res.set_request_object(request_object)

        # add resource object to parent object
        self.add_obj(res)

        # return object for modification
        return res

    # def associate(self, resource_obj, indicator):
    #     """ """
    #     self._associate(resource_obj, indicator, PropertiesAction.POST, 'Add')
    #
    # def disassociate(self, resource_obj, indicator):
    #     """ """
    #     self._associate(resource_obj, indicator, PropertiesAction.DELETE, 'Delete')
    #
    # @staticmethod
    # # TODO: this is the same for add and delete
    # def _associate(resource_obj, indicator, http_method, action):
    #     """
    #     POST /v2/groups/incidents/119842/indicators/addresses/10.0.2.5
    #     POST /v2/groups/emails/747227/indicators/emailAddresses/bcs150@badguys.com
    #
    #     POST /v2/indicators/addresses/10.0.2.5/groups/incidents/119842
    #     POST /v2/groups/emails/747227/groups/adversaries/747266
    #     """
    #
    #     #
    #     # get indicator type and properties
    #     #
    #     indicator_resource_type = get_resource_type(indicator)
    #     # get indicator properties for the object
    #     if indicator_resource_type.value % 10:
    #         indicator_resource_type = ResourceType(indicator_resource_type.value - 5)
    #     indicator_properties = ResourceProperties[indicator_resource_type.name].value()
    #     indicator_uri = indicator_properties.resource_uri_attribute
    #
    #     #
    #     # prepare the request
    #     #
    #     resource_type = resource_obj.request_object.resource_type
    #
    #     # get properties for the object
    #     if resource_type.value % 10:
    #         resource_type = ResourceType(resource_type.value - 5)
    #     properties = ResourceProperties[resource_type.name].value(http_method)
    #
    #     request_object = RequestObject(resource_type.name, resource_obj.get_id())
    #     request_object.set_description(
    #         '%s association of indicator (%s) with resource id (%s).' % (
    #             action, indicator, resource_obj.get_id()))
    #     request_object.set_http_method(properties.http_method)
    #     request_object.set_request_uri(
    #         properties.association_add_path % (
    #             resource_obj.get_id(), indicator_uri, indicator))
    #     request_object.set_owner_allowed(False)
    #     request_object.set_resource_pagination(False)
    #     # TODO: what does this need to be?
    #     request_object.set_resource_type(ResourceType.ATTRIBUTES)
    #
    #     resource_obj.add_association_request(request_object)

    @staticmethod
    # TODO: this is the same for add and delete
    def _associate_group(resource_obj, indicator, http_method, action):
        """
        POST /v2/indicators/addresses/10.0.2.5/groups/incidents/119842
        POST /v2/groups/emails/747227/groups/adversaries/747266

        DELETE /v2/indicators/addresses/10.0.2.5/groups/incidents/119842
        DELETE /v2/groups/emails/747227/groups/adversaries/747266
        """

        #
        # get indicator type and properties
        #
        indicator_resource_type = get_resource_type(indicator)
        # switch any multiple resource request to single result request
        if indicator_resource_type.value % 10:
            indicator_resource_type = ResourceType(indicator_resource_type.value - 5)
        # get indicator properties for the object
        indicator_properties = ResourceProperties[indicator_resource_type.name].value()
        indicator_uri = indicator_properties.resource_uri_attribute

        #
        # prepare the request
        #
        resource_type = resource_obj.request_object.resource_type

        # switch any multiple resource request to single result request
        if resource_type.value % 10:
            resource_type = ResourceType(resource_type.value - 5)
        # get properties for the object
        properties = ResourceProperties[resource_type.name].value(http_method)

        request_object = RequestObject(resource_type.name, resource_obj.get_id())
        request_object.set_description(
            '%s association of indicator (%s) with resource id (%s).' % (
                action, indicator, resource_obj.get_id()))
        request_object.set_http_method(properties.http_method)
        request_object.set_request_uri(
            properties.association_add_path % (
                resource_obj.get_id(), indicator_uri, indicator))
        request_object.set_owner_allowed(False)
        request_object.set_resource_pagination(False)
        # TODO: what does this need to be?
        request_object.set_resource_type(ResourceType.ATTRIBUTES)

        resource_obj.add_association_request(request_object)

    # @staticmethod
    # def attribute_add(resource_obj, r_type, value, displayed=True):
    #     """
    #     POST /v2/groups/incidents/119842/attributes
    #     Host: api.threatconnect.com
    #     Content-Type:  application/json
    #     {
    #         "type" : "Source",
    #         "value" : "Proprietary TC-IRT Reporting",
    #         "displayed" : true
    #     }
    #     """
    #
    #     body_json = json.dumps({
    #         'type': r_type,
    #         'value': value,
    #         'displayed': displayed})
    #
    #     resource_type = resource_obj.request_object.resource_type
    #
    #     # special case for indicators
    #     if 500 <= resource_type.value <= 599:
    #         resource_type = get_resource_type(resource_obj.get_indicator())
    #
    #     # get properties for the object
    #     if resource_type.value % 10:
    #         resource_type = ResourceType(resource_type.value - 5)
    #     properties = ResourceProperties[resource_type.name].value(PropertiesAction.POST)
    #
    #     # build request object
    #     if isinstance(properties, IndicatorProperties):
    #         request_object = RequestObject(resource_type.name, resource_obj.get_indicator())
    #         request_object.set_description(
    #             'Add attribute type (%s) with value of (%s) to %s indicator.' % (
    #                 r_type, value, resource_type.name.lower()))
    #         request_object.set_body(body_json)
    #         request_object.set_http_method(properties.http_method)
    #         request_object.set_request_uri(
    #             properties.attribute_add_path % resource_obj.get_indicator())
    #         request_object.set_owner_allowed(True)
    #         request_object.set_resource_pagination(False)
    #         request_object.set_resource_type(ResourceType.ATTRIBUTES)
    #     elif isinstance(properties, GroupProperties):
    #         request_object = RequestObject(resource_type.name, resource_obj.get_id())
    #         request_object.set_description(
    #             'Add attribute type (%s) with value of (%s) to %s resource.' % (
    #                 r_type, value, resource_type.name.lower()))
    #         request_object.set_body(body_json)
    #         request_object.set_http_method(properties.http_method)
    #         request_object.set_request_uri(properties.attribute_add_path % resource_obj.get_id())
    #         request_object.set_owner_allowed(False)
    #         request_object.set_resource_pagination(False)
    #         request_object.set_resource_type(ResourceType.ATTRIBUTES)
    #
    #     resource_obj.add_attribute_request(request_object)

    # @staticmethod
    # def attribute_delete(resource_obj, attribute):
    #     """ """
    #     resource_type = resource_obj.request_object.resource_type
    #
    #     # special case for indicators
    #     if 500 <= resource_type.value <= 599:
    #         resource_type = get_resource_type(resource_obj.get_indicator())
    #
    #     # get properties for the object
    #     if resource_type.value % 10:
    #         resource_type = ResourceType(resource_type.value - 5)
    #     properties = ResourceProperties[resource_type.name].value(PropertiesAction.DELETE)
    #
    #     # build request object
    #     if isinstance(properties, IndicatorProperties):
    #         request_object = RequestObject(resource_type.name, resource_obj.get_indicator())
    #         request_object.set_description(
    #             'Deleting attribute id (%s) from indicator (%s).' % (
    #                 attribute.get_id(), resource_obj.get_indicator()))
    #         request_object.set_http_method(properties.http_method)
    #
    #         request_object.set_request_uri(
    #             properties.attribute_delete_path % (resource_obj.get_indicator(), attribute.get_id()))
    #
    #         request_object.set_owner_allowed(True)
    #         request_object.set_resource_pagination(False)
    #         request_object.set_resource_type(ResourceType.ATTRIBUTES)
    #     elif isinstance(properties, GroupProperties):
    #         request_object = RequestObject(resource_type.name, resource_obj.get_id())
    #         request_object.set_description(
    #             'Deleting attribute id (%s) from resource id (%s).' % (
    #                 attribute.get_id(), resource_obj.get_id()))
    #         request_object.set_http_method(properties.http_method)
    #
    #
    #         request_object.set_request_uri(
    #             properties.attribute_delete_path % (resource_obj.get_id(), attribute.get_id()))
    #
    #
    #         request_object.set_owner_allowed(False)
    #         request_object.set_resource_pagination(False)
    #         request_object.set_resource_type(ResourceType.ATTRIBUTES)
    #
    #     # add request to resource object to process on commit
    #     resource_obj.add_attribute_request(request_object)

    # @staticmethod
    # def attribute_update(resource_obj, attribute, value):
    #     """
    #     PUT /v2/groups/incidents/123456/attributes/54321
    #     Host: api.threatconnect.com
    #     Content-Type:  application/json
    #     {
    #         "value" : "Severe"
    #     }
    #     """
    #
    #     body_json = json.dumps({
    #         'value': value})
    #
    #     resource_type = resource_obj.request_object.resource_type
    #
    #     # special case for indicators
    #     if 500 <= resource_type.value <= 599:
    #         resource_type = get_resource_type(resource_obj.get_indicator())
    #
    #     # get properties for the object
    #     if resource_type.value % 10:
    #         resource_type = ResourceType(resource_type.value - 5)
    #     properties = ResourceProperties[resource_type.name].value(PropertiesAction.PUT)
    #
    #     # build request object
    #     if isinstance(properties, IndicatorProperties):
    #         request_object = RequestObject(resource_type.name, resource_obj.get_indicator())
    #         request_object.set_description(
    #             'Update attribute type (%s) with value of (%s) to %s resource.' % (
    #                 attribute.get_type(), value, resource_type.name.lower()))
    #         request_object.set_body(body_json)
    #         request_object.set_http_method(properties.http_method)
    #
    #         request_object.set_request_uri(
    #             properties.attribute_update_path % (resource_obj.get_indicator(), attribute.get_id()))
    #
    #         request_object.set_owner_allowed(True)
    #         request_object.set_resource_pagination(False)
    #         request_object.set_resource_type(ResourceType.ATTRIBUTES)
    #     elif isinstance(properties, GroupProperties):
    #         request_object = RequestObject(resource_type.name, resource_obj.get_id())
    #         request_object.set_description(
    #             'Update attribute type (%s) with value of (%s) to %s resource.' % (
    #                 attribute.get_type(), value, resource_type.name.lower()))
    #         request_object.set_body(body_json)
    #         request_object.set_http_method(properties.http_method)
    #
    #         request_object.set_request_uri(
    #             properties.attribute_update_path % (resource_obj.get_id(), attribute.get_id()))
    #
    #         request_object.set_owner_allowed(False)
    #         request_object.set_resource_pagination(False)
    #         request_object.set_resource_type(ResourceType.ATTRIBUTES)
    #
    #     resource_obj.add_attribute_request(request_object)

    def add_obj(self, data_obj):
        """add object to resource instance"""
        has_id = False

        # update id index
        if hasattr(data_obj, 'get_id'):
            resource_id = data_obj.get_id()
            if resource_id is not None:
                # signify that id will be used a index key
                has_id = True
                if resource_id not in self._object_res_id_idx:
                    self._object_res_id_idx.setdefault(resource_id, data_obj)
                    self._objects.append(data_obj)

        # use name if id is not available
        if hasattr(data_obj, 'get_name'):
            resource_name = data_obj.get_name()
            if resource_name is not None:
                if resource_name not in self._object_res_name_idx:
                    self._object_res_name_idx.setdefault(resource_name, []).append(data_obj)

                    # only do this if the object has no id
                    if not has_id:
                        self._objects.append(data_obj)

    def add_api_response(self, data):
        """ """
        self._api_response.append(data)

    def add_error_message(self, data):
        """ """
        self._error_messages.append(data)

    def add_filter(self, resource_type=None):
        if resource_type is not None:
            filter_obj = self._filter_class(resource_type)
        else:
            filter_obj = self._filter_class()

        # append filter object
        self._filter_objects.append(filter_obj)
        return filter_obj

    def add_owners(self, data):
        """ """
        if isinstance(data, list):
            self._owners.extend(data)
        else:
            self._owners.append(data)

    def get_group_associations(self, resource_obj, group_type=None):
        """
        GET /v2/groups/adversaries/747266/groups
        GET /v2/groups/adversaries/747266/groups/adversaries
        """
        # for indicators
        if 500 <= self._resource_type.value <= 599:
            identifier = resource_obj.get_indicator()
        else:
            identifier = resource_obj.get_id()

        groups = self._tc.groups()
        filter1 = groups.add_filter()
        filter1.filter_associations(resource_obj.resource_type, identifier, group_type)
        groups.retrieve()

        for obj in groups:
            resource_obj.add_association_group_object(obj)
        del groups

    def get_indicator_associations(self, resource_obj, indicator_type=None):
        """
        GET /v2/groups/adversaries/747266/indicators
        GET /v2/groups/adversaries/747266/indicators/addresses
        """
        # for indicators
        if 500 <= self._resource_type.value <= 599:
            identifier = resource_obj.get_indicator()
        else:
            identifier = resource_obj.get_id()

        indicators = self._tc.indicators()
        filter1 = indicators.add_filter()
        filter1.filter_associations(resource_obj.resource_type, identifier, indicator_type)
        indicators.retrieve()

        for obj in indicators:
            resource_obj.add_association_indicator_object(obj)
        del indicators

    def get_victim_associations(self, resource_obj):
        """
        GET /v2/groups/emails/747227/victims

        GET /v2/groups/emails/747227/victimAssets
        GET /v2/groups/emails/747227/victimAssets/emailAddresses
        """
        # resource_type = resource_obj.resource_type
        #
        # # switch any multiple resource request to single result request
        # if resource_type.value % 10:
        #     resource_type = ResourceType(resource_type.value - 5)
        # # get properties for the object
        # properties = ResourceProperties[resource_type.name].value()

        # for indicators
        if 500 <= self._resource_type.value <= 599:
            identifier = resource_obj.get_indicator()
            # owner_allowed = True
        else:
            identifier = resource_obj.get_id()
            # owner_allowed = False

        victims = self._tc.victims()
        filter1 = victims.add_filter()
        filter1.filter_associations(resource_obj.resource_type, identifier)
        victims.retrieve()

        for obj in victims:
            print(obj)
            resource_obj.add_association_victim_object(obj)
        del victims

        # # build request object
        # request_object = RequestObject(resource_type.name, 'group associations')
        # request_object.set_description('Get group associations for (%s).' % identifier)
        # request_object.set_http_method(properties.http_method)
        # request_object.set_request_uri(
        #     properties.association_victim_path % identifier)
        # request_object.set_owner_allowed(owner_allowed)
        # request_object.set_resource_pagination(True)
        # request_object.set_resource_type(ResourceType.VICTIMS)
        #
        # victims = self._tc.victims()
        # data_set = self._tc.api_build_request(victims, request_object)
        #
        # for obj in data_set:
        #     resource_obj.add_association_victim_object(obj)

    def get_attributes(self, resource_obj):
        """ """
        resource_type = resource_obj.request_object.resource_type

        # special case for indicators
        if 500 <= resource_type.value <= 599:
            resource_type = get_resource_type(resource_obj.get_indicator())

        # switch any multiple resource request to single result request
        if resource_type.value % 10:
            resource_type = ResourceType(resource_type.value - 5)
        # get properties for the object
        properties = ResourceProperties[resource_type.name].value()

        # build request object
        if isinstance(properties, IndicatorProperties):
            # indicator resource

            # switch any multiple resource request to single result request
            if resource_type.value % 10:
                resource_type = ResourceType(resource_type.value - 5)
            # get properties for the object
            properties = ResourceProperties[resource_type.name].value()

            request_object = RequestObject(resource_type.name, resource_obj.get_indicator())
            request_object.set_http_method(properties.http_method)
            request_object.set_request_uri(properties.attribute_path % resource_obj.get_indicator())
            request_object.set_owner_allowed(True)
            request_object.set_resource_pagination(True)
            request_object.set_resource_type(ResourceType.ATTRIBUTES)
        elif isinstance(properties, GroupProperties):
            request_object = RequestObject(resource_type.name, resource_obj.get_id())
            request_object.set_http_method(properties.http_method)
            request_object.set_request_uri(properties.attribute_path % resource_obj.get_id())
            request_object.set_owner_allowed(False)
            request_object.set_resource_pagination(True)
            request_object.set_resource_type(ResourceType.ATTRIBUTES)
        else:
            request_object = None

        attributes = self._tc.attributes()
        data_set = self._tc.api_build_request(attributes, request_object)

        for obj in data_set:
            resource_obj.add_attribute_object(obj)

    def get_resource_by_identity(self, data):
        if data in self._master_object_id_idx:
            return self._master_object_id_idx[data]

    def add_master_resource_obj(self, data_obj, index):
        """ """
        resource_object_id = id(data_obj)
        # has_id = False
        duplicate = True

        # update master resource object id index
        self._master_object_id_idx.setdefault(id(data_obj), data_obj)

        if index not in self._master_res_id_idx:
            self._master_objects.append(data_obj)
            self._master_res_id_idx.setdefault(index, data_obj)
            duplicate = False
        else:
            resource_object_id = id(self._master_res_id_idx[index])

        # #
        # # id
        # #
        # if hasattr(data_obj, 'get_id'):
        #     has_id = True
        #     resource_id = data_obj.get_id()
        #     if resource_id is not None:
        #         # avoid storing duplicate resources by checking the resource id number
        #         if resource_id not in self._object_res_id_idx:
        #             self._master_objects.append(data_obj)
        #             self._master_res_id_idx.setdefault(resource_id, data_obj)
        #         else:
        #             # merge
        #             duplicate = True
        #
        # #
        # # name
        # #
        # if not has_id:
        #     # use name if id is not available
        #     if hasattr(data_obj, 'get_name'):
        #         resource_name = data_obj.get_name()
        #         # avoid storing duplicate resources by checking the resource id number
        #         if resource_name is not None:
        #             if resource_name not in self._object_res_name_idx:
        #                 self._objects.append(data_obj)
        #                 self._master_res_id_idx.setdefault(resource_name, data_obj)
        #             else:
        #                 duplicate = True

        if not duplicate:
            # date added index
            if hasattr(data_obj, 'get_date_added'):
                if data_obj.get_date_added() is not None:
                    date_added = data_obj.get_date_added()
                    date_added = dateutil.parser.parse(date_added)
                    date_added_seconds = int(time.mktime(date_added.timetuple()))
                    self._date_added_idx.setdefault(date_added_seconds, []).append(data_obj)

            # file type index
            if hasattr(data_obj, 'get_file_type'):
                if data_obj.get_file_type() is not None:
                    self._file_type_idx.setdefault(data_obj.get_file_type(), []).append(data_obj)

        return resource_object_id

    def add_result_count(self, data_int):
        """ """
        self._result_count += data_int

    def add_status(self, data_enum):
        """ """
        self._status = ApiStatus(self._status.value & data_enum.value)

    def add_status_code(self, data_int):
        """ """
        self._status_code.append(data_int)

    def add_uris(self, data):
        """ """
        self._uris.append(data)

    def commit(self):
        """ """
        # iterate through each object in resource objects
        for obj in self._objects:
            temporary_id = None
            new_id = None
            resource_type = obj.request_object.resource_type

            # special case for indicators
            if 500 <= resource_type.value <= 599:
                resource_type = get_resource_type(obj.get_indicator())

            # the body needs to be set right before the commit
            if obj.api_action == 'add':
                print('ADD:')
                if obj.validate():
                    temporary_id = str(obj.get_id())
                    # add resource
                    obj.request_object.set_body(obj.get_json())
                    self._tc.api_build_request(self, obj.request_object)
                    new_id = str(obj.get_id())
                else:
                    print('Failed validation.')
            elif obj.api_action == 'update':
                print('UPDATE:')
                if obj.request_object is not None and obj.stage != 'new':
                    request_object = obj.request_object
                else:
                    # switch any multiple resource request to single result request
                    if resource_type.value % 10:
                        resource_type = ResourceType(resource_type.value - 5)
                    properties = ResourceProperties[resource_type.name].value(PropertiesAction.PUT)

                    if isinstance(properties, IndicatorProperties):
                        # request object for groups
                        request_object = RequestObject(resource_type.name, obj.get_indicator())
                        request_object.set_description(
                            'Update %s indicator (%s).' % (
                                self._resource_type.name.lower(), obj.get_indicator()))
                        request_object.set_body(obj.get_json())
                        request_object.set_http_method(properties.http_method)
                        request_object.set_request_uri(
                            properties.put_path % (
                                properties.resource_uri_attribute, obj.get_indicator()))
                        request_object.set_owner_allowed(True)
                        request_object.set_resource_pagination(False)
                        request_object.set_resource_type(resource_type)

                    elif isinstance(properties, GroupProperties):
                        # request object for groups
                        request_object = RequestObject(resource_type.name, obj.get_id())
                        request_object.set_description(
                            'Update %s resource object with id (%s).' % (
                                self._resource_type.name.lower(), obj.get_id()))
                        request_object.set_body(obj.get_json())
                        request_object.set_http_method(properties.http_method)
                        request_object.set_request_uri(properties.put_path % obj.get_id())
                        request_object.set_owner_allowed(False)
                        request_object.set_resource_pagination(False)
                        request_object.set_resource_type(resource_type)
                self._tc.api_build_request(self, request_object)
            elif obj.api_action == 'delete':
                print('DELETE:')
                if obj.request_object is not None and obj.stage != 'new':
                    request_object = obj.request_object
                else:
                    # switch any multiple resource request to single result request
                    if resource_type.value % 10:
                        resource_type = ResourceType(resource_type.value - 5)
                    properties = ResourceProperties[resource_type.name].value(PropertiesAction.DELETE)

                    if isinstance(properties, IndicatorProperties):
                        request_object = RequestObject(resource_type.name, obj.get_indicator())
                        request_object.set_description(
                            'Deleting %s indicator resource (%s).' % (
                                resource_type.name.lower(), obj.get_indicator()))
                        request_object.set_http_method(properties.http_method)
                        request_object.set_request_uri(
                            properties.delete_path % obj.get_indicator())
                        request_object.set_owner_allowed(False)
                        request_object.set_resource_pagination(False)
                        request_object.set_resource_type(resource_type)
                    elif isinstance(properties, GroupProperties):
                        request_object = RequestObject(resource_type.name, obj.get_id())
                        request_object.set_description(
                            'Deleting %s resource object with id (%s).' % (
                                resource_type.name.lower(), obj.get_id()))
                        request_object.set_http_method(properties.http_method)
                        request_object.set_request_uri(properties.delete_path % obj.get_id())
                        request_object.set_owner_allowed(False)
                        request_object.set_resource_pagination(False)
                        request_object.set_resource_type(resource_type)
                self._tc.api_build_request(self, request_object)

            #
            # process attribute requests
            #
            for request_object in obj.attribute_requests:
                if request_object.http_method in ['DELETE', 'POST', 'PUT']:
                    # instantiate attribute resource object
                    attributes = self._tc.attributes()
                    data_set = self._tc.api_build_request(attributes, request_object)

                    # add returned attribute to resource object
                    for attribute_object in data_set:
                        obj.add_attribute_object(attribute_object)

                    del attributes
            #
            # process tag requests
            #
            for request_object in obj.tag_requests:
                # replace temporary id
                if temporary_id != new_id:
                    request_uri = str(request_object.request_uri).replace(temporary_id, new_id)
                    request_object.set_request_uri(request_uri)

                if request_object.http_method in ['DELETE', 'POST', 'PUT']:
                    # instantiate tag resource object
                    tags = self._tc.tags()
                    self._tc.api_build_request(tags, request_object)

                    del tags

                    # TODO: why does adding a tag not return a tag object?
                    # data_set = self._tc.api_build_request(tags, request_object)
                    # add returned tag to resource object
                    # for tag_object in data_set:
                    #     obj.add_tag_object(tag_object)

            #
            # process associations requests
            #
            for request_object in obj.association_requests:
                # replace temporary id
                if temporary_id != new_id:
                    request_uri = str(request_object.request_uri).replace(temporary_id, new_id)
                    request_object.set_request_uri(request_uri)

                if request_object.http_method in ['DELETE', 'POST', 'PUT']:
                    # instantiate association resource object
                    # TODO: using tags here because there is no dummy object
                    associations = self._tc.tags()
                    self._tc.api_build_request(associations, request_object)

                    del associations

    def delete(self, resource_id):
        """ """
        # switch any multiple resource request to single result request
        if self._resource_type.value % 10:
            self._resource_type = ResourceType(self._resource_type.value - 5)
        # set properties
        properties = ResourceProperties[self._resource_type.name].value(PropertiesAction.DELETE)

        # resource object
        # if self.get_resource_by_id(resource_id) is not None:
        #     resource_object = self.get_resource_by_id(resource_id)
        # else:
        #     resource_object = properties.resource_object
        #     # set resource id
        #     resource_object.set_id(resource_id)

        resource_object = properties.resource_object
        # set resource id
        resource_object.set_id(resource_id)
        # set resource api action
        resource_object.set_api_action('delete')

        # build request object
        request_object = RequestObject(self._resource_type.name, resource_id)
        request_object.set_description(
            'Deleting %s resource object with id (%s).' % (
                self._resource_type.name.lower(), resource_id))
        request_object.set_http_method(properties.http_method)
        request_object.set_request_uri(properties.delete_path % resource_id)
        request_object.set_owner_allowed(False)
        request_object.set_resource_pagination(False)
        request_object.set_resource_type(self._resource_type)

        # add to temporary object storage
        roi = self.add_master_resource_obj(resource_object, resource_id)

        res = self.get_resource_by_identity(roi)
        request_object.set_resource_object_id(id(res))
        res.set_request_object(request_object)

        # add resource object to parent object
        self.add_obj(res)

    def get_api_response(self):
        """ """
        return self._api_response

    def get_current_filter(self):
        """ """
        return self._current_filter

    def get_tags(self, resource_obj):
        """ """
        resource_type = resource_obj.request_object.resource_type

        # special case for indicators
        if 500 <= resource_type.value <= 599:
            resource_type = get_resource_type(resource_obj.get_indicator())

        # switch any multiple resource request to single result request
        if resource_type.value % 10:
            resource_type = ResourceType(resource_type.value - 5)
        # get properties for the object
        properties = ResourceProperties[resource_type.name].value()

        # build request object
        if isinstance(properties, IndicatorProperties):
            request_object = RequestObject(resource_type.name, resource_obj.get_indicator())
            request_object.set_http_method(properties.http_method)
            request_object.set_request_uri(properties.tag_path % resource_obj.get_indicator())
            request_object.set_owner_allowed(True)
            request_object.set_resource_pagination(True)
            request_object.set_resource_type(ResourceType.TAGS)
        elif isinstance(properties, GroupProperties):
            request_object = RequestObject(resource_type.name, resource_obj.get_id())
            request_object.set_http_method(properties.http_method)
            request_object.set_request_uri(properties.tag_path % resource_obj.get_id())
            request_object.set_owner_allowed(False)
            request_object.set_resource_pagination(True)
            request_object.set_resource_type(ResourceType.TAGS)
        else:
            request_object = None

        tags = self._tc.tags()
        data_set = self._tc.api_build_request(tags, request_object)

        for obj in data_set:
            resource_obj.add_tag_object(obj)

    def filter_date_added(self, data, operator):
        """ """
        if operator == FilterOperator.EQ:
            if data in self._date_added_idx:
                for data_obj in self._date_added_idx[data]:
                    data_obj.add_matched_filter(
                        'date_added|%s (%s)' % (data, operator.name.lower()))
                    yield data_obj
        else:
            for key, data_obj_list in self._date_added_idx.items():
                if operator.value(key, data):
                    for data_obj in data_obj_list:
                        data_obj.add_matched_filter(
                            'date_added|%s (%s)' % (data, operator.name.lower()))
                        yield data_obj

    def filter_file_type(self, data, operator):
        """ """
        if operator == FilterOperator.EQ:
            if data in self._file_type_idx:
                for data_obj in self._file_type_idx[data]:
                    data_obj.add_matched_filter(
                        'file_type|%s (%s)' % (data, operator.name.lower()))
                    yield data_obj
        else:
            for key, data_obj_list in self._file_type_idx.items():
                if operator.value(key, data):
                    for data_obj in data_obj_list:
                        data_obj.add_matched_filter(
                            'file_type|%s (%s)' % (data, operator.name.lower()))
                        yield data_obj

    def get_http_method(self):
        """ """
        return self._http_method

    def get_json(self):
        """ """
        return self._resource_object.get_json()

    def get_max_results(self):
        """ """
        return self._max_results

    def get_object_class(self):
        """ """
        return self._object_class

    def get_owner_allowed(self):
        """ """
        return self._owner_allowed

    def get_owners(self):
        """ """
        return self._owners

    def get_resource_pagination(self):
        """ """
        return self._resource_pagination

    def get_resource_by_id(self, data):
        """ """
        if data in self._master_res_id_idx:
            return self._master_res_id_idx[data]
        else:
            print('(%s) was not found in index.' % data)
            return None
            # sys.exit(1)

    def get_resource_by_name(self, data):
        """ """
        if data in self._master_res_id_idx:
            return self._master_res_id_idx[data]
        else:
            print('(%s) was not found in index.' % data)
            sys.exit(1)

    def get_request_uri(self):
        """ """
        return self._request_uri

    def get_result_count(self):
        """ """
        return self._result_count

    def get_status(self):
        """ """
        return self._status

    def get_status_code(self):
        """ """
        return self._status_code

    def get_uris(self):
        """ """
        return self._uris

    @property
    def request_object(self):
        """ """
        return self._request_object

    @property
    def resource_type(self):
        """ """
        return self._resource_type

    def retrieve(self):
        """ """
        good_filters = []
        for filter_obj in self._filter_objects:
            if filter_obj.error:
                self._error_messages = True
                for filter_error in filter_obj.get_errors():
                    self.add_error_message(filter_error)
            else:
                good_filters.append(filter_obj)

        # retrieve resources for good filters
        if not self._error_messages:
            self._tc.get_filtered_resource(self, good_filters)

    def set_current_filter(self, data):
        """ """
        self._current_filter = data

    def set_http_method(self, data):
        """ """
        self._http_method = data

    def set_max_results(self, data_int):
        """ """
        self._max_results = int(data_int)

    def set_owner_allowed(self, data):
        """ """
        self._owner_allowed = data

    def set_resource_pagination(self, data):
        """ """
        self._resource_pagination = data

    # def set_request_object(self, data_obj):
    #     """ """
    #     self._request_object = data_obj

    def set_request_uri(self, data):
        """ """
        self._request_uri = data

    def set_resource_type(self, data_enum):
        """ """
        self._resource_type = data_enum

    # @staticmethod
    # def add_tag(resource_obj, tag):
    #     """ """
    #     resource_type = resource_obj.request_object.resource_type
    #
    #     # special case for indicators
    #     if 500 <= resource_type.value <= 599:
    #         resource_type = get_resource_type(resource_obj.get_indicator())
    #
    #     # get properties for the object
    #     if resource_type.value % 10:
    #         resource_type = ResourceType(resource_type.value - 5)
    #     properties = ResourceProperties[resource_type.name].value(PropertiesAction.POST)
    #
    #     # build request object
    #     request_object = RequestObject(resource_type.name, tag)
    #     request_object.set_http_method(properties.http_method)
    #     request_object.set_resource_pagination(False)
    #     request_object.set_resource_type(ResourceType.TAGS)
    #
    #     if isinstance(properties, IndicatorProperties):
    #         request_object.set_description(
    #             'Add tag (%s) to indicator (%s).' % (
    #                 tag, resource_obj.get_id()))
    #         request_object.set_request_uri(
    #             properties.tag_add_path % (
    #                 resource_obj.get_indicator(), tag))
    #         request_object.set_owner_allowed(True)
    #     elif isinstance(properties, GroupProperties):
    #         request_object.set_description(
    #             'Add tag (%s) to resource id (%s).' % (
    #                 tag, resource_obj.get_id()))
    #         request_object.set_request_uri(
    #             properties.tag_add_path % (resource_obj.get_id(), tag))
    #         request_object.set_owner_allowed(False)
    #
    #     # add request to resource object to process on commit
    #     resource_obj.add_tag_request(request_object)

    # @staticmethod
    # def delete_tag(resource_obj, tag):
    #     """ """
    #     resource_type = resource_obj.request_object.resource_type
    #
    #     # special case for indicators
    #     if 500 <= resource_type.value <= 599:
    #         resource_type = get_resource_type(resource_obj.get_indicator())
    #
    #     # get properties for the object
    #     if resource_type.value % 10:
    #         resource_type = ResourceType(resource_type.value - 5)
    #     properties = ResourceProperties[resource_type.name].value(PropertiesAction.DELETE)
    #
    #     # build request object
    #     request_object = RequestObject(resource_type.name, tag)
    #
    #     if isinstance(properties, IndicatorProperties):
    #         request_object.set_description(
    #             'Deleting tag (%s) from resource id (%s).' % (
    #                 tag, resource_obj.get_indicator()))
    #         request_object.set_http_method(properties.http_method)
    #         request_object.set_request_uri(
    #             properties.tag_delete_path % (resource_obj.get_indicator(), tag))
    #         request_object.set_owner_allowed(False)
    #         request_object.set_resource_pagination(False)
    #         request_object.set_resource_type(ResourceType.TAGS)
    #     elif isinstance(properties, GroupProperties):
    #         request_object.set_description(
    #             'Deleting tag (%s) from resource id (%s).' % (
    #                 tag, resource_obj.get_id()))
    #         request_object.set_http_method(properties.http_method)
    #         request_object.set_request_uri(
    #             properties.tag_delete_path % (resource_obj.get_id(), tag))
    #         request_object.set_owner_allowed(False)
    #         request_object.set_resource_pagination(False)
    #         request_object.set_resource_type(ResourceType.TAGS)
    #
    #     # add request to resource object to process on commit
    #     resource_obj.add_tag_request(request_object)

    # def get_tags(self, resource_obj):
    #     """ """
    #     resource_type = resource_obj.request_object.resource_type
    #
    #     # special case for indicators
    #     if 500 <= resource_type.value <= 599:
    #         resource_type = get_resource_type(resource_obj.get_indicator())
    #
    #     # switch any multiple resource request to single result request
    #     if resource_type.value % 10:
    #         resource_type = ResourceType(resource_type.value - 5)
    #     # get properties for the object
    #     properties = ResourceProperties[resource_type.name].value()
    #
    #     # build request object
    #     if isinstance(properties, IndicatorProperties):
    #         request_object = RequestObject(resource_type.name, resource_obj.get_indicator())
    #         request_object.set_http_method(properties.http_method)
    #         request_object.set_request_uri(properties.tag_path % resource_obj.get_indicator())
    #         request_object.set_owner_allowed(True)
    #         request_object.set_resource_pagination(True)
    #         request_object.set_resource_type(ResourceType.TAGS)
    #     elif isinstance(properties, GroupProperties):
    #         request_object = RequestObject(resource_type.name, resource_obj.get_id())
    #         request_object.set_http_method(properties.http_method)
    #         request_object.set_request_uri(properties.tag_path % resource_obj.get_id())
    #         request_object.set_owner_allowed(False)
    #         request_object.set_resource_pagination(True)
    #         request_object.set_resource_type(ResourceType.TAGS)
    #
    #     tags = self._tc.tags()
    #     data_set = self._tc.api_build_request(tags, request_object)
    #
    #     for obj in data_set:
    #         resource_obj.add_tag_object(obj)

    def update(self, resource_id):
        """ """
        # switch any multiple resource request to single result request
        if self._resource_type.value % 10:
            self._resource_type = ResourceType(self._resource_type.value - 5)
        # set properties
        properties = ResourceProperties[self._resource_type.name].value(PropertiesAction.PUT)

        # resource object
        resource_object = properties.resource_object
        # set resource id
        resource_object.set_id(resource_id)
        # set resource api action
        resource_object.set_api_action('update')

        # build request object
        request_object = RequestObject(self._resource_type.name, resource_id)
        request_object.set_description(
            'Update %s resource object with id (%s).' % (
                self._resource_type.name.lower(), resource_id))
        request_object.set_http_method(properties.http_method)
        request_object.set_request_uri(properties.put_path % resource_id)
        request_object.set_owner_allowed(False)
        request_object.set_resource_pagination(False)
        request_object.set_resource_type(self._resource_type)

        # add to temporary object storage
        self.add_master_resource_obj(resource_object, resource_id)

        res = self.get_resource_by_id(resource_id)
        request_object.set_resource_object_id(id(res))
        res.set_request_object(request_object)

        # add resource object to parent object
        self.add_obj(res)

        return res

    def __iter__(self):
        """ """
        for obj in self._objects:
            yield obj

    def __len__(self):
        """ """
        return len(self._objects)

    def __str__(self):
        """ """
        obj_str = format_header('Resource Object')
        printable_items = dict(self.__dict__)
        for key, val in sorted(printable_items.items()):
            obj_str += format_item(key, val)

        return obj_str


# class ResourceObject(object):
# """ """
#     def __init__(self):
#         """ """
#         self._id = None
#         self._data_methods = None
#         self._methods = []
#         self._matched_filters = []
#         self._name = None
#         self._object_type = None
#         self._url = None
#
#     # def add_id(self, data):
#     #     """ """
#     #     self._id = data
#
#     def add_matched_filter(self, data):
#         """ """
#         self._matched_filters.append(data)
#
#     def add_method(self, data):
#         """ """
#         self._methods.append(data)
#
#     # def add_name(self, data):
#     #     """ """
#     #     self._name = data
#
#     def add_request_url(self, data):
#         """ """
#         self._url = data
#
#     # def get_id(self):
#     #     """ """
#     #     return self._id
#
#     def get_data_methods(self):
#         """ """
#         return self._data_methods
#
#     def get_matched_filters(self):
#         """ """
#         return self._matched_filters
#
#     def get_methods(self):
#         """ """
#         return self._methods
#
#     # def get_name(self):
#     #     """ """
#     #     return self._name
#
#     def get_request_url(self):
#         """ """
#         return self._url
#
#     def __str__(self):
#         """ """
#         if self.get_name() is not None:
#             obj_str = format_header('%s' % self.get_name())
#         else:
#             obj_str = format_header('%s' % 'Resource')
#         printable_items = dict(self.__dict__)
#         printable_items.pop('_data_methods')
#         printable_items.pop('_object_type')
#         for key, val in sorted(printable_items.items()):
#             obj_str += format_item(key, val)
#
#         return obj_str


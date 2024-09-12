"""PDS Registry Client lreated classes."""
from __future__ import print_function

import logging
from datetime import datetime

from pds.api_client import ApiClient
from pds.api_client import Configuration
from pds.api_client.api.all_products_api import AllProductsApi

logger = logging.getLogger(__name__)

DEFAULT_API_BASE_URL = "https://pds.nasa.gov/api/search/1"


class PDSRegistryClient:
    """Used to connect to the PDSRegistry."""

    def __init__(self, base_url=DEFAULT_API_BASE_URL):
        """Constructor.

        :param base_url: default value is the official production server, can be specified otherwise
        """
        configuration = Configuration()
        configuration.host = base_url
        self.api_client = ApiClient(configuration)


class Products:
    """Use to access any class of planetary products."""

    SORT_PROPERTY = "ops:Harvest_Info.ops:harvest_date_time"
    PAGE_SIZE = 100

    def __init__(self, client: PDSRegistryClient):
        """Use to access any class of planetary products.

        :param client: instance of PDSRegistryClient
        """
        self._products = AllProductsApi(client.api_client)
        self._q_string = ""
        self._latest_harvest_time = None
        self._crt_page_iterator = None
        self._counter_in_page = None

    def __add_clause(self, clause):
        clause = f"({clause})"
        if self._q_string:
            self._q_string += f" and {clause}"
        else:
            self._q_string = clause

    def has_target(self, identifier: str):
        """Selects products having a given target.

        Lazy evaluation is used to only apply the filter when one iterates on it.
        This is done so that multiple filters can be combined before the request is actually sent.
        :param identifier: lidvid of the target
        :return: a Products instance with the target filter added.
        """
        clause = f'ref_lid_target eq "{identifier}"'
        self.__add_clause(clause)
        return self

    def before(self, d: datetime):
        """Selects products which start date is before given datetime.

        :param d: datetime
        :return: a Products instance with before filter applied
        """
        iso8601_datetime = d.isoformat().replace("+00:00", "Z")
        clause = f'pds:Time_Coordinates.pds:start_date_time le "{iso8601_datetime}"'
        self.__add_clause(clause)
        return self

    def after(self, d: datetime):
        """Selects products which end date is after given datetime.

        :param d: datetime
        :return: a Products instance with after filter applied
        """
        iso8601_datetime = d.isoformat().replace("+00:00", "Z")
        clause = f'pds:Time_Coordinates.pds:stop_date_time ge "{iso8601_datetime}"'
        self.__add_clause(clause)
        return self

    def of_collection(self, id: str):
        """Selects products which belong to a collection.

        :param id: the collection id, e.g. a lidvid
        :return: a Products instance with after filter applied
        """
        clause = f'ops:Provenance.ops:parent_collection_identifier eq "{id}"'
        self.__add_clause(clause)
        return self

    def _init_new_page(self):
        logger.info("get new page from API")

        # if not first page, this was the last page is number of products is less than page size.
        if self._counter_in_page is not None and self._counter_in_page < self.PAGE_SIZE:
            raise StopIteration("This was the last page")

        kwargs = dict()
        kwargs["sort"] = [self.SORT_PROPERTY]
        kwargs["limit"] = self.PAGE_SIZE

        if self._latest_harvest_time is not None:
            kwargs["search_after"] = [self._latest_harvest_time]

        if len(self._q_string) > 0:
            kwargs["q"] = f"({self._q_string})"

        results = self._products.product_list(**kwargs)

        self._counter_in_page = 0
        self._crt_page_iterator = iter(results.data)

    def __iter__(self):
        """:return: an iterator on the filtered products."""
        self._init_new_page()
        return self

    def _get_new_product(self):
        self._counter_in_page += 1
        next_product = next(self._crt_page_iterator)
        self._latest_harvest_time = next_product.properties[self.SORT_PROPERTY][0]
        return next_product

    def __next__(self):
        """Iterate on the full list of filtered results.

        The pagination implemented by the web API is handle here for the user.

        :return: next filtered product
        """
        try:
            return self._get_new_product()
        except StopIteration:
            self._init_new_page()
            return self._get_new_product()

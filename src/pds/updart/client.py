"""PDS Registry Client lreated classes."""
from __future__ import print_function

from datetime import datetime

from pds.api_client import ApiClient
from pds.api_client import Configuration
from pds.api_client.api.all_products_api import AllProductsApi

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

    def __init__(self, client: PDSRegistryClient):
        """Use to access any class of planetary products.

        :param client: instance of PDSRegistryClient
        """
        self._products = AllProductsApi(client.api_client)
        self._q_string = ""
        self._crt_page_iterator = None

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

    def __iter__(self):
        """:return: an iterator on the filtered products."""
        if len(self._q_string) > 0:
            results = self._products.product_list(q=f"({self._q_string})")
        else:
            results = self._products.product_list()

        self._crt_page_iterator = iter(results.data)
        return self

    def __next__(self):
        """Iterate on the full list of filtered results.

        The pagination implemented by the web API is handle here for the user.

        :return: next filtered product
        """
        try:
            return next(self._crt_page_iterator)
        except StopIteration:
            # TODO: implement next page retrieval and return first element of next page
            raise

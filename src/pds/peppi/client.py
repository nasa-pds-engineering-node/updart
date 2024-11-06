"""PDS Registry Client related classes."""
import logging
from datetime import datetime
from typing import Literal
from typing import Optional

from pds.api_client import ApiClient
from pds.api_client import Configuration
from pds.api_client.api.all_products_api import AllProductsApi

logger = logging.getLogger(__name__)

DEFAULT_API_BASE_URL = "https://pds.nasa.gov/api/search/1"
"""Default URL used when querying PDS API"""

PROCESSING_LEVELS = Literal["telemetry", "raw", "partially-processed", "calibrated", "derived"]
"""Processing level values that can be used with has_processing_level()"""


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
        self._page_counter = None
        self._expected_pages = None

    def __add_clause(self, clause):
        if self._page_counter or self._expected_pages:
            raise RuntimeError(
                "Cannot modify query while paginating over previous query results.\n"
                "Use the reset() method on this Products instance or exhaust all returned "
                "results before assigning new query clauses."
            )

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

    def has_investigation(self, identifier: str):
        """Selects products having a given investigation.

        Lazy evaluation is used to only apply the filter when one iterates on it.
        This is done so that multiple filters can be combined before the request is actually sent.
        :param identifier: lidvid of the target
        :return: a Products instance with the investigation filter added.
        """
        clause = f'ref_lid_investigation eq "{identifier}"'
        self.__add_clause(clause)
        return self

    def before(self, d: datetime):
        """Selects products with a start date before the given datetime.

        :param d: datetime
        :return: a Products instance with a before filter applied
        """
        iso8601_datetime = d.isoformat().replace("+00:00", "Z")
        clause = f'pds:Time_Coordinates.pds:start_date_time le "{iso8601_datetime}"'
        self.__add_clause(clause)
        return self

    def after(self, d: datetime):
        """Selects products with an end date after the given datetime.

        :param d: datetime
        :return: a Products instance with an after filter applied
        """
        iso8601_datetime = d.isoformat().replace("+00:00", "Z")
        clause = f'pds:Time_Coordinates.pds:stop_date_time ge "{iso8601_datetime}"'
        self.__add_clause(clause)
        return self

    def of_collection(self, identifier: str):
        """Selects products which belong to a Collection.

        :param identifier: the collection id, e.g. a lidvid
        :return: a Products instance with a parent collection identifier filter applied
        """
        clause = f'ops:Provenance.ops:parent_collection_identifier eq "{identifier}"'
        self.__add_clause(clause)
        return self

    def observationals(self):
        """Selects Observational products for a specific filter.

        :return: a Products instance with Observational product class filter applied
        """
        clause = 'product_class eq "Product_Observational"'
        self.__add_clause(clause)
        return self

    def collections(self, type: Optional[str] = None):
        """Selects Collection products for a specific filter.

        :param type: optional collection type argument
        :return: a Products instance with Collections filter applied
        """
        clause = 'product_class eq "Product_Collection"'
        self.__add_clause(clause)

        if type:
            clause = f'pds:Collection.pds:collection_type eq "{type}"'
            self.__add_clause(clause)

        return self

    def bundles(self):
        """Selects Bundle products for a specific filter.

        :return: a Products instance with Product_Bundle filter applied
        """
        clause = 'product_class eq "Product_Bundle"'
        self.__add_clause(clause)
        return self

    def has_instrument(self, identifier: str):
        """Selects products that have an instrument matching the provided ID.

        :param identifier: the collection id, e.g. a lidvid
        :return: a Products instance with an instrument filter applied
        """
        clause = f'ref_lid_instrument eq "{identifier}"'
        self.__add_clause(clause)
        return self

    def has_instrument_host(self, identifier: str):
        """Selects products that have an instrument host matching the provided ID.

        :param identifier: the collection id, e.g. a lidvid
        :return: a Products instance with an instrument host filter applied
        """
        clause = f'ref_lid_instrument_host eq "{identifier}"'
        self.__add_clause(clause)
        return self

    def has_processing_level(self, processing_level: PROCESSING_LEVELS = "raw"):
        """Selects products with a specific processing level.

        :param processing_level: one of telemetry, raw, partially-processed, calibrated, derived
        :return: a Products instance with a processing level filter applied
        """
        clause = f'pds:Primary_Result_Summary.pds:processing_level eq "{processing_level.title()}"'
        self.__add_clause(clause)
        return self

    def get(self, identifier: str):
        """Selects products which have a lidvid matching the provided value.

        :param identifier: lidvid of the product(s) to retrieve
        :return: a Products instance with an identifier filter applied
        """
        self.__add_clause(f'lidvid like "{identifier}"')
        return self

    def filter(self, clause: str):
        """Selects products that match the provided clause.

        :param clause: a custom query clause
        :return: a Products instance with the provided filtering clause applied
        """
        self.__add_clause(clause)
        return self

    def _init_new_page(self):
        """Quieries the PDS API for the next page of results.

        Any query clauses associated to the Products instance will be included
        here. Results of the query will be available from the page iterator object.
        :return:
        """
        # Check if we've hit the expected number of pages (or exceeded in cases
        # where no results were returned from the query)
        if self._page_counter and self._page_counter >= self._expected_pages:
            raise StopIteration

        kwargs = {"sort": [self.SORT_PROPERTY], "limit": self.PAGE_SIZE}

        if self._latest_harvest_time is not None:
            kwargs["search_after"] = [self._latest_harvest_time]

        if len(self._q_string) > 0:
            kwargs["q"] = f"({self._q_string})"

        results = self._products.product_list(**kwargs)

        # If this is the first page fetch, calculate total number of expected pages
        # based on hit count
        if self._expected_pages is None:
            hits = results.summary.hits

            self._expected_pages = hits // self.PAGE_SIZE
            if hits % self.PAGE_SIZE:
                self._expected_pages += 1

            self._page_counter = 0

        for product in results.data:
            yield product
            self._latest_harvest_time = product.properties[self.SORT_PROPERTY][0]

        # If here, current page has been exhausted
        self._page_counter += 1

    def __iter__(self):
        """Generator that iterates over all filtered products.

        Handles pagination automatically by fetching new pages from the API as needed.
        """
        while True:
            try:
                for product in self._init_new_page():
                    yield product
            except RuntimeError as err:
                # Make sure we got the StopIteration that was converted to a RuntimeError,
                # otherwise we need to re-raise
                if "StopIteration" not in str(err):
                    raise err

                self.reset()
                break

    def reset(self):
        """Resets internal pagination state to default.

        This method should be called before making any modifications to the
        query clause stored by this Products instance while still paginating
        through the results of a previous query.
        """
        self._q_string = ""
        self._expected_pages = None
        self._page_counter = None
        self._latest_harvest_time = None

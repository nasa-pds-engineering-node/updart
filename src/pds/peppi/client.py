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
    """Used to connect and interface with the PDS Registry.

    Attributes
    ----------
    api_client : pds.api_client.ApiClient
        Object used to interact with the PDS Registry API

    """

    def __init__(self, base_url=DEFAULT_API_BASE_URL):
        """Creates a new instance of PDSRegistryClient.

        Parameters
        ----------
        base_url: str, optional
            The base endpoint URL of the PDS Registry API. The default value is
             the official production server, can be specified otherwise.

        """
        configuration = Configuration()
        configuration.host = base_url
        self.api_client = ApiClient(configuration)


class Products:
    """Use to access any class of planetary products via the PDS Registry API."""

    SORT_PROPERTY = "ops:Harvest_Info.ops:harvest_date_time"
    """Default property to sort results of a query by."""

    PAGE_SIZE = 100
    """Default number of results returned in each page fetch from the PDS API."""

    def __init__(self, client: PDSRegistryClient):
        """Creates a new instance of the Products class.

        Parameters
        ----------
        client: PDSRegistryClient
            The client object used to interact with the PDS Registry API.

        """
        self._products = AllProductsApi(client.api_client)
        self._q_string = ""
        self._latest_harvest_time = None
        self._page_counter = None
        self._expected_pages = None

    def __add_clause(self, clause):
        """Adds the provided clause to the query string to use on the next fetch of products from the Registry API.

        Repeated calls to this method results in a joining with any previously
        added clauses via Logical AND.

        Lazy evaluation is used to only apply the filter when one iterates on this
        Products instance. This way, multiple filters can be combined before the
        request is actually sent.

        Notes
        -----
        This method should not be called while there are still results to
        iterate over from a previous query, as this could affect the results
        of the next page fetch. The `reset()` method may be used to abandon
        a query in progress so that this method may be called safely again.

        Parameters
        ----------
        clause : str
            The query clause to append. Clause should match the domain language
            expected by the PDS Registry API

        Raises
        ------
        RuntimeError
            If this method is called while there are still results to be iterated
            over from a previous query.

        """
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
        """Adds a query clause selecting products having a given target identifier.

        Parameters
        ----------
        identifier : str
            Identifier (LIDVID) of the target.

        Returns
        -------
        This Products instance with the "has target" query filter applied.

        """
        clause = f'ref_lid_target eq "{identifier}"'
        self.__add_clause(clause)
        return self

    def has_investigation(self, identifier: str):
        """Adds a query clause selecting products having a given investigation identifier.

        Parameters
        ----------
        identifier : str
            Identifier (LIDVID) of the target.

        Returns
        -------
        This Products instance with the "has investigation" query filter applied.

        """
        clause = f'ref_lid_investigation eq "{identifier}"'
        self.__add_clause(clause)
        return self

    def before(self, dt: datetime):
        """Adds a query clause selecting products with a start date before the given datetime.

        Parameters
        ----------
        dt : datetime.datetime
            Datetime object containing the desired time.

        Returns
        -------
        This Products instance with the "before" filter applied.

        """
        iso8601_datetime = dt.isoformat().replace("+00:00", "Z")
        clause = f'pds:Time_Coordinates.pds:start_date_time le "{iso8601_datetime}"'
        self.__add_clause(clause)
        return self

    def after(self, dt: datetime):
        """Adds a query clause selecting products with an end date after the given datetime.

        Parameters
        ----------
        dt : datetime.datetime
            Datetime object containing the desired time.

        Returns
        -------
        This Products instance with the "before" filter applied.

        """
        iso8601_datetime = dt.isoformat().replace("+00:00", "Z")
        clause = f'pds:Time_Coordinates.pds:stop_date_time ge "{iso8601_datetime}"'
        self.__add_clause(clause)
        return self

    def of_collection(self, identifier: str):
        """Adds a query clause selecting products belonging to the given Parent Collection identifier.

        Parameters
        ----------
        identifier : str
            Identifier (LIDVID) of the Collection.

        Returns
        -------
        This Products instance with the "Parent Collection" filter applied.

        """
        clause = f'ops:Provenance.ops:parent_collection_identifier eq "{identifier}"'
        self.__add_clause(clause)
        return self

    def observationals(self):
        """Adds a query clause selecting only "Product Observational" type products on the current filter.

        Returns
        -------
        This Products instance with the "Observational Product" filter applied.

        """
        clause = 'product_class eq "Product_Observational"'
        self.__add_clause(clause)
        return self

    def collections(self, collection_type: Optional[str] = None):
        """Adds a query clause selecting only "Product Collection" type products on the current filter.

        Parameters
        ----------
        collection_type : str, optional
            Collection type to filter on. If not provided, all collection types
            are included.

        Returns
        -------
        This Products instance with the "Product Collection" filter applied.

        """
        clause = 'product_class eq "Product_Collection"'
        self.__add_clause(clause)

        if collection_type:
            clause = f'pds:Collection.pds:collection_type eq "{collection_type}"'
            self.__add_clause(clause)

        return self

    def bundles(self):
        """Adds a query clause selecting only "Bundle" type products on the current filter.

        Returns
        -------
        This Products instance with the "Product Bundle" filter applied.

        """
        clause = 'product_class eq "Product_Bundle"'
        self.__add_clause(clause)
        return self

    def has_instrument(self, identifier: str):
        """Adds a query clause selecting products having an instrument matching the provided identifier.

        Parameters
        ----------
        identifier : str
            Identifier (LIDVID) of the instrument.

        Returns
        -------
        This Products instance with the "has instrument" filter applied.

        """
        clause = f'ref_lid_instrument eq "{identifier}"'
        self.__add_clause(clause)
        return self

    def has_instrument_host(self, identifier: str):
        """Adds a query clause selecting products having an instrument host matching the provided identifier.

        Parameters
        ----------
        identifier : str
            Identifier (LIDVID) of the instrument host.

        Returns
        -------
        This Products instance with the "has instrument host" filter applied.

        """
        clause = f'ref_lid_instrument_host eq "{identifier}"'
        self.__add_clause(clause)
        return self

    def has_processing_level(self, processing_level: PROCESSING_LEVELS = "raw"):
        """Adds a query clause selecting products with a specific processing level.

        Parameters
        ----------
        processing_level : str, optional
            The processing level to filter on. Must be one of "telemetry", "raw",
            "partially-processed", "calibrated", or "derived". Defaults to "raw".

        Returns
        -------
        This Products instance with the "has processing level" filter applied.

        """
        clause = f'pds:Primary_Result_Summary.pds:processing_level eq "{processing_level.title()}"'
        self.__add_clause(clause)
        return self

    def get(self, identifier: str):
        """Adds a query clause selecting the product with a LIDVID matching the provided value.

        Parameters
        ----------
        identifier : str
            LIDVID of the product to filter for.

        Returns
        -------
        This Products instance with the "LIDVID identifier" filter applied.

        """
        self.__add_clause(f'lidvid like "{identifier}"')
        return self

    def filter(self, clause: str):
        """Selects products that match the provided query clause.

        Parameters
        ----------
        clause : str
            A custom query clause.

        Returns
        -------
        This Products instance with the provided filtering clause applied.
        """
        self.__add_clause(clause)
        return self

    def _init_new_page(self):
        """Quieries the PDS API for the next page of results.

        Any query clauses associated to this Products instance are included here.

        If there are results remaining from the previously acquired page,
        they are yieled on each subsequent call to this method.

        Yields
        ------
        product : pds.api_client.models.pds_product.PDSProduct
            The next product within the current page fetched from the PDS Registry
            API.

        Raises
        ------
        StopIteration
            Once all available pages of query results have been exhausted.

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
        """Iterates over all products returned by the current query filter applied to this Products instance.

        This method handles pagination automatically by fetching additional pages
        from the PDS Registry API as needed. Once all available pages and results
        have been yielded, this method will reset this Products instance to a
        default state which can be used to perform a new query.

        Yields
        ------
        product : pds.api_client.models.pds_product.PDSProduct
            The next product within the current page fetched from the PDS Registry
            API.

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

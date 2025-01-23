"""Module of the ResultSet."""
import logging

from pds.api_client.api.all_products_api import AllProductsApi

from .client import PDSRegistryClient

logger = logging.getLogger(__name__)


class ResultSet:
    """ResultSet of products on which a query has been applied."""

    _SORT_PROPERTY = "ops:Harvest_Info.ops:harvest_date_time"
    """Default property to sort results of a query by."""

    _PAGE_SIZE = 100
    """Default number of results returned in each page fetch from the PDS API."""

    def __init__(self, client: PDSRegistryClient):
        """Constructor of the ResultSet."""
        self._products = AllProductsApi(client.api_client)
        self._latest_harvest_time = None
        self._page_counter = None
        self._expected_pages = None

    def init_new_page(self, query_string="", fields=None):
        """Queries the PDS API for the next page of results.

        Any query clauses associated to this Products instance are included here.

        If there are results remaining from the previously acquired page,
        they are yieled on each subsequent call to this method.

        Parameters
        ----------
        query_string : str, optional
            The query string to submit to the PDS API.
        fields : iterable, optional
            Additional fields to include with the query parameters.

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

        kwargs = {"sort": [self._SORT_PROPERTY], "limit": self._PAGE_SIZE}

        if self._latest_harvest_time is not None:
            kwargs["search_after"] = [self._latest_harvest_time]

        if len(query_string) > 0:
            kwargs["q"] = f"({query_string})"

        if fields and len(fields) > 0:
            # The sort property is used for pagination
            if self._SORT_PROPERTY not in fields:
                fields.append(self._SORT_PROPERTY)

            kwargs["fields"] = fields

        results = self._products.product_list(**kwargs)

        # If this is the first page fetch, calculate total number of expected pages
        # based on hit count
        if self._expected_pages is None:
            hits = results.summary.hits

            self._expected_pages = hits // self._PAGE_SIZE
            if hits % self._PAGE_SIZE:
                self._expected_pages += 1

            self._page_counter = 0

        for product in results.data:
            yield product
            self._latest_harvest_time = product.properties[self._SORT_PROPERTY][0]

        # If here, current page has been exhausted
        self._page_counter += 1

    def reset(self):
        """Resets internal pagination state to default."""
        self._expected_pages = None
        self._page_counter = None
        self._latest_harvest_time = None

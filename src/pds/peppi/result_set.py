"""Module of the ResultSet."""
import logging
from typing import Optional

import pandas as pd
from pds.api_client.api.all_products_api import AllProductsApi

from .client import PDSRegistryClient
from .query_builder import QueryBuilder

logger = logging.getLogger(__name__)


class ResultSet(QueryBuilder):
    """ResultSet of products on which a query has been applied. Iterable."""

    _SORT_PROPERTY = "ops:Harvest_Info.ops:harvest_date_time"
    """Default property to sort results of a query by."""

    _PAGE_SIZE = 100
    """Default number of results returned in each page fetch from the PDS API."""

    def __init__(self, client: PDSRegistryClient):
        """Constructor of the ResultSet."""
        super().__init__()
        self._products = AllProductsApi(client.api_client)
        self._latest_harvest_time = None
        self._page_counter = None
        self._expected_pages = None

    def __str__(self):
        """Returns a string representation of the ResultSet, including the current query string."""
        return f"Current {self.__class__.__name__} query:\n{super().__str__()}"

    def _init_new_page(self):
        """Queries the PDS API for the next page of results.

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

        kwargs = {"sort": [self._SORT_PROPERTY], "limit": self._PAGE_SIZE}

        if self._latest_harvest_time is not None:
            kwargs["search_after"] = [self._latest_harvest_time]

        if len(self._q_string) > 0:
            kwargs["q"] = f"({self._q_string})"

        if len(self._fields) > 0:
            # The sort property is used for pagination
            if self._SORT_PROPERTY not in self._fields:
                self._fields.append(self._SORT_PROPERTY)

            kwargs["fields"] = self._fields

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
        self._expected_pages = None
        self._page_counter = None
        self._latest_harvest_time = None

    def as_dataframe(self, max_rows: Optional[int] = None):
        """Returns the found products as a pandas DataFrame.

        Loops on the products found and returns a pandas DataFrame with the product properties as columns
        and their identifier as index.

        Parameters
        ----------
        max_rows : int
            Optional limit in the number of products returned in the dataframe. Convenient for test while developing.
            Default is no limit (None)

        Returns
        -------
        The products as a pandas dataframe.
        """
        result_as_dict_list = []
        lidvid_index = []
        n = 0
        for p in self:
            result_as_dict_list.append(p.properties)
            lidvid_index.append(p.id)
            n += 1
            if max_rows and n >= max_rows:
                break
        self.reset()

        if n > 0:
            df = pd.DataFrame.from_records(result_as_dict_list, index=lidvid_index)
            # reduce useless arrays in dataframe columns
            for column in df.columns:
                only_1_element = df.apply(lambda x: len(x[column]) <= 1, axis=1)  # noqa
                if only_1_element.all():
                    df[column] = df.apply(lambda x: x[column][0], axis=1)  # noqa
            return df
        else:
            logger.warning("Query with clause %s did not return any products.", self._q_string)  # noqa
            return None

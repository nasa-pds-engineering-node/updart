"""Module for the QueryBuilder.

Contains all the methods use to elaborate the PDS4 Information Model queries through the PDS Search API.
"""
import logging
from datetime import datetime
from functools import cache
from typing import Literal
from typing import Optional
from typing import Union

import pandas as pd

from .client import PDSRegistryClient
from .result_set import ResultSet

logger = logging.getLogger(__name__)

PROCESSING_LEVELS = Literal["telemetry", "raw", "partially-processed", "calibrated", "derived"]
"""Processing level values that can be used with has_processing_level()"""


class QueryBuilder:
    """QueryBuilder provides method to elaborate complex PDS queries."""

    def __init__(self, client: PDSRegistryClient):
        """Creates a new instance of the QueryBuilder class."""
        self._client = client
        self._q_string = ""
        self._fields: list[str] = []
        self._result_set = ResultSet(self._client)

    def __str__(self):
        """Returns a formatted string representation of the current query."""
        return "\n  and".join(self._q_string.split("and"))

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
                for product in self._result_set.init_new_page(query_string=self._q_string, fields=self._fields):
                    yield product
            except RuntimeError as err:
                # Make sure we got the StopIteration that was converted to a RuntimeError,
                # otherwise we need to re-raise
                if "StopIteration" not in str(err):
                    raise err

                self._result_set.reset()
                break

    def _add_clause(self, clause, logical_join="and"):
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
        logical_join : str, optional
            The logical operator to use to join the new clause with any existing
            clauses. Must be one of "and" or "or" (case-insensitive). This
            argument has no effect if this is the first clause to be added.
            Defaults to "and".

        Raises
        ------
        RuntimeError
            If this method is called while there are still results to be iterated
            over from a previous query.

        """
        # TODO transition off usage of this function to build a query string
        #      in response to each user method call.
        #      rather, have each user call track state about what was requested,
        #      and then only assemble the final query string when __iter__ is called.
        #      this should allow us flexibility to assemble individual sub-clauses
        #      with logical OR, then join all sub-clauses together with logical AND.
        if logical_join.lower() not in ("and", "or"):
            raise ValueError(f'Invalid logical join operator "{logical_join}", must be either "and" or "or".')

        # TODO have something more agnostic of what the iterator is
        #      since the iterator is not managed by this present object
        if hasattr(self._result_set, "_page_counter") and self._result_set._page_counter:
            raise RuntimeError(
                "Cannot modify query while paginating over previous query results.\n"
                "Use the reset() method on this Products instance or exhaust all returned "
                "results before assigning new query clauses."
            )

        clause = f"({clause})"

        if self._q_string:
            self._q_string += f" {logical_join.lower()} {clause}"
        else:
            self._q_string = clause

    def _has_target(self, identifiers: Union[list, str]):
        """Adds a query clause from 1 or n, target lids, apply OR operator between lids."""
        if isinstance(identifiers, str):
            identifiers = [identifiers]

        if len(identifiers) > 0:
            clause = "or ".join([f'ref_lid_target eq "{identifier}"' for identifier in identifiers])
            # add parenthesis to force the precendence on the 'or' operator
            clause = f"({clause})"
            self._add_clause(clause)
        else:
            logger.warning("No target filter defined, ignore")

        return self

    def has_target(self, target: str):
        """Adds a query clause selecting products having a given target as a lid or a keyword.

        Adds a query clause selecting products having a given target as a lid
        (for example `urn:nasa:pds:context:target:planet.mercury`) or a keyword, for example `Mercury`.

        Parameters
        ----------
        target : str
            Identifier (LID) of the target or a keyword matching the title of the target.
            The provided keyword is "cannonicalized" into several variations
            (uppercase, lowercase, etc.) to cast a wider search across target names.

        Returns
        -------
        This instance with the "has target" query filter applied.

        """
        if target.startswith("urn:"):
            logger.info('Finding products with target lid "%s"', target)
            lids = [target]
        else:

            @cache
            def _get_lids_from_title(k):
                return list({p.properties["lid"][0] for p in QueryBuilder(self._client).contexts(k)})

            logger.info('Finding products with target "%s"', target)
            lids = _get_lids_from_title(target)
            logger.info('Found %d product(s) matching target "%s", lids are: %s', len(lids), target, lids)

        return self._has_target(lids)

    def has_investigation(self, identifier: str):
        """Adds a query clause selecting products having a given investigation identifier.

        Parameters
        ----------
        identifier : str
            Identifier (LIDVID) of the target.

        Returns
        -------
        This instance with the "has investigation" query filter applied.

        """
        clause = f'ref_lid_investigation eq "{identifier}"'
        self._add_clause(clause)
        return self

    def before(self, dt: datetime):
        """Adds a query clause selecting products with a start date before the given datetime.

        Parameters
        ----------
        dt : datetime.datetime
            Datetime object containing the desired time.

        Returns
        -------
        This instance with the "before" filter applied.

        """
        iso8601_datetime = dt.isoformat().replace("+00:00", "Z")
        clause = f'pds:Time_Coordinates.pds:start_date_time le "{iso8601_datetime}"'
        self._add_clause(clause)
        return self

    def after(self, dt: datetime):
        """Adds a query clause selecting products with an end date after the given datetime.

        Parameters
        ----------
        dt : datetime.datetime
            Datetime object containing the desired time.

        Returns
        -------
        This instance with the "before" filter applied.

        """
        iso8601_datetime = dt.isoformat().replace("+00:00", "Z")
        clause = f'pds:Time_Coordinates.pds:stop_date_time ge "{iso8601_datetime}"'
        self._add_clause(clause)
        return self

    def of_collection(self, identifier: str):
        """Adds a query clause selecting products belonging to the given Parent Collection identifier.

        Parameters
        ----------
        identifier : str
            Identifier (LIDVID) of the Collection.

        Returns
        -------
        This instance with the "Parent Collection" filter applied.

        """
        clause = f'ops:Provenance.ops:parent_collection_identifier eq "{identifier}"'
        self._add_clause(clause)
        return self

    def observationals(self):
        """Adds a query clause selecting only "Product Observational" type products on the current filter.

        Returns
        -------
        This instance with the "Observational Product" filter applied.

        """
        clause = 'product_class eq "Product_Observational"'
        self._add_clause(clause)
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
        This instance with the "Product Collection" filter applied.

        """
        clause = 'product_class eq "Product_Collection"'
        self._add_clause(clause)

        if collection_type:
            clause = f'pds:Collection.pds:collection_type eq "{collection_type}"'
            self._add_clause(clause)

        return self

    def bundles(self):
        """Adds a query clause selecting only "Bundle" type products on the current filter.

        Returns
        -------
        This instance with the "Product Bundle" filter applied.

        """
        clause = 'product_class eq "Product_Bundle"'
        self._add_clause(clause)
        return self

    def contexts(self, keyword: str = None):
        """Adds a query clause selecting only "Context" type products (targets, investigations, instruments, etc...).

        Parameters
        ----------
        keyword : str, optional
            Title of the context products. Automatically search for "cannonicalized" variations
            (uppercase, lowercase, etc.) to cast a wider search across target names.

        Returns
        -------
        This instance with the "Product Context" filter applied.

        """
        clause = 'product_class eq "Product_Context"'
        self._add_clause(clause)

        if keyword:

            def _canonicalize_string(string: str):
                return string.title(), string.upper(), string.lower()

            def eq_cannonical_string_clause(property_name: str, value: str):
                return " or ".join(f'{property_name} eq "{s}"' for s in _canonicalize_string(value))

            q_string = eq_cannonical_string_clause("pds:Identification_Area.pds:title", keyword)
            q_string += f" or {eq_cannonical_string_clause('pds:Alias.pds:alternate_title', keyword)}"

            # add parenthesis to enforce the expected precedence on the or operator.
            q_string = f"({q_string})"

            self._add_clause(q_string)

        return self

    def has_instrument(self, identifier: str):
        """Adds a query clause selecting products having an instrument matching the provided identifier.

        Parameters
        ----------
        identifier : str
            Identifier (LIDVID) of the instrument.

        Returns
        -------
        This instance with the "has instrument" filter applied.

        """
        clause = f'ref_lid_instrument eq "{identifier}"'
        self._add_clause(clause)
        return self

    def has_instrument_host(self, identifier: str):
        """Adds a query clause selecting products having an instrument host matching the provided identifier.

        Parameters
        ----------
        identifier : str
            Identifier (LIDVID) of the instrument host.

        Returns
        -------
        This instance with the "has instrument host" filter applied.

        """
        clause = f'ref_lid_instrument_host eq "{identifier}"'
        self._add_clause(clause)
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
        This instance with the "has processing level" filter applied.

        """
        clause = f'pds:Primary_Result_Summary.pds:processing_level eq "{processing_level.title()}"'
        self._add_clause(clause)
        return self

    def within_range(self, range_in_km: float):
        """Adds a query clause selecting products within the provided range value.

        Notes
        -----
        This method should be implemented by product-specific inheritors that
        support the notion of range to a given target.

        Parameters
        ----------
        range_in_km : float
            The range in kilometers to use with the query.

        Raises
        ------
        NotImplementedError

        """
        raise NotImplementedError("within_range is not available for base QueryBuilder")

    def within_bbox(self, lat_min: float, lat_max: float, lon_min: float, lon_max: float):
        """Adds a query clause selecting products which fall within the bounds of the provided bounding box.

        Notes
        -----
        This method should be implemented by product-specific inheritors that
        support the notion of bounding box to filter results by.

        Parameters
        ----------
        lat_min : float
            Minimum latitude boundary.
        lat_max : float
            Maximum latitude boundary.
        lon_min : float
            Minimum longitude boundary.
        lon_max : float
            Maximum longitude boundary.

        Raises
        ------
        NotImplementedError

        """
        raise NotImplementedError("within_bbox is not available for base QueryBuilder")

    def get(self, identifier: str):
        """Adds a query clause selecting the product with a LIDVID matching the provided value.

        Parameters
        ----------
        identifier : str
            LIDVID of the product to filter for.

        Returns
        -------
        This instance with the "LIDVID identifier" filter applied.

        """
        # Note: use of "like" is currently broken in the API when combined with other clauses
        self._add_clause(f'lidvid eq "{identifier}"', logical_join="or")
        return self

    def fields(self, fields: list):
        """Reduce the list of fields returned, for improved efficiency."""
        self._fields = fields
        return self

    def filter(self, clause: str):
        """Selects products that match the provided query clause.

        Parameters
        ----------
        clause : str
            A query clause using the
            `PDS API query syntax <https://nasa-pds.github.io/pds-api/guides/search/endpoints.html#query-string-syntax>`_

        Returns
        -------
        This instance with the provided filtering clause applied.
        """
        self._add_clause(clause)
        return self

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

    def reset(self):
        """Resets internal pagination state to default.

        This method should be called before making any modifications to the
        query clause stored by this QueryBuilder instance while still paginating
        through the results of a previous query.

        """
        self._result_set.reset()
        self._q_string = ""

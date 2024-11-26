"""Module for the QueryBuilder.

Contains all the methods use to elaborate the PDS4 Information Model queries through the PDS Search API.
"""
import logging
from datetime import datetime
from typing import Literal
from typing import Optional

logger = logging.getLogger(__name__)


PROCESSING_LEVELS = Literal["telemetry", "raw", "partially-processed", "calibrated", "derived"]
"""Processing level values that can be used with has_processing_level()"""


class QueryBuilder:
    """QueryBuilder provides method to elaborate complex PDS queries."""

    def __init__(self):
        """Creates a new instance of the QueryBuilder class.

        Parameters
        ----------
        client: PDSRegistryClient
            The client object used to interact with the PDS Registry API.

        """
        self._q_string = ""
        self._fields: list[str] = []

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
        # TODO have something more agnostic of what the iterator is
        # since the iterator is not managed by this present object
        if hasattr(self, "_page_counter") and self._page_counter:
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

    def fields(self, fields: list):
        """Reduce the list of fields returned, for improved efficiency."""
        self._fields = fields
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

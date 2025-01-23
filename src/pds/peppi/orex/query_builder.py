"""Module containing the Osiris Rex (OREX) tailored QueryBuilder class."""
from pds.peppi.client import PDSRegistryClient
from pds.peppi.query_builder import QueryBuilder


class OrexQueryBuilder(QueryBuilder):
    """Inherits the functionality of the QueryBuilder class, but adds implementations for unimplemented stubs."""

    orex_investigation_lidvid = "urn:nasa:pds:context:investigation:mission.orex"

    def __init__(self, client: PDSRegistryClient):
        """Creates a new instance of OrexResultSet.

        Parameters
        ----------
        client : PDSRegistryClient
            Client defining the connection with the PDS Search API.

        """
        super().__init__(client)

        # By default, all query results are filtered to just those applicable to
        # the Osiris Rex investigation
        self._q_string = f'ref_lid_investigation eq "{self.orex_investigation_lidvid}"'

    def has_investigation(self, identifier: str):
        """Adds a query clause selecting products having an instrument matching the provided identifier.

        Notes
        -----
        For OrexResultsSet, this method is not impemented since the instrument
        is implicitly always fixed to Osiris Rex.

        Parameters
        ----------
        identifier : str
            Identifier (LIDVID) of the instrument.

        Raises
        ------
        NotImplementedError

        """
        raise NotImplementedError(f"Cannot specify an additional investigation on {self.__class__.__name__}")

    def within_range(self, range_in_km: float):
        """Adds a query clause selecting products within the provided range value.

        Parameters
        ----------
        range_in_km : float
            The range in kilometers to use with the query.

        Returns
        -------
        This OrexResultSet instance with the "within range" filter applied.

        """
        self._add_clause(f"orex:Spatial.orex:target_range le {range_in_km}")

        return self

    def within_bbox(self, lat_min: float, lat_max: float, lon_min: float, lon_max: float):
        """Adds a query clause selecting products which fall within the bounds of the provided bounding box.

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

        Returns
        -------
        This OrexResultSet instance with the "within bounding box" filter applied.

        """
        self._add_clause(f"orex:Spatial.orex:latitude ge {lat_min}")
        self._add_clause(f"orex:Spatial.orex:latitude le {lat_max}")
        self._add_clause(f"orex:Spatial.orex:longitude ge {lon_min}")
        self._add_clause(f"orex:Spatial.orex:longitude le {lon_max}")

        return self

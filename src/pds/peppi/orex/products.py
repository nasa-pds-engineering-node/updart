"""Main class of the Osiris Rex (OREX) Peppi package."""
from pds.peppi.client import PDSRegistryClient
from pds.peppi.orex.query_builder import OrexQueryBuilder


class OrexProducts(OrexQueryBuilder):
    """Specialized Products class used to query specfically for Osiris Rex (OREX) products."""

    def __init__(self, client: PDSRegistryClient):
        """Creates a new instance of OrexProducts.

        Parameters
        ----------
        client : PDSRegistryClient
            Client defining the connection with the PDS Search API.

        """
        super().__init__(client)

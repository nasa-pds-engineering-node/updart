"""Main class of the library in this module."""
from .client import PDSRegistryClient
from .result_set import ResultSet


class Products(ResultSet):
    """Use to access any class of planetary products via the PDS Registry API."""

    def __init__(self, client: PDSRegistryClient):
        """Constructor of the products.

        Attributes
        ----------
        client : PDSRegistryClient
            Client defining the connexion with the PDS Search API
        """
        ResultSet.__init__(self, client)

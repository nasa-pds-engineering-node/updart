"""Main class of the library in this module."""
from .client import PDSRegistryClient
from .query_builder import QueryBuilder


class Products(QueryBuilder):
    """Use to access any class of planetary products via the PDS Registry API.

    This class is an inheritor of :class:`.query_builder.QueryBuilder`, which
    carries methods to subset the products, and which can be iterated on or
    converted to a pandas DataFrame.
    """

    def __init__(self, client: PDSRegistryClient):
        """Constructor of the products.

        Attributes
        ----------
        client : PDSRegistryClient
            Client defining the connexion with the PDS Search API
        """
        super().__init__(client)

"""Main class of the library in this module."""
from .client import PDSRegistryClient
from .result_set import ResultSet


class Products(ResultSet):
    """Use to access any class of planetary products via the PDS Registry API.

    This class is both a :class:`.query_builder.QueryBuilder` which carries methods to subset the products
    and a :class:`.result_set.ResultSet` which can be iterated on or converted to for example a pandas DataFrame
    """

    def __init__(self, client: PDSRegistryClient):
        """Constructor of the products.

        Attributes
        ----------
        client : PDSRegistryClient
            Client defining the connexion with the PDS Search API
        """
        ResultSet.__init__(self, client)

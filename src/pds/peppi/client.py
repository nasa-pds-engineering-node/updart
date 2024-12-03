"""PDS Registry Client related classes."""
import logging

from pds.api_client import ApiClient
from pds.api_client import Configuration


logger = logging.getLogger(__name__)

_DEFAULT_API_BASE_URL = "https://pds.nasa.gov/api/search/1"
"""Default URL used when querying PDS API"""


class PDSRegistryClient:
    """Used to connect and interface with the PDS Registry.

    Attributes
    ----------
    api_client : pds.api_client.ApiClient
        Object used to interact with the PDS Registry API

    """

    def __init__(self, base_url=_DEFAULT_API_BASE_URL):
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

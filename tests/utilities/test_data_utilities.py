import threading

from fbnsdkutilities import ApiClientBuilder

from tests.utilities import CredentialsSource
import tests.sdk.petstore as petstore


class TestDataUtilities:

    _api_client = None
    _lock = threading.Lock()

    @classmethod
    def api_client(cls):
        if not cls._api_client:
            with cls._lock:
                if not cls._api_client:
                    cls._api_client = ApiClientBuilder().build(petstore, CredentialsSource.secrets_path())
        return cls._api_client

import unittest
from collections import UserString
from datetime import datetime
from unittest.mock import patch
from parameterized import parameterized
from threading import Thread

from lusid import InstrumentsApi, ResourceListOfInstrumentIdTypeDescriptor
from fbnsdkutilities import ApiClientFactoryBase

from tests.sdk.petstore.api import StoreApi
from tests.utilities import TokenUtilities as tu, CredentialsSource
from tests.utilities.temp_file_manager import TempFileManager
from tests.utilities import MockApiResponse
import tests.sdk.petstore as petstore

class UnknownApi:
    pass


class UnknownImpl:
    pass


source_config_details, config_keys = CredentialsSource.fetch_credentials(), CredentialsSource.fetch_config_keys()


class RefreshingToken(UserString):

    def __init__(self):
        token_data = {"expires": datetime.now(), "current_access_token": ""}

        def get_token():
            token_data["current_access_token"] = None
            return token_data["current_access_token"]

        self.access_token = get_token

    def __getattribute__(self, name):
        token = object.__getattribute__(self, "access_token")()
        if name == "data":
            return token
        return token.__getattribute__(name)


class ApiFactory(unittest.TestCase):
    def validate_api(self, api):
        result = api.get_investory()
        self.assertIsNotNone(result)
        self.assertIsInstance(result, ResourceListOfInstrumentIdTypeDescriptor)
        self.assertGreater(len(result.values), 0)

    @parameterized.expand([
        ["Unknown API", UnknownApi, "unknown api: UnknownApi"],
        ["Unknown Implementation", UnknownImpl, "unknown api: UnknownImpl"]
    ])
    def test_get_unknown_api_throws_exception(self, _, api_to_build, error_message):
        factory = ApiClientFactoryBase(
            petstore,
            api_secrets_filename=CredentialsSource.secrets_path()
        )

        with self.assertRaises(TypeError) as error:
            factory.build(api_to_build)
        self.assertEqual(error.exception.args[0], error_message)

    def test_get_api_with_token(self):
        token, refresh_token = tu.get_okta_tokens(CredentialsSource.secrets_path())
        factory = ApiClientFactoryBase(
            petstore,
            token=token,
            api_url=source_config_details["api_url"],
            app_name=source_config_details["app_name"]
        )
        api = factory.build(StoreApi)
        self.assertIsInstance(api, StoreApi)
        #self.validate_api(api)

    def test_get_api_with_none_token(self):
        factory = ApiClientFactoryBase(
            petstore,
            token=None,
            api_url=source_config_details["api_url"],
            app_name=source_config_details["app_name"],
            api_secrets_filename=CredentialsSource.secrets_path(),
        )
        api = factory.build(StoreApi)
        self.assertIsInstance(api, StoreApi)
        #self.validate_api(api)

    def test_get_api_with_str_none_token(self):
        factory = ApiClientFactoryBase(
            petstore,
            token=RefreshingToken(),
            api_url=source_config_details["api_url"],
            app_name=source_config_details["app_name"],
            api_secrets_filename=CredentialsSource.secrets_path(),
        )
        api = factory.build(StoreApi)
        self.assertIsInstance(api, StoreApi)
        #self.validate_api(api)

    def test_get_api_with_token_url_as_env_var(self):
        token, refresh_token = tu.get_okta_tokens(CredentialsSource.secrets_path())
        with patch.dict('os.environ', {"FBN_LUSID_API_URL": source_config_details["api_url"]}, clear=True):
            factory = ApiClientFactoryBase(
                petstore,
                token=token,
                app_name=source_config_details["app_name"])
        api = factory.build(StoreApi)
        self.assertIsInstance(api, StoreApi)
        #self.validate_api(api)

    def test_get_api_with_configuration(self):
        factory = ApiClientFactoryBase(
            petstore,
            api_secrets_filename=CredentialsSource.secrets_path()
        )
        api = factory.build(StoreApi)
        self.assertIsInstance(api, StoreApi)
       # self.validate_api(api)

    def test_get_api_with_info(self):
        factory = ApiClientFactoryBase(
            petstore,
            api_secrets_filename=CredentialsSource.secrets_path()
        )
        api = factory.build(StoreApi)

        self.assertIsInstance(api, StoreApi)
        #result = api.get_instrument_identifier_types(call_info=lambda r: print(r))

        #self.assertIsNotNone(result)

    def test_get_info_with_invalid_param_throws_error(self):
        factory = ApiClientFactoryBase(
            petstore,
            api_secrets_filename=CredentialsSource.secrets_path()
        )
        api = factory.build(StoreApi)
        self.assertIsInstance(api, StoreApi)

        #with self.assertRaises(ValueError) as error:
        #    api.get_instrument_identifier_types(call_info="invalid param")

        #self.assertEqual(error.exception.args[0], "call_info value must be a lambda")

    def test_wrapped_method(self):
        factory = ApiClientFactoryBase(
            petstore,
            api_secrets_filename=CredentialsSource.secrets_path()
        )

        wrapped_store_api = factory.build(StoreApi)
        store_api = StoreApi(wrapped_store_api.api_client)

        self.assertEqual(store_api.__doc__, wrapped_store_api.__doc__)
        self.assertEqual(store_api.__module__, wrapped_store_api.__module__)
        self.assertDictEqual(store_api.__dict__, wrapped_store_api.__dict__)

    def test_get_api_with_proxy_file(self):

        secrets = {
            "api": {
                config_keys[key]["config"]: value for key, value in source_config_details.items() if
                value is not None and "proxy" not in key
            },
            "proxy": {
                config_keys[key]["config"]: value for key, value in source_config_details.items() if
                value is not None and "proxy" in key
            }
        }

        secrets["api"].pop("clientCertificate", None)

        if secrets["proxy"].get("address", None) is None:
            self.skipTest(f"missing proxy configuration")

        secrets_file = TempFileManager.create_temp_file(secrets)
        # Load the config
        factory = ApiClientFactoryBase(
            petstore, api_secrets_filename=secrets_file.name)
        # Close and thus delete the temporary file
        TempFileManager.delete_temp_file(secrets_file)
        api = factory.build(StoreApi)
        #self.validate_api(api)

    def test_get_api_with_proxy_config(self):

        secrets = {
            "api": {
                config_keys[key]["config"]: value for key, value in source_config_details.items() if
                value is not None and "proxy" not in key
            }
        }

        secrets["api"].pop("clientCertificate", None)

        if source_config_details.get("proxy_address", None) is None:
            self.skipTest(f"missing proxy configuration")

        secrets_file = TempFileManager.create_temp_file(secrets)
        # Load the config
        with patch.dict('os.environ', {}, clear=True):
            factory = ApiClientFactoryBase(
                petstore,
                api_secrets_filename=secrets_file.name,
                proxy_url=source_config_details["proxy_address"],
                proxy_username=source_config_details["proxy_username"],
                proxy_password=source_config_details["proxy_password"])

        # Close and thus delete the temporary file
        TempFileManager.delete_temp_file(secrets_file)
        api = factory.build(StoreApi)
        #self.validate_api(api)

    def test_get_api_with_correlation_id_from_env_var(self):

        env_vars = {config_keys[key]["env"]: value for key, value in source_config_details.items() if value is not None}
        env_vars["FBN_CORRELATION_ID"] = "env-correlation-id"

        with patch.dict('os.environ', env_vars, clear=True):
            factory = ApiClientFactoryBase(petstore)
            api = factory.build(StoreApi)
            self.assertIsInstance(api, StoreApi)
            #self.validate_api(api)
            #self.assertTrue("CorrelationId" in api.api_client.default_headers, msg="CorrelationId not found in headers")
            #self.assertEquals(api.api_client.default_headers["CorrelationId"], "env-correlation-id")

    def test_get_api_with_correlation_id_from_param(self):

        env_vars = {config_keys[key]["env"]: value for key, value in source_config_details.items() if value is not None}

        with patch.dict('os.environ', env_vars, clear=True):
            factory = ApiClientFactoryBase(
                petstore,
                api_secrets_filename=CredentialsSource.secrets_path(),
                correlation_id="param-correlation-id"
            )
            api = factory.build(StoreApi)
            self.assertIsInstance(api, StoreApi)
            #self.validate_api(api)
            #self.assertTrue("CorrelationId" in api.api_client.default_headers, msg="CorrelationId not found in headers")
            #self.assertEquals(api.api_client.default_headers["CorrelationId"], "param-correlation-id")

    def test_use_apifactory_with_id_provider_response_handler(self):
        """
        Ensures that an id_provider_response handler that is passed to the ApiClientFactory can be used during
        communication with the id provider (if appropriate).
        """
        responses = []

        def record_response(id_provider_response):
            nonlocal responses
            responses.append(id_provider_response.status_code)

        api_factory = ApiClientFactoryBase(
            petstore,
            api_secrets_filename=CredentialsSource.secrets_path(),
            id_provider_response_handler=record_response
        )

        api = api_factory.build(StoreApi)
        test = f"{api.api_client.configuration.access_token}"

        self.assertGreater(len(responses), 0)

    def test_use_apifactory_multiple_threads(self):

        access_token = str(ApiClientFactoryBase(
            petstore,
            api_secrets_filename=CredentialsSource.secrets_path()
        ).api_client.configuration.access_token)

        api_factory = ApiClientFactoryBase(
            petstore,
            api_secrets_filename=CredentialsSource.secrets_path()
        )

        def get_identifier_types(factory):
            return f"{factory.build(StoreApi).api_client.configuration.access_token}"
            #return factory.build(StoreApi).get_inventory()

        thread1 = Thread(target=get_identifier_types, args=[api_factory])
        thread2 = Thread(target=get_identifier_types, args=[api_factory])
        thread3 = Thread(target=get_identifier_types, args=[api_factory])

        with patch("requests.post") as identity_mock:
            identity_mock.side_effect = lambda *args, **kwargs: MockApiResponse(
                json_data={
                    "access_token": f"{access_token}",
                    "refresh_token": "mock_refresh_token",
                    "expires_in": 3600
                },
                status_code=200
            )

            thread1.start()
            thread2.start()
            thread3.start()

            thread1.join()
            thread2.join()
            thread3.join()

            # Ensure that we only got an access token once
            self.assertEqual(1, identity_mock.call_count)

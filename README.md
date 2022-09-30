# FINBOURNE<sup>®</sup> SDK Utilities

![LUSID_by_Finbourne](https://content.finbourne.com/FINBOURNE_repo.png)

[![Daily build](https://github.com/finbourne/sdk-utilities-python/actions/workflows/cron.yaml/badge.svg)](https://github.com/finbourne/sdk-utilities-python/actions/workflows/cron.yaml) [![Build and test](https://github.com/finbourne/sdk-utilities-python/actions/workflows/build-and-test.yaml/badge.svg)](https://github.com/finbourne/sdk-utilities-python/actions/workflows/build-and-test.yaml)

This package provides a set of utilities for use with the suite of FINBOURNE Python SDKs, this includes capabilities such as:
* authentication token acquisition
* refresh token
* request retries
* API construction

## Installation

The SDK utilities package is available on PyPi and can be installed using the following:

```
pip install finbourne-sdk-utilities
```

## SDK Configuration

The following configuration items are used by the utilities package to configure the SDK:

| Key | Description |
| --- | --- |
| `apiUrl` | The  API url |
| `tokenUrl` | Okta endpoint to generate the authentication token, this is the value for 'Token Url' in your portal |
| `clientId` | OpenID Connect Client ID, this is the value for 'Client Id' in your portal |
| `clientSecret` | OpenID Connect Client Secret, this is the value for 'Secret' in your portal |
| `username` | The username of the account being used for accessing the API |
| `password` | The password of the account being used for accessing the API |
| `applicationName` | An optional identifier for your application |

These configuration items must be exposed by an SDK via a `utilities` module containing a `ConfigKeys` class with `get()` classmethod that returns a dictionary of configuration keys/values.

```
mysdk/
|
...
├── utilities/
│   ├── __init__.py
│   └── ConfigKeys.py
...
```

An implementation of `ConfigKeys.py` may look like the example below where the keys are stored in a json file

```python
class ConfigKeys:

    config_key_path = 'config_keys.json'

    @classmethod
    def get(cls):
        with open(Path(__file__).parent.joinpath(cls.config_key_path)) as json_file:
            config_keys = json.load(json_file)

        return config_keys
```

The returned values are a dictionary of configuration keys, containing a dictionary of key-values for the environment variables and json configuration files e.g.

```json
{
    ...

    "token_url": {  
        "env": "FBN_TOKEN_URL",
        "config": "tokenUrl"
    },

    ...
}
```

## Usage

The SDK utilities can be used with FINBOURNE SDKs such as the [Luminesce Python SDK](https://github.com/finbourne/)

```python
import luminesce
from fbnsdkutilities import ApiClientFactory

factory = ApiClientFactory(luminesce)
sql_exec_api = factory.build(luminesce.api.SqlExecutionApi)

sql_exec_api.put_by_query_csv("""
    select * from lusid.portfolio limit 10
""")
```


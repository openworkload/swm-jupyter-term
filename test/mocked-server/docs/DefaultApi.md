# openapi_client.DefaultApi

All URIs are relative to *http://localhost*

Method | HTTP request | Description
------------- | ------------- | -------------
[**user_job_get**](DefaultApi.md#user_job_get) | **GET** /user/job | List all jobs
[**user_job_job_id_delete**](DefaultApi.md#user_job_job_id_delete) | **DELETE** /user/job/{jobId} | Cancels a job
[**user_job_job_id_get**](DefaultApi.md#user_job_job_id_get) | **GET** /user/job/{jobId} | Find job by ID
[**user_job_post**](DefaultApi.md#user_job_post) | **POST** /user/job | Submit a new job


# **user_job_get**
> [Job] user_job_get()

List all jobs

Returns list of job object

### Example

```python
import time
import openapi_client
from openapi_client.api import default_api
from openapi_client.model.job import Job
from pprint import pprint
# Defining the host is optional and defaults to http://localhost
# See configuration.py for a list of all supported configuration parameters.
configuration = openapi_client.Configuration(
    host = "http://localhost"
)


# Enter a context with an instance of the API client
with openapi_client.ApiClient() as api_client:
    # Create an instance of the API class
    api_instance = default_api.DefaultApi(api_client)

    # example, this endpoint has no required or optional parameters
    try:
        # List all jobs
        api_response = api_instance.user_job_get()
        pprint(api_response)
    except openapi_client.ApiException as e:
        print("Exception when calling DefaultApi->user_job_get: %s\n" % e)
```


### Parameters
This endpoint does not need any parameter.

### Return type

[**[Job]**](Job.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | successful operation |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **user_job_job_id_delete**
> user_job_job_id_delete(job_id)

Cancels a job

Cancels execution or pending of a job by job ID

### Example

```python
import time
import openapi_client
from openapi_client.api import default_api
from pprint import pprint
# Defining the host is optional and defaults to http://localhost
# See configuration.py for a list of all supported configuration parameters.
configuration = openapi_client.Configuration(
    host = "http://localhost"
)


# Enter a context with an instance of the API client
with openapi_client.ApiClient() as api_client:
    # Create an instance of the API class
    api_instance = default_api.DefaultApi(api_client)
    job_id = "jobId_example" # str | Job id to cancel
    api_key = "api_key_example" # str |  (optional)

    # example passing only required values which don't have defaults set
    try:
        # Cancels a job
        api_instance.user_job_job_id_delete(job_id)
    except openapi_client.ApiException as e:
        print("Exception when calling DefaultApi->user_job_job_id_delete: %s\n" % e)

    # example passing only required values which don't have defaults set
    # and optional values
    try:
        # Cancels a job
        api_instance.user_job_job_id_delete(job_id, api_key=api_key)
    except openapi_client.ApiException as e:
        print("Exception when calling DefaultApi->user_job_job_id_delete: %s\n" % e)
```


### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **job_id** | **str**| Job id to cancel |
 **api_key** | **str**|  | [optional]

### Return type

void (empty response body)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: Not defined


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
**400** | Invalid job ID |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **user_job_job_id_get**
> Job user_job_job_id_get(job_id)

Find job by ID

Returns a single job information

### Example

```python
import time
import openapi_client
from openapi_client.api import default_api
from openapi_client.model.job import Job
from pprint import pprint
# Defining the host is optional and defaults to http://localhost
# See configuration.py for a list of all supported configuration parameters.
configuration = openapi_client.Configuration(
    host = "http://localhost"
)


# Enter a context with an instance of the API client
with openapi_client.ApiClient() as api_client:
    # Create an instance of the API class
    api_instance = default_api.DefaultApi(api_client)
    job_id = "jobId_example" # str | ID of job to return

    # example passing only required values which don't have defaults set
    try:
        # Find job by ID
        api_response = api_instance.user_job_job_id_get(job_id)
        pprint(api_response)
    except openapi_client.ApiException as e:
        print("Exception when calling DefaultApi->user_job_job_id_get: %s\n" % e)
```


### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **job_id** | **str**| ID of job to return |

### Return type

[**Job**](Job.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | successful operation |  -  |
**400** | Invalid job ID supplied |  -  |
**404** | Job not found |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **user_job_post**
> JobToSubmit user_job_post()

Submit a new job

A new job is submitted with a specific job script

### Example

```python
import time
import openapi_client
from openapi_client.api import default_api
from openapi_client.model.job_to_submit import JobToSubmit
from pprint import pprint
# Defining the host is optional and defaults to http://localhost
# See configuration.py for a list of all supported configuration parameters.
configuration = openapi_client.Configuration(
    host = "http://localhost"
)


# Enter a context with an instance of the API client
with openapi_client.ApiClient() as api_client:
    # Create an instance of the API class
    api_instance = default_api.DefaultApi(api_client)

    # example, this endpoint has no required or optional parameters
    try:
        # Submit a new job
        api_response = api_instance.user_job_post()
        pprint(api_response)
    except openapi_client.ApiException as e:
        print("Exception when calling DefaultApi->user_job_post: %s\n" % e)
```


### Parameters
This endpoint does not need any parameter.

### Return type

[**JobToSubmit**](JobToSubmit.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | successful operation of job submission |  -  |
**405** | Invalid input |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)


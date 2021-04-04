#!/usr/bin/env python3

import time

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

import openapi_client
from pprint import pprint
from openapi_client.api import default_api
from openapi_client.model.job import Job


APP = FastAPI()

def main():
    configuration = openapi_client.Configuration(host = "http://container:8443")

    # Enter a context with an instance of the API client
    with openapi_client.ApiClient(configuration) as api_client:
        # Create an instance of the API class
        api_instance = default_api.DefaultApi(api_client)
        try:
            # List all jobs
            api_response = api_instance.user_job_get()
            pprint(api_response)
        except openapi_client.ApiException as e:
            print("Exception when calling DefaultApi->user_job_get: %s\n" % e)



if __name__ == "__main__":
    main()

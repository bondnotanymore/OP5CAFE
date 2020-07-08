## O P 5 C A F E

# OP5 Monitor API Automation Tests

Pytest based framework to perform functional end-to-end testing of OP5 backend APIs.

Automated tests for [OP5](https://github.com/bondnotanymore/OP5CAFE),

## Initial Setup

You should use a virtualenv. There are plenty of resources out there that describe them.

1. Create a virtual env using python-3.6 --> `virtualenv -p python3 op5_pytest`
2. Activate the virtual env --> `source {path/to/spark_pytest}/bin/activate`
3. Install all the dependencies --> `pip install -r requirements.txt`
4. Set the environment against which you want to run your tests:

   (i)Run --> `export ENV_FOR_DYNACONF=development` if you want to run tests using the development section config 
   settings, which points to a dev env(or local) setup of OP5 monitor server.
   
   (ii)Run --> `export ENV_FOR_DYNACONF=staging` if you want to run tests using the staging section config settings,
   which points to a staging env setup of OP5 monitor server
   
   (iii)Run --> `export ENV_FOR_DYNACONF=production` if you want to run tests using the production section config 
   settings, which points to a production env setup of OP5 monitor server
   
(Go to `settings.toml` to understand the different section/environment-scope configs)

## Running Tests

Before running the tests, navigate to the OP5-pytest directory:

`cd OP5-pytest`

Run all tests with: `pytest`, but not a good idea though

You can also run tests based on markers for eg:

To run end to end tests
`pytest -m e2e`

To run host config tests
`pytest -m 'host and config'`

To run service config tests
`pytest -m 'service and config'`
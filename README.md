## O P 5 C A F E

# OP5 Monitor API Automation Tests

Pytest based framework to perform functional end-to-end testing of OP5 backend APIs.

Automated tests for [SPARK](https://github.rackspace.com/kapi3776/Spark_pytest),

## Initial Setup

You should use a virtualenv. There are plenty of resources out there that describe them.

1. Create a virtual env using python-3.6 --> `virtualenv -p python3 op5_pytest`
2. Activate the virtual env --> `source {path/to/spark_pytest}/bin/activate`
3. Install all the dependencies --> `pip install -r requirements.txt`
4. Set the environment against which you want to run your tests:

    (i) Run --> `export ENV_FOR_DYNACONF=default` if you want to run using the default section config settings which 
    points to old production or spark oh three.

   (ii)Run --> `export ENV_FOR_DYNACONF=development` if you want to run tests using the development section config 
   settings, which points to the development-spark env.
   
   (iii)Run --> `export ENV_FOR_DYNACONF=staging` if you want to run tests using the staging section config settings,
   which points to the staging-spark env.
   
   (iv)Run --> `export ENV_FOR_DYNACONF=production` if you want to run tests using the production section config 
   settings, which points to the production-spark env.
   
(Go to `settings.toml` to understand the different section/environment-scope configs)

## Running Tests

Before running the tests, navigate to the OP5-pytest directory:

`cd OP5-pytest`

Run all tests with: `pytest`, but not a good idea though

Below are the different ways to run product specific tests:

## Directory Layout
```
|                    __ User
|                   |__ Account
|____ Identity_Api__|__ Project
|                   |__ tests
|
|____ Common->|____ Clients
|             |
|             |___ Fixtures -->  Conftests_<product>.py
|             |
|             |___ Data_models_______ Constants
|                               |
|                               |____ tools
|_____ Tests
|
|_____ Conftest.py (Session level fixtures/ Plugins(product level conftests.py)
|
|_____ Settings.toml
|
|_____ Pytest.ini
|
|_____ Coverage (Coverage report)
|
|_____ Reports (HTML reports via allure

```

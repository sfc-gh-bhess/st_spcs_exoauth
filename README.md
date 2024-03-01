# Example Streamlit in Snowpark Conatiner Services
This is a simple Streamlit that can be deployed in 
Snowpark Container Services. It queries the TPC-H 100 
data set and returns the top sales clerks. The Streamlit
provides date pickers to restrict the range of the sales
data and a slider to determine how many top clerks to display.
The data is presented in a table sorted by highest seller
to lowest.

# Setup
This example requires importing the `SNOWFLAKE_SAMPLE_DATA`
data share, and an account with Snowpark Container Services
enabled.

1. Follow the "Common Setup" [here](https://docs.snowflake.com/en/LIMITEDACCESS/snowpark-containers/tutorials/common-setup)
2. In a SQL Worksheet, execute `SHOW IMAGE REPOSITORIES` and look
   for the entry for `TUTORIAL_DB.DATA_SCHEMA.TUTORIAL_REPOSITORY`.
   Note the value for `repository_url`.
3. In the main directory of this repo, execute 
   `./configure.sh`. Enter the URL of the repository that you
   noted in step 2 for the repository. Enter the name of the warehouse
   you set up in step 1 (if you followed the directions, it would be
   `tutorial_warehouse`).
4. Log into the Docker repository, build the Docker image, and push
   the image to the repository by running `make all`
   1. You can also run the steps individually. Log into the Docker 
      repository by running `make login` and entering your credentials.
   2. Make the Docker image by running `make build`.
   3. Push the image to the repository by running `make push_docker`
5. You will need to create a SAML integration with your Identity Provider
   (e.g., Okta) that will allow your user to log in via the Identity Provider.
   In Snowflake we need to create a SAML2 integration. See [here](https://docs.snowflake.com/en/user-guide/admin-security-fed-auth-security-integration)
   for instructions. See the documentation for your own Identity Provider
   for their instructions.
6. You will also need to create an application in your Identity Provider 
   that will allow the Streamlit to use a client credential flow to authenticate
   the visiting user. Then you will need to create an External OAuth integration
   in Snowflake so that the token returned from the Identity Provider can be
   used to create a Snowflake session as the visiting user. See [here](https://docs.snowflake.com/en/user-guide/oauth-ext-overview) 
   for instructions. See the documentation for your own Identity Provider for their
   instructions.
7. In order for the Streamlit to connect to Snowflake as the visiting user,
   we need an EXTERNAL ACCESS INTEGRATION to allow connecting to the public 
   URL for the Snowflake account, as well as allowing the Streamlit to reach
   out to the OAuth server.
   1. First, gather the list of hostnames for your account by running the
      the following in your Snowflake account:
      ```
      SELECT LISTAGG(DISTINCT '''' || split_part(h.value:host, '"', 1) || ':' || p.port || '''', ',\n') AS value_list 
      FROM TABLE(FLATTEN(input=>parse_json(SYSTEM$ALLOWLIST()))) AS h 
      CROSS JOIN (SELECT '80' AS port UNION ALL SELECT '443' AS port) AS p;
      ```
   2. Create a NETWORK RULE for this list of hostnames:
      ```
      CREATE OR REPLACE NETWORK RULE nr_local_snowflake
        MODE = EGRESS
        TYPE = HOST_PORT
        VALUE_LIST = (
        <paste in the value_list from previous step>
        );
      ```
   3. Create a NETWORK RULE for your OAuth server. For example, if youre
      OAuth server was `XYZ.oktapreview.com` you would execute:
      ```
      CREATE OR REPLACE NETWORK RULE nr_oauth
        MODE = EGRESS
        TYPE = HOST_PORT
        VALUE_LIST = ( 'XYZ.oktapreview.com' )
      ;
      ```
   4. Create an EXTERNAL ACCESS INTEGRATION for these 2 NETWORK RULES:
      ```
      CREATE OR REPLACE EXTERNAL ACCESS INTEGRATION eai_snowauthex
        ALLOWED_NETWORK_RULES = ( nr_local_snowflake, nr_oauth )
        ENABLED = true;
      ```
8. You need to create a TOML file for configuring the OAuth flow. Copy the
   `secrets.toml.template` to `secrets.toml` and fill in the various fields
   per the set up of the OAuth for your application. To aid in this, you can
   also run the `./configure_secrets.sh` script, which will guide you.
9. Create a Snowflake SECRET with the TOML details by executing `make secret`
   and running the resulting DDL.
10. Create the service by executing the DDL. You can get this DDL
   by running `make ddl`:
   ```
   CREATE SERVICE st_spcs
   IN COMPUTE POOL  tutorial_compute_pool
   FROM SPECIFICATION $$
   spec:
   containers:
      - name: streamlit
         image: sfsenorthamerica-bmh-prod3.registry.snowflakecomputing.com/sandbox/idea/repo1/st_spcs_exoauth
         env:
         SNOWFLAKE_WAREHOUSE: wh_xs
         secrets:
         - snowflakeSecret: sec_exoauth
            secretKeyRef: secret_string
            envVarName: SNOWAUTHEX_SECRETS
   endpoints:
      - name: streamlit
         port: 8501
         public: true
   $$
   EXTERNAL_ACCESS_INTEGRATIONS = ( EAI_EXOAUTH )
   ;
   ```
11. See that the service has started by executing `SHOW SERVICES IN COMPUTE POOL tutorial_compute_pool` 
   and `SELECT system$get_service_status('st_spcs')`.
12. Find the public endpoint for the service by executing `SHOW ENDPOINTS IN SERVICE st_spcs`.
13. Now that we have the endpoint, we need to update the TOML in the SECRET.
   1. Edit `secrets.toml` and change the `redirect_url` to the `streamlit` endpoint.
   2. Run `make secret` and execute the resulting DDL.
14. Nowe we need to SUSPEND and RESUME the service to pick up the new secret:
   ```
   ALTER SERVICE sispcs_snowauthex SUSPEND;
   ALTER SERVICE sispcs_snowauthex RESUME;
   ```
15. Grant permissions for folks to visit the Streamlit. You do this by granting 
   `USAGE` on the service: `GRANT USAGE ON SERVICE st_spcs TO ROLE some_role`, 
   where you specify the role in place of `some_role`.
16. Navigate to the endpoint and authenticate. Note, you must use a user whose
   default role is _not_ `ACCOUNTADMIN`, `SECURITYADMIN`, or `ORGADMIN`.
17. Enjoy!


## Local Testing
This Streamlit can be tested running locally. To do that, build the
image for your local machine with `make build_local`.

In order to run the Streamlit in the container, we need to set some 
environment variables in our terminal session before running the 
container. The variables to set are:
* `SNOWFLAKE_ACCOUNT` - the account locator for the Snowflake account
* `SNOWFLAKE_USER` - the Snowflake username to use
* `SNOWFLAKE_PASSWORD` - the password for the Snowflake user
* `SNOWFLAKE_WAREHOUSE` - the warehouse to use
* `SNOWFLAKE_DATABASE` - the database to set as the current database (does not really matter that much what this is set to)
* `SNOWFLAKE_SCHEMA` - the schema in the database to set as the current schema (does not really matter that much what this is set to)

You also need to copy the `secrets.toml` file to `src/.streamlit/secrets.toml`:
```
mkdir -p src/.streamlit
cp secrets.toml src/.streamlit/secrets.toml
```

Once those have been set, run the Streamlit container with `make run`. Navigate
to `http://localhost:8080`.

You can also run Streamlit from your terminal by changing directory to `src`
and running `streamlit run app.py`.

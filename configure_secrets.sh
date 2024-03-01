#!/bin/bash

# Prompt user for input
read -p "What is the IdP's authorization endpoint? " authorization_endpoint
read -p "What is the IdP's token endpoint? " token_endpoint
read -p "What is the IdP's JWKS URI? " jwks_uri
read -p "What is the client ID? " client_id
read -p "What is the client secret? " client_secret
read -p "What is the audience? " audience
read -p "What is the field that contains the identity that maps to the Snowflake user (e.g., sub)? " identity_field
read -p "What is the Snowflake account? " snowflake_account
read -p "What is the database in the account? " snowflake_database
read -p "What is the schema in the account? " snowflake_schema
read -p "What warehouse can the application use? " snowflake_warehouse


# Paths to the files
secrets="secrets.toml"

# Copy files
cp $secrets.template $secrets

# Replace placeholders in Secrets file using | as delimiter
sed -i "" "s|<<SNOWFLAKE_ACCOUNT>>|$snowflake_account|g" $secrets
sed -i "" "s|<<AUTHORIZATION_ENDPOINT>>|$authorization_endpoint|g" $secrets
sed -i "" "s|<<TOKEN_ENDPOINT>>|$token_endpoint|g" $secrets
sed -i "" "s|<<JWKS_URI>>|$jwks_uri|g" $secrets
sed -i "" "s|<<CLIENT_ID>>|$client_id|g" $secrets
sed -i "" "s|<<CLIENT_SECRET>>|$client_secret|g" $secrets
sed -i "" "s|<<AUDIENCE>>|$audience|g" $secrets
sed -i "" "s|<<IDENTITY_FIELD>>|$identity_field|g" $secrets
sed -i "" "s|<<SNOWFLAKE_DATABASE>>|$snowflake_database|g" $secrets
sed -i "" "s|<<SNOWFLAKE_SCHEMA>>|$snowflake_schema|g" $secrets
sed -i "" "s|<<SNOWFLAKE_WAREHOUSE>>|$snowflake_warehouse|g" $secrets


echo "Placeholder values have been replaced!"

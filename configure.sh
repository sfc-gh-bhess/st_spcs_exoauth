#!/bin/bash

# Prompt user for input
read -p "What is the image repository URL (SHOW IMAGE REPOSITORIES IN SCHEMA)? " repository_url
read -p "What warehouse can the Streamlit app use? " warehouse
read -p "What is the stage location for the Streamlit secrets file? " secrets_stage

# Paths to the files
makefile="./Makefile"
streamlit_yaml="./streamlit.yaml"

# Copy files
cp $makefile.template $makefile
cp $streamlit_yaml.template $streamlit_yaml

# Replace placeholders in Makefile file using | as delimiter
sed -i "" "s|<<repository_url>>|$repository_url|g" $makefile

# Replace placeholders in Streamlit file using | as delimiter
sed -i "" "s|<<repository_url>>|$repository_url|g" $streamlit_yaml
sed -i "" "s|<<warehouse_name>>|$warehouse|g" $streamlit_yaml
sed -i "" "s|<<secrets_stage>>|$secrets_stage|g" $streamlit_yaml

echo "Placeholder values have been replaced!"

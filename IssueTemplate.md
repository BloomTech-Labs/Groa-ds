<!--- Provide a general summary of the issue in the Title above -->

## Expected Behavior
Data accepted by the endpoint should be accepted and processed into a format(s) that the model will ingest. 

## Current Behavior
The processor.py file accepts CSV data and converts it to a pandas dataframe. 

The model only accepts a single nested numpy array. 

Therefore if you try to give the sagemaker container a numpy array it will throw an error due to it only accepting csv data and if you provide csv data the model will error due to only accepting a nested array. 

Additionally, the method for inferencing is currently giving an error due to the import being directly tied to a tensorflow based model. 

## Possible Solution
Reconfigure processor.py so that it accepts csv data but converts that data into a nested numpy array.

Additionally we must make use of [Sagemaker's SDK Predictors class](https://sagemaker.readthedocs.io/en/stable/predictors.html). 

## Steps to Reproduce
1. Deploy endpoint
2. Using the fulldeploy notebook, run all cells
3. Observe type error from accepting a csv

## Context (Environment)

This is a core functionality blocker. 

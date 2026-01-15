#TODO: description:


## Setup: 
#### Prerequisites： Git and anaconda (or miniconda)
```Bash
conda env create -f environment.yaml
conda activate dsait4090
```


-pipeline.py file: It reads transcripts, iterates through models defined in models.json, enforces JSON schema constraints, and saves generation results to CSV.

-.env file: Stores Keys.

-models.json file: A configuration file that defines the model matrix. It includes settings for Open-Source (Llama via DeepInfra) and Closed-Source (Gemini) models across various sizes (Small, Medium, Large, Reasoning).

-environment.yaml file: The Conda configuration file used to set up the dsait4090 python environment.

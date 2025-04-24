# MetaGPT Setup & Usage

## Installation

To install MetaGPT and the required dependencies, run:

```bash
pip install metagpt
pip install httpx==0.27.2
```
## Configure LLM
Initialize the configuration file with:

```bash
metagpt --init-config
```
This will generate a file at ~/.metagpt/config2.yaml.
Edit this file with your LLM configurations to ensure your API key and other sensitive information are kept private. 
For full details on how to properly configure the file, refer to the [MetaGPT documentation](https://docs.deepwisdom.ai/main/en/guide/get_started/configuration/llm_api_configuration.html).

## Running the code
To start the code with two data product YAML files, use the following command:

```bash
python start.py --dp1_path=".Path/To/First/DataProduct.yml" --dp2_path=".Path/To/Second/DataProduct.yml" --n_round=10
Replace the paths with the actual locations of your data product files.
```

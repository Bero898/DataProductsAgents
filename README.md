# Data Products Agents Evaluation Workspace

This workspace contains code and data for evaluating compatibility assessments between data products using multiple metrics and agent-based approaches.

## Project Structure

- `run_metrics/bleu.py` — BLEU score evaluation (requires NLTK)
- `run_metrics/BERTScore.py` — BERTScore evaluation (requires bert-score)
- `run_metrics/g-eval_ChatGPTMesh.py` — G-eval (Deepeval) evaluation (requires deepeval and dependencies)
- `metagpt/` — MetaGPT agent code (requires MetaGPT and dependencies)
- `Data Products/` — Example data product YAMLs and results
- `GEvalTest/` — G-eval test cases, results, and ground truth

## Example Data Products

Example data products can be found in the [`Data Products`](Data%20Products/README.md) directory. The [`example-DPs/ChatGPT_DMesh`](Data%20Products/example-DPs/ChatGPT_DMesh) subdirectory provides the synthetic data mesh used for testing with [`test.py`](test.py).

NOTE: Additionally [`example-DPs/ChatGPT_DMesh`](Data%20Products/example-DPs/ChatGPT_DMesh) has a folder Results, this contains the results obtained from running test.py (that is the compatibility reports). If test.py is not working consider deleting this folder as it will reset the compatibility reports. Similarly if the metrics are not running consider deleting their corresponding folder in [`GEvalTest/ChatGPT_DMesh`](Data%20Products/GEvalTest)

## Environment Setup

**Important:**  
Each metric should be run in its own Python virtual environment to avoid dependency conflicts. The MetaGPT based framework should also be given its own enviornment.

---

### 1. BLEU Score (`run_metrics/bleu.py`)

**Environment:**  
Create and activate a new virtual environment (e.g., `.bleu`).

**Required Libraries:**
- `nltk`

**Setup:**
```sh
python -m venv .bleu
source .bleu/Scripts/activate  # or .bleu/bin/activate on Linux/Mac
pip install nltk
```

---

### 2. BERTScore (`run_metrics/BERTScore.py`)

**Environment:**  
Create and activate a new virtual environment (e.g., `.BERTScore`).

**Required Libraries:**
- `bert-score`
- `torch` (will be installed as a dependency)

**Setup:**
```sh
python -m venv .BERTScore
source .BERTScore/Scripts/activate  # or .BERTScore/bin/activate
pip install bert-score
```

---

### 3. Deepeval G-eval (`run_metrics/g-eval_ChatGPTMesh.py`)

**Environment:**  
Create and activate a new virtual environment (e.g., `.deepeval`).

**Required Libraries:**
- `deepeval`
- Any additional dependencies for your LLM provider (e.g., OpenAI, Groq, etc.)

**Setup:**
```sh
python -m venv .deepeval
source .deepeval/Scripts/activate  # or .deepeval/bin/activate
pip install deepeval
# Install any LLM provider SDKs as needed
```

---

### 4. MetaGPT Agents (`metagpt/`)

**Environment:**  
Create and activate a new virtual environment (e.g., `.mgpt-lib`).

**Required Libraries:**
- `metagpt`
- Any other dependencies specified in your agent code

**Setup:**
```sh
python -m venv .mgpt-lib
source .mgpt-lib/Scripts/activate  # or .mgpt-lib/bin/activate
pip install metagpt
```

---

## Running Compatibility Assessments

To test compatibility between example data products in the synthetic data mesh, use [`test.py`](test.py). This script uses the data products in [`Data Products/example-DPs/ChatGPT_DMesh`](Data%20Products/example-DPs/ChatGPT_DMesh) as input.

---

## Running Compatibility Assessments

To test compatibility between example data products in the synthetic data mesh, use [`test.py`](test.py). This script uses the data products in [`Data Products/example-DPs/ChatGPT_DMesh`](Data%20Products/example-DPs/ChatGPT_DMesh) as input.

You can also run a compatibility assessment between any two data products directly using `start.py` with command-line arguments, for example:
```sh
python start.py --dp1_path=PATH_TO_DATA_PRODUCT_1 --dp2_path=PATH_TO_DATA_PRODUCT_2 --n_round=NUMBER_OF_ROUNDS
```
---

## Notes

- Each environment is isolated; activate the appropriate environment before running the corresponding scripts.
- Results and logs are stored in the `GEvalTest/`, `logs/`, and `Data Products/example-DPs/ChatGPT_DMesh/Results/` directories.
- For more details on data product specifications, see [Data Products/README.md](Data%20Products/README.md).
- The file [`GEvalTest/full_detailed_compatibility_report.txt`](GEvalTest/full_detailed_compatibility_report.txt) contains the synthetic data compatibility reports produced by ChatGPT. These reports summarize the compatibility analysis, mismatches, recommendations, and conclusions for each pair of example data products in the synthetic data mesh.


---

## Example Usage

**Run BLEU evaluation:**
```sh
source .bleu/Scripts/activate
python run_metrics/bleu.py
```

**Run BERTScore evaluation:**
```sh
source .BERTScore/Scripts/activate
python run_metrics/BERTScore.py
```

**Run Deepeval G-eval:**
```sh
source .deepeval/Scripts/activate
python run_metrics/g-eval_ChatGPTMesh.py
```

**Run MetaGPT agents:**
```sh
source .mgpt-lib/Scripts/activate
# Run your MetaGPT agent scripts as needed
```

**Run compatibility assessments on synthetic data mesh:**
```sh
python test.py
```
---

## Environment Variables

Some scripts (such as those using Deepeval G-eval) require a Groq API key for LLM access.  
You must provide your Groq API key in a `.env` file as follows:

```
GROQ_API_KEY=your_groq_api_key_here
```

Place this `.env` file in the appropriate directory (e.g., `GEvalTest/`) before running scripts that require LLM access.

---

## Contact

For questions or issues, please refer to the code comments or contact the repository maintainer.
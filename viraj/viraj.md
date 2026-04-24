# Local setup

Run these commands from inside the `up-skin` folder:

source ~/.venvs/global/bin/activate

```bash
# Create the local virtual environment if it does not already exist.
/opt/homebrew/bin/python3.11 -m venv venv

# Start the virtual environment.
source venv/bin/activate

# Install the project requirements.
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

# Start Jupyter for the notebooks.
jupyter lab

# When finished, leave the virtual environment.
deactivate
```

## Build handoff artifacts

Run this after the Kaggle CSVs are available in `Datasets/`:

```bash
source venv/bin/activate
python viraj/scripts/build_handoff_artifacts.py
```

This creates local outputs under `artifacts/`:

- Matrix Factorization train/test/prediction artifacts
- transformer product embeddings and nearest neighbors
- hybrid metrics
- `artifacts/handoff/bayesian_handoff_features.csv` for the Bayesian Neural Network step

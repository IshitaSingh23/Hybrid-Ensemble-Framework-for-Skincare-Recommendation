# Local setup

Run these commands from inside the `up-skin` folder:

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

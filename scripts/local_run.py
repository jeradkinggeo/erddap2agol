import os
import sys

os.environ['AGOL_HOME'] = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'venv'))

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from erddap2agol import run

def main():
    run.cui()

if __name__ == "__main__":
    run.cui()
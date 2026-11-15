# Pipeline rules (Python)
- Python 3.11, type hints everywhere, pydantic v2 models generated from contracts/.
- numpy float32 for images; never load full SPHEREx files.
- Every public function has a docstring stating units of inputs/outputs.
- Tests use only real fixtures in tests/data (tiny cutouts). Mark network tests with @pytest.mark.network.

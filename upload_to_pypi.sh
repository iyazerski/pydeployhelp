source venv/bin/activate
rm -rf build dist pydeployhelp.egg-info
python -m build
python -m twine upload dist/*

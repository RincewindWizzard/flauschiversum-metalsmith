run:
	export FLASK_APP=flauschiversum.py; flask run
debug:
	export FLASK_DEBUG=1; export FLASK_APP=flauschiversum.py; flask run
clean:
	rm -rf build

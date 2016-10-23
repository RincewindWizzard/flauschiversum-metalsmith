run:
	export FLASK_APP=flauschiversum.py; flask run
debug:
	export FLASK_DEBUG=1; export FLASK_APP=flauschiversum.py; flask run
build:
	rm -r build; mkdir build; cd build; wget -m http://localhost:5000/
clean:
	rm -rf build

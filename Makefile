RUN = poetry run

test:
	$(RUN) python -m unittest

all_py: src/linkml_renderer/style/model.py 

%.py: %.yaml
	$(RUN) gen-pydantic $< > $@.tmp && mv $@.tmp $@ && $(RUN) black $@


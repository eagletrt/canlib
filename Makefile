test:
	cd test && $(MAKE)

clean:
	rm -rf ids
	rm -rf lib
	rm -rf proto
	rm -rf csv
	cd test && $(MAKE) clean

format:
	black .
	isort .

.PHONY: test clean format

build:
	python3 canlib/__init__.py generate-all test/networks/ ids/ lib/ proto/ csv/
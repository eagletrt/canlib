all:
	canlib generate-ids networks ids
	canlib generate-lib networks ids lib

	mkdir -p out

	gcc test.c -o out/test_c
	g++ test.c -o out/test_cpp

	@echo "=============="
	@echo "Starting tests"
	@echo "=============="

	./out/test_c
	./out/test_cpp
	python3 test.py

clean:
	rm -rf ids
	rm -rf lib
	rm -rf out


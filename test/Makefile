all:
	canlib generate-ids networks ids
	canlib generate-lib networks ids lib

	mkdir -p out

	gcc test.c -o out/test_c
	cp test.c test.cpp
	g++ test.cpp -o out/test_cpp

	@echo "=============="
	@echo "Starting tests"
	@echo "=============="

	./out/test_c > out/test_c.out
	./out/test_cpp > out/test_cpp.out
	python3 test.py > out/test_python.out

	diff3 out/test_c.out out/test_cpp.out out/test_python.out

clean:
	rm -rf ids
	rm -rf lib
	rm -rf out

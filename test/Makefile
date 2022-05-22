all:
	canlib generate-ids networks ids
	canlib generate-lib networks ids lib

	mkdir -p out

	gcc main.c -o out/test_c
	g++ main.cpp -o out/test_cpp

	./out/test_c
	./out/test_cpp
	python3 test.py

clean:
	rm -rf ids
	rm -rf lib
	rm -rf out


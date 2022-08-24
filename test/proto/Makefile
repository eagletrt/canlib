all:
	canlib generate-ids ../networks ids
	canlib generate-lib ../networks ids lib
	canlib generate-proto ../networks ids proto

	mkdir -p out

	cd out &&  cmake .. && make -j

	@echo "===================="
	@echo "Starting PROTO tests"
	@echo "===================="

	./out/test

clean:
	rm -rf ids
	rm -rf lib
	rm -rf out

clean:
	rm -rf ids
	rm -rf sources
	rm -rf protobuf
	rm -rf sheets

format:
	black .
	isort .
	djlint --reformat .

.PHONY: clean format

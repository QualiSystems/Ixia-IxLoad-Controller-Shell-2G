
.PHONY: build
install:
	pip install -i http://$(repo):8036 --trusted-host $(repo) -U -r test_requirements.txt

install-local:
	make install repo=localhost

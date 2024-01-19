all:
	make install

install:
	pip install --upgrade pip
	pip install -r requirements.txt

clear_logs:
	@echo "Clearing logs folder"
	rm -rf logs/

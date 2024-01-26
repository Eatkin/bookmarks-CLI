all:
	make install

install:
	pip install --upgrade pip
	pip install -r requirements.txt

clear_logs:
	@echo "Clearing logs folder"
	rm -rf logs/

clear_db:
	@echo "Deleting the database lol"
	rm bookmarks.db

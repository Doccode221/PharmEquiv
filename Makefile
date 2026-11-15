install:
	pip install -r requirements-dev.txt

data:
	python scripts/build_dataset.py

scrape:
	python scripts/scrape_arp.py && python scripts/build_dataset.py

test:
	pytest -q

run:
	streamlit run app.py

docker:
	docker build -t pharmequiv . && docker run -p 8501:8501 pharmequiv

.PHONY: install data scrape test run docker

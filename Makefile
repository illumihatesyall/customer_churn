.PHONY: data eda model interpret all

data:
	python src/etl.py

eda:
	python src/eda.py

model:
	python src/model.py

interpret:
	python src/interpret.py

memo:
	python src/memo.py

all: data eda model interpret memo

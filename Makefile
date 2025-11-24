.PHONY: airflow-build airflow-init airflow-create-user airflow-up airflow-down airflow-reset

airflow-build:
	docker compose build

airflow-init:
	docker compose up airflow-init

airflow-create-user:
	docker compose run --rm airflow-webserver airflow users create \
		--username admin \
		--firstname Admin \
		--lastname User \
		--role Admin \
		--email admin@example.com \
		--password admin

airflow-up:
	docker compose up

airflow-down:
	docker compose down

airflow-reset:
	docker compose down --volumes --remove-orphans || true
	$(MAKE) airflow-build
	$(MAKE) airflow-init
	$(MAKE) airflow-create-user
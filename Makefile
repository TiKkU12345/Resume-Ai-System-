.PHONY: help build run stop restart logs clean shell

help:
	@echo: "AI Resume Shortlisting - Docker Commands"
	@ech ""
	@echo "make build   - Build Docker image"
	@echo "make run   - start application"	
	@echo "make stop   - stop application"	
	@echo "make restart   - restart application"	
	@echo "make logs   -  views logs"	
	@echo "make clean   -  Remove containers"	
	@echo "make shell  -  open containers shell"	


build:
	@echo "Building..."
	docker-compose buildrun:

run:
	@echo "Starting..."
	docker-compose up -d
	@echo  "Running at http://localhost:8501"

stop:
	@echo "Stopping..."
	docker-compose down

restart: stop run

logs:
	docker-compose logs -f

clean:
	docker-compose down -v
	docker system prune -f

shell:
	docker-compose exec resume-Shortlisting bash

	
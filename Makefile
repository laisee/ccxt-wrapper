push:
	@docker push sjc.vultrcr.com/moolah/moolah-trading-watcher
	@docker push sjc.vultrcr.com/moolah/moolah-trading-web

tag:
	@docker tag moolah-trading-watcher sjc.vultrcr.com/moolah/moolah-trading-watcher
	@docker tag moolah-trading-web sjc.vultrcr.com/moolah/moolah-trading-web

build:
	@docker-compose build

clean:
	@docker rmi -f sjc.vultrcr.com/moolah/moolah-trading-watcher
	@docker rmi -f sjc.vultrcr.com/moolah/moolah-trading-web

all: clean build tag push

docker-compose build

docker tag moolah-trading-watcher sjc.vultrcr.com/moolah/moolah-trading-watcher
docker push sjc.vultrcr.com/moolah/moolah-trading-watcher

docker tag moolah-trading-web sjc.vultrcr.com/moolah/moolah-trading-web
docker push sjc.vultrcr.com/moolah/moolah-trading-web

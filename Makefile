build:
	metalsmith

preview: build
	kill -9 `cat /tmp/pyhttpd.pid` || true
	cd build; python3 -m http.server 8080 & echo $! > /tmp/pyhttpd.pid; sleep 2

test: preview
	wget --spider -o /tmp/wget.log -e robots=off  -r -p http://localhost:8080/; grep -B 2 '404 File not found' /tmp/wget.log

clean:
	rm -rf build

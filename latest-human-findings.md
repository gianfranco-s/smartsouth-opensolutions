http://192.1.1.38:81/ -- nginx proxy manager

10.77.10.5
openportal01 es aparentemente el NGINX principal

What would settle it in one step, using the same access you already have on that box: look at /etc/nginx/sites-enabled/ (or the container's /data/nginx/proxy_host/ if it's dockerized) and see how many distinct upstream domains/targets it routes to. One config for Maipú's portal → it's a client-specific proxy, not "principal." A pile of configs for domains across multiple clients → then it genuinely competes with the 4 NPM hosts for that role, and the findings.md "resuelto" note needs walking back.


http://192.1.3.250/firewall_nat.php -- no tiene NAT rules

import subprocess
from config import LB_IP

PEM_KEY = "/home/ubuntu/autoscaler-key.pem"

def update_lb(worker_ips):
    config = """<VirtualHost *:80>

    ProxyRequests Off
    ProxyPreserveHost On

    <Proxy "balancer://mycluster">
"""

    for ip in worker_ips:
        config += f"        BalancerMember http://{ip}:8080\n"

    config += """
    </Proxy>
     ProxyPass "/" "balancer://mycluster/"
    ProxyPassReverse "/" "balancer://mycluster/"

</VirtualHost>
"""

    # Write config to temp file
    with open("lb.conf", "w") as f:
        f.write(config)

    # Copy config to Load Balancer
        subprocess.run(f"scp -i {PEM_KEY} lb.conf ubuntu@{LB_IP.replace('http://','://','')}:~/", shell=True)

    # Move config + reload Apache on LB
    subprocess.run(f"""
    ssh -i {PEM_KEY} ubuntu@{LB_IP.replace('http://','')} '
    sudo mv ~/lb.conf /etc/apache2/sites-available/000-default.conf &&
    sudo systemctl reload apache2
    '
    """, shell=True)

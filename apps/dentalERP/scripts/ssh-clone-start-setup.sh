# 1. SSH to VM
gcloud compute ssh dental-erp-vm --zone=us-central1-a

# 2. Clone repo
cd /opt && sudo git clone https://github.com/nomad3/dentalERP.git
cd dentalERP

# 3. Run setup
sudo chmod +x setup-vm.sh && sudo ./setup-vm.sh

# 4. Start app
sudo docker-compose -f docker-compose.prod.yml up -d

# 5. Check status
sudo docker-compose -f docker-compose.prod.yml ps

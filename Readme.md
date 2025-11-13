terraform init
terraform apply -auto-approve


terraform output inventory > ~/cloudbot-infra/ansible/inventories/hosts.ini

ansible-playbook ~/cloudbot-infra/ansible/playbooks/deploy_agent.yml

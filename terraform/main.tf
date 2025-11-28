provider "aws" {
  region = "us-east-1"
}

resource "aws_key_pair" "cloudbot_key" {
  key_name   = "cloudbot-key"
  public_key = file("~/.ssh/id_rsa.pub")
}

resource "aws_security_group" "cloudbot_sg" {
  name        = "cloudbot-sg"
  description = "Allow SSH, HTTP, and Agent Port 8000"

  ingress {
    description      = "SSH"
    from_port        = 22
    to_port          = 22
    protocol         = "tcp"
    cidr_blocks      = ["0.0.0.0/0"]
  }

  ingress {
    description      = "HTTP"
    from_port        = 80
    to_port          = 80
    protocol         = "tcp"
    cidr_blocks      = ["0.0.0.0/0"]
  }

  ingress {
    description      = "Agent API (FastAPI)"
    from_port        = 8000
    to_port          = 8000
    protocol         = "tcp"
    cidr_blocks      = ["0.0.0.0/0"]
  }

  egress {
    from_port        = 0
    to_port          = 0
    protocol         = "-1"
    cidr_blocks      = ["0.0.0.0/0"]
  }
}

# Agent Nodes only (controller = local)
resource "aws_instance" "agents" {
  count                  = 2
  ami                    = "ami-08c40ec9ead489470"
  instance_type          = "t3.micro"
  key_name               = aws_key_pair.cloudbot_key.key_name
  vpc_security_group_ids = [aws_security_group.cloudbot_sg.id]
  tags                   = { Name = "cloudbot-agent-${count.index + 1}" }
}       

# Generate Ansible Inventory (no master IP)
data "template_file" "inventory" {
  template = file("${path.module}/inventory.tpl")
  vars = {
    agent_ips = join("\n", aws_instance.agents[*].public_ip)
  }
}

output "inventory" {
  value = data.template_file.inventory.rendered
}

output "agent_ips" {
  value = aws_instance.agents[*].public_ip
}

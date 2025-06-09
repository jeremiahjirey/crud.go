terraform {
    required_providers {
    aws = {
        source = "hashicorp/aws"
        version = "5.96.0"
    }
    random = {
        source = "hashicorp/random"
        version = "~> 3.0"
    }
    }
}

provider "aws" {
    region = "us-east-1"
}

resource "aws_vpc" "go_vpc" {
    cidr_block           = "25.1.0.0/16"
    enable_dns_support   = true
    enable_dns_hostnames = true
    tags = {
        Name = "go-imannuel"
    }
}

resource "aws_vpc_ipv6_cidr_block_association" "ipv6ass" {
    vpc_id = aws_vpc.go_vpc.id
    assign_generated_ipv6_cidr_block = "true"
}

resource "aws_internet_gateway" "go_igw" {
    vpc_id = aws_vpc.go_vpc.id
    tags = {
    Name = "go-igw"
    }
}

resource "aws_subnet" "go_public_a" {
    vpc_id                  = aws_vpc.go_vpc.id
    cidr_block              = "25.1.0.0/24"
    availability_zone       = "us-east-1a"
    map_public_ip_on_launch = true
    tags = {
    Name = "go-public-subnet-a"
    }
}

resource "aws_subnet" "go_public_b" {
    vpc_id                  = aws_vpc.go_vpc.id
    cidr_block              = "25.1.2.0/24"
    availability_zone       = "us-east-1b"
    map_public_ip_on_launch = true
    tags = {
    Name = "go-public-subnet-b"
    }
}

resource "aws_subnet" "go_private_a" {
    vpc_id            = aws_vpc.go_vpc.id
    cidr_block        = "25.1.1.0/24"
    availability_zone = "us-east-1a"
    tags = {
    Name = "go-private-subnet-a"
    }
}

resource "aws_subnet" "go_private_b" {
    vpc_id            = aws_vpc.go_vpc.id
    cidr_block        = "25.1.3.0/24"
    availability_zone = "us-east-1b"
    tags = {
    Name = "go-private-subnet-b"
    }
}

resource "aws_eip" "go_nat_eip" {
    vpc = true
}

resource "aws_nat_gateway" "go_nat" {
    allocation_id = aws_eip.go_nat_eip.id
    subnet_id     = aws_subnet.go_public_a.id
    tags = {
    Name = "go-nat"
    }
}

resource "aws_route_table" "go_public_rt" {
    vpc_id = aws_vpc.go_vpc.id

    route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.go_igw.id
    }

    tags = {
        Name = "go-public"
    }
}

resource "aws_route_table_association" "go_public_assoc_a" {
    subnet_id      = aws_subnet.go_public_a.id
    route_table_id = aws_route_table.go_public_rt.id
}

resource "aws_route_table_association" "go_public_assoc_b" {
    subnet_id      = aws_subnet.go_public_b.id
    route_table_id = aws_route_table.go_public_rt.id
}

resource "aws_route_table" "go_private_rt" {
    vpc_id = aws_vpc.go_vpc.id

    route {
        cidr_block     = "0.0.0.0/0"
        nat_gateway_id = aws_nat_gateway.go_nat.id
    }

    tags = {
        Name = "go-private"
    }
}

resource "aws_route_table_association" "go_private_assoc_a" {
    subnet_id      = aws_subnet.go_private_a.id
    route_table_id = aws_route_table.go_private_rt.id
}

resource "aws_route_table_association" "go_private_assoc_b" {
    subnet_id      = aws_subnet.go_private_b.id
    route_table_id = aws_route_table.go_private_rt.id
}

resource "aws_security_group" "go_sg_app" {
    name   = "go-sg"
    vpc_id = aws_vpc.go_vpc.id

    ingress {
        from_port   = 0
        to_port     = 0
        protocol    = "-1"
        cidr_blocks = ["0.0.0.0/0"]
    }

    egress {
        from_port   = 0
        to_port     = 0
        protocol    = "-1"
        cidr_blocks = ["0.0.0.0/0"]
    }

    tags = {
        Name = "go-sg-apps"
    }
}

resource "aws_ecr_repository" "goecr" {
  name                 = "goecr25"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }
  encryption_configuration {
    encryption_type = "AES256"
  }
}

resource "aws_db_subnet_group" "private" {
  name       = "private_subnet_group"
  subnet_ids = [aws_subnet.go_private_a.id, aws_subnet.go_private_b.id]

  tags = {
    Name = "Private Subnet Group"
  }
}

resource "aws_rds_cluster" "aurora_cluster" {
  cluster_identifier      = "go-aurora"
  engine                  = "aurora-mysql"
  engine_version          = ""
  database_name           = "todoapp"
  master_username         = "admin"
  master_password         = "godatabase"
  backup_retention_period = 7
  preferred_backup_window = "07:00-09:00"
  vpc_security_group_ids  = [aws_security_group.go_sg_app.id]
  db_subnet_group_name    = aws_db_subnet_group.private.name
}

resource "aws_rds_cluster_instance" "cluster_instances1" {
  count              = 2
  identifier         = "go-cluster-instance-${count.index}"
  cluster_identifier = aws_rds_cluster.aurora_cluster.id
  instance_class     = "db.t3.medium"
  engine             = aws_rds_cluster.aurora_cluster.engine
  engine_version     = aws_rds_cluster.aurora_cluster.engine_version
  publicly_accessible = false
}


resource "aws_eks_cluster" "cluster" {
  name = "clusterGo2"

  access_config {
    authentication_mode = "API" 
  }

  role_arn = "arn:aws:iam::778876534404:role/LabRole"
  version  = "1.32"

  vpc_config {
    subnet_ids = [aws_subnet.go_public_a.id,aws_subnet.go_public_b.id,]
    security_group_ids = [aws_security_group.go_sg_app.id]
    endpoint_public_access = true
  } 
}

resource "aws_eks_addon" "addson1" {
  cluster_name = aws_eks_cluster.cluster.name
  addon_name   = "vpc-cni"
}

resource "aws_eks_addon" "addson2" {
  cluster_name = aws_eks_cluster.cluster.name
  addon_name   = "coredns" 
}
resource "aws_eks_addon" "addson3" {
  cluster_name = aws_eks_cluster.cluster.name
  addon_name   = "kube-proxy" 
}
resource "aws_eks_addon" "addson4" {
  cluster_name = aws_eks_cluster.cluster.name
  addon_name   = "eks-pod-identity-agent" 
}
resource "aws_eks_addon" "addson5" {
  cluster_name = aws_eks_cluster.cluster.name
  addon_name   = "node-monitoring-agent" 
}
resource "aws_eks_addon" "addson6" {
  cluster_name = aws_eks_cluster.cluster.name
  addon_name   = "external-dns" 
}

resource "aws_eks_node_group" "go-node" {
  cluster_name    = aws_eks_cluster.cluster.name
  node_group_name = "go-worker"
  node_role_arn   = "arn:aws:iam::778876534404:role/LabRole"
  subnet_ids = [aws_subnet.go_public_a.id,aws_subnet.go_public_b.id]

  scaling_config {
    desired_size = 2
    max_size     = 2
    min_size     = 2
  }
  capacity_type = "ON_DEMAND"
  ami_type = "AL2023_x86_64_STANDARD"
  instance_types = ["t3.medium"]

  update_config {
    max_unavailable = 1
  }
}




# Ambil IAM Role yang sudah ada
data "aws_iam_role" "existing_lab_role" {
    name = "LabRole"
}

# Archive file lambda dari luar folder terraform
data "archive_file" "get" {
    type        = "zip"
    source_file = "${path.module}/../lambda/lambda_function.py"
    output_path = "${path.module}/lambda.zip"
}

# Deploy Lambda function pakai role existing
resource "aws_lambda_function" "lambda" {
    function_name    = "lambda-handler"
    role             = data.aws_iam_role.existing_lab_role.arn
    handler          = "lambda_function.lambda_handler"
    runtime          = "python3.13"

    filename         = data.archive_file.get.output_path
    source_code_hash = data.archive_file.get.output_base64sha256

     environment {
    variables = {
      DB_HOST = "dummy"
      DB_USER = "dummy"
      DB_PASSWORD = "dummy"
      DB_NAME = "dummy"
      DB_PORT = "dummy"
    } 
  }
}

resource "aws_api_gateway_rest_api" "api" {
    name = "go-api"
}

resource "aws_api_gateway_resource" "resource" {
    path_part   = "task"
    parent_id   = aws_api_gateway_rest_api.api.root_resource_id
    rest_api_id = aws_api_gateway_rest_api.api.id
}

resource "aws_api_gateway_method" "post_method" {
    rest_api_id   = aws_api_gateway_rest_api.api.id
    resource_id   = aws_api_gateway_resource.resource.id
    http_method   = "POST"
    authorization = "NONE"
}


resource "aws_api_gateway_integration" "get_integration" {
    rest_api_id             = aws_api_gateway_rest_api.api.id
    resource_id             = aws_api_gateway_resource.resource.id
    http_method             = aws_api_gateway_method.post_method.http_method
    integration_http_method = "POST"
    type                    = "AWS_PROXY"
    uri                     = aws_lambda_function.lambda.invoke_arn
}

resource "aws_lambda_permission" "get_premission" {
    statement_id  = "AllowAPIGatewayInvoke"
    action        = "lambda:InvokeFunction"
    function_name = aws_lambda_function.lambda.function_name
    principal     = "apigateway.amazonaws.com"

    source_arn = "${aws_api_gateway_rest_api.api.execution_arn}//"
}

resource "aws_api_gateway_method" "get_method" {
    rest_api_id   = aws_api_gateway_rest_api.api.id
    resource_id   = aws_api_gateway_resource.resource.id
    http_method   = "GET"
    authorization = "NONE"
}


resource "aws_api_gateway_integration" "get_integration_2" {
    rest_api_id             = aws_api_gateway_rest_api.api.id
    resource_id             = aws_api_gateway_resource.resource.id
    http_method             = aws_api_gateway_method.get_method.http_method
    integration_http_method = "POST"
    type                    = "AWS_PROXY"
    uri                     = aws_lambda_function.lambda.invoke_arn
}


resource "aws_api_gateway_method" "put_method" {
    rest_api_id   = aws_api_gateway_rest_api.api.id
    resource_id   = aws_api_gateway_resource.resource.id
    http_method   = "GET"
    authorization = "NONE"
}


resource "aws_api_gateway_integration" "get_integration_3" {
    rest_api_id             = aws_api_gateway_rest_api.api.id
    resource_id             = aws_api_gateway_resource.resource.id
    http_method             = aws_api_gateway_method.put_method.http_method
    integration_http_method = "POST"
    type                    = "AWS_PROXY"
    uri                     = aws_lambda_function.lambda.invoke_arn
}


resource "aws_api_gateway_method" "delete_method" {
    rest_api_id   = aws_api_gateway_rest_api.api.id
    resource_id   = aws_api_gateway_resource.resource.id
    http_method   = "GET"
    authorization = "NONE"
}


resource "aws_api_gateway_integration" "get_integration_4" {
    rest_api_id             = aws_api_gateway_rest_api.api.id
    resource_id             = aws_api_gateway_resource.resource.id
    http_method             = aws_api_gateway_method.delete_method.http_method
    integration_http_method = "POST"
    type                    = "AWS_PROXY"
    uri                     = aws_lambda_function.lambda.invoke_arn
}


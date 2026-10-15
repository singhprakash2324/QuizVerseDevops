# AWS EC2 Deployment Guide: QuizVerse Stack

This guide details the step-by-step procedure to deploy the QuizVerse full-stack application (Streamlit App, Prometheus, Grafana) onto an AWS EC2 instance.

---

## 1. Launch AWS EC2 Instance

1. Navigate to the **AWS Management Console** -> **EC2** -> **Launch Instance**.
2. **Name**: `quizverse-production` (or custom identifier).
3. **AMI**: Ubuntu Server 22.04 LTS or 24.04 LTS (HVM, SSD Volume Type, 64-bit x86).
4. **Instance Type**: `t3.small` (2 vCPUs, 2 GiB RAM) or larger (recommended for hosting Streamlit, Prometheus, and Grafana simultaneously).
5. **Key Pair**: Select or create an SSH key pair (`quizverse-key.pem`).
6. **Storage**: Minimum `20 GB` gp3 root volume.

---

## 2. Configure Inbound Security Group Rules

Create an EC2 Security Group with the following inbound rules:

| Type | Protocol | Port Range | Source | Description / Purpose |
| :--- | :--- | :--- | :--- | :--- |
| **SSH** | TCP | `22` | `My IP` (`<YOUR_IP>/32`) | Secure administrative SSH access |
| **Custom TCP** | TCP | `8501` | `Anywhere-IPv4` (`0.0.0.0/0`) | Public Streamlit Quiz Application |
| **Custom TCP** | TCP | `8001` | `My IP` (`<YOUR_IP>/32`) | Metrics Endpoint (Scraped by Prometheus internally) |
| **Custom TCP** | TCP | `9090` | `My IP` (`<YOUR_IP>/32`) | Prometheus Server Web UI |
| **Custom TCP** | TCP | `3000` | `My IP` (`<YOUR_IP>/32`) | Grafana Analytics Dashboard |

*Note: For production, keep ports 8001, 9090, and 3000 restricted to your trusted IP address or access them via an SSH tunnel (`ssh -L 3000:localhost:3000 -L 9090:localhost:9090 ubuntu@<EC2_PUBLIC_IP>`).*

---

## 3. Connect and Initialize Server

SSH into your new EC2 instance:
```bash
chmod 400 quizverse-key.pem
ssh -i quizverse-key.pem ubuntu@<EC2_PUBLIC_IP>
```

Run the bootstrap setup script to install Docker and Docker Compose v2:
```bash
curl -fsSL https://raw.githubusercontent.com/<YOUR_USER>/interactive_quiz_application/main/deploy/ec2-setup.sh | bash
# Or clone the repository first and run:
# bash deploy/ec2-setup.sh
newgrp docker
```

---

## 4. Clone Repository & Setup Environment

1. Clone the repository:
```bash
git clone https://github.com/<YOUR_USER>/interactive_quiz_application.git
cd interactive_quiz_application
```

2. Create the `.env` file on the server (never commit this file to version control):
```bash
cat << 'EOF' > .env
GOOGLE_API_KEY=your_actual_gemini_api_key_here
GEMINI_API_KEY=your_actual_gemini_api_key_here
EOF
chmod 600 .env
```

---

## 5. Build and Launch the Stack

Start all services in detached mode with restart policies enabled:
```bash
docker compose up --build -d
```

Verify service status:
```bash
docker compose ps
```
Expected output: `app`, `prometheus`, and `grafana` should all display status `Up`.

Check application logs to ensure no tracebacks:
```bash
docker compose logs app --tail 30
```

Verify the Prometheus metrics endpoint:
```bash
curl -s localhost:8001/metrics | head
```

---

## 6. Accessing Your Deployed Stack

Replace `<EC2_PUBLIC_IP>` with your instance's Elastic IP or public IPv4:

- **QuizVerse Streamlit Web App**: `http://<EC2_PUBLIC_IP>:8501`
- **Prometheus Dashboard & Targets**: `http://<EC2_PUBLIC_IP>:9090/targets`
- **Grafana Analytics Dashboard**: `http://<EC2_PUBLIC_IP>:3000`
  - Default credentials: `admin` / `admin` (update on first login)
  - Pre-provisioned dashboard: **Quiz Application Metrics** (`/d/quizverse-metrics/quiz-application-metrics`)

---

## 7. Service Management

- **View Live Logs**:
  ```bash
  docker compose logs -f
  ```
- **Restart Specific Service**:
  ```bash
  docker compose restart app
  ```
- **Stop Stack**:
  ```bash
  docker compose down
  ```
- **Update Application Code**:
  ```bash
  git pull
  docker compose up --build -d
  ```

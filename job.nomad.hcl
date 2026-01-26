job "cashflow" {
  namespace = "money"

  type = "service"

  group "cashflow" {
    network {
      port "http" {
        to = 8000 # hardcoded in Dockerfile
      }
    }

    service {
      name     = "cashflow"
      port     = "http"
      provider = "nomad"
      tags = [
        "traefik.enable=true",
        "traefik.http.routers.cashflow.rule=Host(`cashflow.datasektionen.se`)",
        "traefik.http.routers.cashflow.tls.certresolver=default",
      ]
    }

    task "cashflow" {
      driver = "docker"

      config {
        image = var.image_tag
        ports = ["http"]
      }

      template {
        data        = <<ENV
{{ with nomadVar "nomad/jobs/cashflow" }}
DATABASE_URL=postgres://cashflow:{{ .db_password }}@postgres.dsekt.internal:5432/cashflow
SECRET_KEY={{ .secret_key }}
OIDC_SECRET={{ .oidc_secret }}
HIVE_SECRET={{ .hive_api_token_secret }}
SPAM_API_KEY={{ .spam_api_key }}
S3_ACCESS_KEY_ID={{ .s3_access_key_id }}
S3_SECRET_ACCESS_KEY={{ .s3_secret_access_key }}
RFINGER_API_KEY={{ .rfinger_api_key }}
{{ end }}

DEBUG=False
DJANGO_LOG_LEVEL=INFO
PYTHONUNBUFFERED=1
BUDGET_URL=https://budget.datasektionen.se
OIDC_PROVIDER=http://sso.nomad.dsekt.internal/op
OIDC_ID=cashflow
REDIRECT_URL=https://cashflow.datasektionen.se/login/
HIVE_URL=https://hive.datasektionen.se
SPAM_URL=https://spam.datasektionen.se
RFINGER_API_URL=https://rfinger.datasektionen.se
S3_REGION=eu-north-1
S3_USE_SIGV4=False
S3_BUCKET_NAME=dsekt-cashflow-2

GOOGLE_ANALYTICS_KEY=UA-96183461-2
ENV
        destination = "local/.env"
        env         = true
      }
    }
  }
}

variable "image_tag" {
  type = string
  default = "ghcr.io/datasektionen/cashflow:latest"
}

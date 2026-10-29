# Cashflow 4 staging. At cutover this replaces job.nomad.hcl, with the host
# changed to cashflow.datasektionen.se.
job "cashflow-next" {
  namespace = "money"

  type = "service"

  group "cashflow-next" {
    network {
      port "http" {
        to = 3000
      }
    }

    service {
      name     = "cashflow-next"
      port     = "http"
      provider = "nomad"
      tags = [
        "traefik.enable=true",
        "traefik.http.routers.cashflow-next.rule=Host(`cashflow-next.datasektionen.se`)",
        "traefik.http.routers.cashflow-next.tls.certresolver=default",
      ]

      check {
        type     = "http"
        path     = "/healthz"
        interval = "15s"
        timeout  = "3s"
      }
    }

    task "cashflow-next" {
      driver = "docker"

      config {
        image = var.image_tag
        ports = ["http"]
      }

      template {
        data        = <<ENV
{{ with nomadVar "nomad/jobs/cashflow-next" }}
# A copy of production restored from a dump. Once Cashflow 4 is trusted, this
# points at the production database so both versions run side by side.
DATABASE_URL=postgres://cashflow_next:{{ .db_password }}@postgres.dsekt.internal:5432/cashflow_next
APP_SECRET_KEY={{ .app_secret_key }}
OIDC_CLIENT_SECRET={{ .oidc_secret }}
HIVE_SECRET={{ .hive_api_token_secret }}
S3_ACCESS_KEY_ID={{ .s3_access_key_id }}
S3_SECRET_ACCESS_KEY={{ .s3_secret_access_key }}
RFINGER_API_KEY={{ .rfinger_api_key }}
{{ end }}

# Deliberately missing while staging runs on a copy of the database:
#
# - SPAM_API_KEY: without it emails are logged, not sent. The copy has real
#   people's addresses, and trying things out on staging must not mail them.
# - FORTNOX_CLIENT_ID/SECRET: the copy holds a copy of production's Fortnox
#   tokens, and Fortnox issues a new refresh token on every refresh. Staging
#   refreshing its copy would disconnect production. Add them only when
#   staging uses the production database, where both versions share one row.
#   See docs/cutover.md.

PORT=3000
PUBLIC_URL=https://cashflow-next.datasektionen.se
HIVE_URL=https://hive.datasektionen.se
OIDC_PROVIDER=https://sso.datasektionen.se/op
OIDC_CLIENT_ID=cashflow
OIDC_REDIRECT_URL=https://cashflow-next.datasektionen.se/auth/callback
BUDGET_URL=https://budget.datasektionen.se
RFINGER_API_URL=https://rfinger.datasektionen.se
SPAM_URL=https://spam.datasektionen.se
# Production's bucket: staging must show the real receipts. New uploads land
# under c4/ beside Cashflow 3's files.
S3_BUCKET_NAME=dsekt-cashflow-2
S3_REGION=eu-north-1
ENV
        destination = "local/.env"
        env         = true
      }

      resources {
        # Uploads of up to 25 MB are held while they stream to S3.
        memory = 256
      }
    }
  }
}

variable "image_tag" {
  type    = string
  default = "ghcr.io/datasektionen/cashflow-next:latest"
}

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
DATABASE_URL=postgres://cashflow_next:{{ .db_password }}@postgres.dsekt.internal:5432/cashflow_next
APP_SECRET_KEY={{ .app_secret_key }}
OIDC_CLIENT_SECRET={{ .oidc_secret }}
HIVE_SECRET={{ .hive_api_token_secret }}
{{ end }}

PORT=3000
HIVE_URL=https://hive.datasektionen.se
OIDC_PROVIDER=https://sso.datasektionen.se/op
OIDC_CLIENT_ID=cashflow
OIDC_REDIRECT_URL=https://cashflow-next.datasektionen.se/auth/callback
ENV
        destination = "local/.env"
        env         = true
      }

      resources {
        memory = 128
      }
    }
  }
}

variable "image_tag" {
  type    = string
  default = "ghcr.io/datasektionen/cashflow-next:latest"
}

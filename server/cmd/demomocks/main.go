// Command demomocks serves the demo's Hive, budget, email and Fortnox locally.
package main

import (
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"strconv"

	"github.com/datasektionen/cashflow/server/internal/demo"
	"github.com/datasektionen/cashflow/server/internal/fortnox"
)

func main() {
	if !demo.Enabled() {
		log.Fatal("demomocks requires DEMO_MODE=true")
	}
	mux := http.NewServeMux()
	mux.HandleFunc("GET /healthz", func(w http.ResponseWriter, r *http.Request) { fmt.Fprint(w, "ok") })
	mux.HandleFunc("GET /api/v1/user/{user}/permissions", func(w http.ResponseWriter, r *http.Request) {
		p, ok := demo.Find(r.PathValue("user"))
		if !ok {
			http.NotFound(w, r)
			return
		}
		respond(w, p.Permissions)
	})
	mux.HandleFunc("POST /api/legacy/sendmail", func(w http.ResponseWriter, r *http.Request) {
		// Consume notifications without forwarding or logging their contents.
		respond(w, map[string]bool{"ok": true})
	})
	mux.HandleFunc("POST /api/batch", func(w http.ResponseWriter, r *http.Request) { respond(w, map[string]string{}) })
	centres := []string{"Sektionslokalsgruppen", "Mottagningen 2026", "Ada", "Näringslivsgruppen", "Studienämnden"}
	secondary := [][]string{{"Inköp", "Evenemang"}, {"Mottagningsveckan", "Phadderiet"}, {"Kärnverksamhet"}, {"Arbetsmarknadsdag"}, {"Studiesociala"}}
	lines := [][][]string{{{"Förbrukningsmaterial", "Städmaterial"}, {"Pubkvällar"}}, {{"Mat", "Aktiviteter"}, {"Tröjor"}}, {{"Fika", "Spel"}}, {{"Lokalhyra", "Tryck"}}, {{"Tentapub", "Läxhjälp"}}}
	mux.HandleFunc("GET /api/CostCentres", func(w http.ResponseWriter, r *http.Request) {
		out := []map[string]any{}
		for i, name := range centres {
			out = append(out, map[string]any{"CostCentreID": i + 1, "CostCentreName": name, "CostCentreType": "committee"})
		}
		respond(w, out)
	})
	mux.HandleFunc("GET /api/SecondaryCostCentres", func(w http.ResponseWriter, r *http.Request) {
		id, _ := strconv.Atoi(r.URL.Query().Get("id"))
		out := []map[string]any{}
		if id > 0 && id <= len(centres) {
			for j, name := range secondary[id-1] {
				out = append(out, map[string]any{"SecondaryCostCentreID": id*10 + j, "SecondaryCostCentreName": name})
			}
		}
		respond(w, out)
	})
	mux.HandleFunc("GET /api/BudgetLines", func(w http.ResponseWriter, r *http.Request) {
		id, _ := strconv.Atoi(r.URL.Query().Get("id"))
		i, j := id/10-1, id%10
		out := []map[string]any{}
		if i >= 0 && i < len(lines) && j < len(lines[i]) {
			for k, name := range lines[i][j] {
				out = append(out, map[string]any{"BudgetLineID": id*10 + k, "BudgetLineName": name, "BudgetLineAccount": "5460", "BudgetLineIncome": 0, "BudgetLineExpense": -50000, "BudgetLineComment": "Simulerad budget för testmiljön"})
			}
		}
		respond(w, out)
	})
	mux.Handle("/", fortnox.NewFake())
	log.Fatal(http.ListenAndServe(":9004", mux))
}
func respond(w http.ResponseWriter, v any) {
	w.Header().Set("Content-Type", "application/json")
	_ = json.NewEncoder(w).Encode(v)
}

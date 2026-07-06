document.addEventListener("DOMContentLoaded", function () {

    const COST_CENTER_URL = "/api/costcenters/";
    const SECONDARY_COST_CENTER_URL = "/api/secondarycostcenters/";
    const BUDGET_LINE_URL = "/api/budgetlines/";

    // In-memory caches
    let costCenterCache = null;
    let secondaryCache = {};
    let budgetCache = {};

    async function fetchJSON(url) {
        const response = await fetch(url, {
            headers: {"Accept": "application/json"}
        });

        if (!response.ok) {
            console.error("API error:", response.status);
            return [];
        }

        return await response.json();
    }

    function populateSelect(select, items, valueKey = "id", labelKey = "name", placeholder = "Välj...") {
        const currentValue = select.value;

        select.innerHTML = "";

        const defaultOption = document.createElement("option");
        defaultOption.value = "";
        defaultOption.textContent = placeholder;
        select.appendChild(defaultOption);

        items.forEach(item => {
            const option = document.createElement("option");
            option.value = String(item[valueKey]);      // <-- ID as value
            option.textContent = item[labelKey]; // <-- name as label
            select.appendChild(option);
        });

        if (currentValue) {
            select.value = currentValue;
        }
    }

    async function loadCostCenters() {
        if (!costCenterCache) {
            costCenterCache = await fetchJSON(COST_CENTER_URL);
        }
        return costCenterCache;
    }

    async function loadSecondary(costCenterId) {
        if (!secondaryCache[costCenterId]) {
            secondaryCache[costCenterId] = await fetchJSON(`${SECONDARY_COST_CENTER_URL}?costcenter_id=${costCenterId}`);
        }
        return secondaryCache[costCenterId];
    }

    async function loadBudgetLines(secondaryId) {
        if (!budgetCache[secondaryId]) {
            budgetCache[secondaryId] = await fetchJSON(`${BUDGET_LINE_URL}?secondarycostcenter_id=${secondaryId}`);
        }
        return budgetCache[secondaryId];
    }

    async function initializeRow(row) {

        const costSelect = row.querySelector(".cost-center-select");
        const secondarySelect = row.querySelector(".secondary-cost-center-select");
        const budgetSelect = row.querySelector(".budget-line-select");

        if (!costSelect) return;

        const preselectedCost = costSelect.value;

        // Load cost centers
        const costCenters = await loadCostCenters();
        populateSelect(costSelect, costCenters, "id", "name", "Välj resultatställe");

        if (preselectedCost) {
            costSelect.value = preselectedCost;

            const secondaryItems = await loadSecondary(preselectedCost);
            populateSelect(secondarySelect, secondaryItems, "id", "name", "Välj sekundärt");
        }

        costSelect.addEventListener("change", async function () {

            const selectedCost = this.value;

            populateSelect(secondarySelect, [], "id", "name", "Laddar...");
            populateSelect(budgetSelect, [], "id", "name", "Välj budgetrad");

            if (!selectedCost) return;

            const secondaryItems = await loadSecondary(selectedCost);
            populateSelect(secondarySelect, secondaryItems, "id", "name", "Välj sekundärt");
        });

        secondarySelect.addEventListener("change", async function () {

            const selectedSecondary = this.value;

            populateSelect(budgetSelect, [], "id", "name", "Laddar...");

            if (!selectedSecondary) return;

            const budgetItems = await loadBudgetLines(selectedSecondary);
            populateSelect(budgetSelect, budgetItems, "id", "name", "Välj budgetrad");
        });
    }

    async function initializeAllRows() {
        const rows = document.querySelectorAll(".row");
        for (const row of rows) {
            await initializeRow(row);
        }
    }

    initializeAllRows();
});
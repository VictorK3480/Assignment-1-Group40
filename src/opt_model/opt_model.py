import gurobipy as gp
from gurobipy import GRB
from typing import Dict, Any, Iterable
from src.data_ops.data_loader import DataLoader1a, DataLoader1b, DataLoader1c, DataLoader2b

# Quiet Gurobi globally; allow per-model override if needed
gp.setParam("LogToConsole", 0)


class OptimizationModel1a:
    """Base model (1a): PV + imports/exports to meet daily demand, maximize profit."""

    def __init__(self, params: Dict[str, Any]):
        self.params = params
        self.model = gp.Model("Optimization1a")
        self.model.Params.LogToConsole = 0
        self.results: Dict[str, Any] = {}
        self._built = False  # tracks model build state

    def build_model(self) -> None:
        hours: Iterable[int] = self.params["hours"]
        pv = self.params["pv"]
        b = self.params["b"]
        s = self.params["s"]
        GE = self.params["GE"]
        GI = self.params["GI"]
        D = self.params["D"]

        # Decision variables (nonnegative)
        self.x = self.model.addVars(hours, name="x", lb=0)  # PV used
        self.y = self.model.addVars(hours, name="y", lb=0)  # imports
        self.z = self.model.addVars(hours, name="z", lb=0)  # exports

        # PV cap: PV used <= PV available
        self.PVcap = self.model.addConstrs((self.x[i] <= pv[i] for i in hours), name="PVcap")

        # Daily demand must be met in total
        self.DailyDemand = self.model.addConstr(
            gp.quicksum(self.x[i] + self.y[i] - self.z[i] for i in hours) >= D,
            name="DailyDemand",
        )

        # No net negative supply each hour (can't export more than PV at hour)
        self.HourlyBalance = self.model.addConstrs((self.x[i] - self.z[i] >= 0 for i in hours), name="HourlyBalance")

        # Operational bounds (kept generous to avoid infeasibility surprises)
        self.model.addConstrs((self.y[i] <= 1000 for i in hours), name="MaxImport")
        self.model.addConstrs((self.z[i] <= 500 for i in hours), name="MaxExport")

        # Maximize revenue from exports minus import costs
        self.model.setObjective(
            gp.quicksum(self.z[i] * (s[i] - GE) - self.y[i] * (b[i] + GI) for i in hours),
            GRB.MAXIMIZE,
        )

        self._built = True

    def run(self) -> None:
        # Build on first run
        if not self._built:
            self.build_model()
        self.model.optimize()
        self.results["status"] = int(self.model.status)  # keep status code for checks
        if self.model.status == GRB.OPTIMAL:
            self._save_results()

    def _save_results(self) -> None:
        hours = self.params["hours"]

        # Objective breakdown
        import_cost = sum(self.y[i].X * (self.params["b"][i] + self.params["GI"]) for i in hours)
        export_rev = sum(self.z[i].X * (self.params["s"][i] - self.params["GE"]) for i in hours)

        # Objective + breakdown
        self.results["objective"] = float(self.model.ObjVal)
        self.results["import_cost"] = import_cost
        self.results["export_revenue"] = export_rev
        self.results["net_profit"] = export_rev - import_cost

        # Hourly primals
        self.results["import"] = {i: self.y[i].X for i in hours}
        self.results["export"] = {i: self.z[i].X for i in hours}
        self.results["pv"] = {i: self.x[i].X for i in hours}
        self.results["demand_served"] = {i: self.x[i].X + self.y[i].X - self.z[i].X for i in hours}

        # Totals
        self.results["total_import"] = sum(self.results["import"].values())
        self.results["total_export"] = sum(self.results["export"].values())
        self.results["total_demand_served"] = sum(self.results["demand_served"].values())

        # Duals (shadow prices)
        self.results["dual_daily_demand"] = self.DailyDemand.Pi
        self.results["dual_hourly_balance"] = {i: self.HourlyBalance[i].Pi for i in hours}
        self.results["dual_pv_cap"] = {i: self.PVcap[i].Pi for i in hours}


class OptimizationModel1b:
    """Flexible load (1b): PV + grid with discomfort penalty, maximize profit - λ*deviation."""

    def __init__(self, params: Dict[str, Any]):
        self.params = params
        self.model = gp.Model("Optimization1b")
        self.model.Params.LogToConsole = 0
        self.results: Dict[str, Any] = {}
        self._built = False

    def build_model(self) -> None:
        hours = self.params["hours"]
        pv = self.params["pv"]
        b = self.params["b"]
        s = self.params["s"]
        GE = self.params["GE"]
        GI = self.params["GI"]
        ref_load = self.params["ref_load"]
        d_hour = self.params["d_hour"]
        lam = self.params["lambda_discomfort"]
        tol = self.params.get("tolerance", {i: 0.0 for i in hours})  # default no tolerance

        # Decision variables
        self.x = self.model.addVars(hours, name="x", lb=0)                    # PV used
        self.y = self.model.addVars(hours, name="y", lb=0)                    # imports
        self.z = self.model.addVars(hours, name="z", lb=0)                    # exports
        self.served = self.model.addVars(hours, name="served", lb=0, ub=d_hour)  # served flexible load
        self.u = self.model.addVars(hours, name="u", lb=0)                    # |served - ref_load| within tol
        self.l = self.model.addVars(hours, name="l", lb=0)                    # optional explicit flexible load (kept for API)

        # PV cap
        self.model.addConstrs((self.x[i] <= pv[i] for i in hours), name="PVcap")

        # Energy balance: served = PV + import - export
        self.model.addConstrs((self.served[i] == self.x[i] + self.y[i] - self.z[i] for i in hours), name="Balance")

        # Deviation with tolerance band
        self.model.addConstrs((self.u[i] >= self.served[i] - ref_load[i] - tol[i] for i in hours), name="Dev_pos")
        self.model.addConstrs((self.u[i] >= ref_load[i] - self.served[i] - tol[i] for i in hours), name="Dev_neg")

        # Maximize revenue - cost - discomfort
        self.model.setObjective(
            gp.quicksum(self.z[i] * (s[i] - GE) - self.y[i] * (b[i] + GI) - lam * self.u[i] for i in hours),
            GRB.MAXIMIZE,
        )

        self._built = True

    def run(self) -> None:
        if not self._built:
            self.build_model()
        self.model.optimize()
        self.results["status"] = int(self.model.status)
        if self.model.status == GRB.OPTIMAL:
            self._save_results()

    def _save_results(self) -> None:
        hours = self.params["hours"]

        import_cost = sum(self.y[i].X * (self.params["b"][i] + self.params["GI"]) for i in hours)
        export_rev = sum(self.z[i].X * (self.params["s"][i] - self.params["GE"]) for i in hours)
        discomfort = sum(self.params["lambda_discomfort"] * self.u[i].X for i in hours)

        self.results["objective"] = float(self.model.ObjVal)
        self.results["import_cost"] = import_cost
        self.results["export_revenue"] = export_rev
        self.results["discomfort_penalty"] = discomfort
        self.results["net_profit"] = export_rev - import_cost - discomfort

        # Hourly primals
        self.results["import"] = {i: self.y[i].X for i in hours}
        self.results["export"] = {i: self.z[i].X for i in hours}
        self.results["pv"] = {i: self.x[i].X for i in hours}
        self.results["served"] = {i: self.served[i].X for i in hours}
        self.results["deviation"] = {i: self.u[i].X for i in hours}
        self.results["reference_load"] = {i: self.params["ref_load"][i] for i in hours}

        # Totals
        self.results["total_import"] = sum(self.results["import"].values())
        self.results["total_export"] = sum(self.results["export"].values())
        self.results["total_served"] = sum(self.results["served"].values())
        self.results["total_deviation"] = sum(self.results["deviation"].values())

        # Duals
        get = self.model.getConstrByName
        self.results["dual_pv_cap"] = {i: get(f"PVcap[{i}]").Pi for i in hours}
        self.results["dual_balance"] = {i: get(f"Balance[{i}]").Pi for i in hours}
        self.results["dual_dev_pos"] = {i: get(f"Dev_pos[{i}]").Pi for i in hours}
        self.results["dual_dev_neg"] = {i: get(f"Dev_neg[{i}]").Pi for i in hours}


class OptimizationModel1c:
    """Flexible load + battery (1c): maximize profit - λ*deviation with storage dynamics."""

    def __init__(self, params: Dict[str, Any]):
        self.params = params
        self.model = gp.Model("Optimization1c")
        self.model.Params.LogToConsole = 0
        self.results: Dict[str, Any] = {}
        self._built = False

    def build_model(self) -> None:
        hours = self.params["hours"]
        pv = self.params["pv"]
        b = self.params["b"]
        s = self.params["s"]
        GE = self.params["GE"]
        GI = self.params["GI"]
        ref_load = self.params["ref_load"]
        d_hour = self.params["d_hour"]
        lam = self.params["lambda_discomfort"]

        # Battery params (normalize: storage and prefs may be lists)
        storage = (self.params["storage"][0] if isinstance(self.params["storage"], list) else self.params["storage"])
        prefs = (
            self.params["storage_preferences"][0]
            if isinstance(self.params["storage_preferences"], list)
            else self.params["storage_preferences"]
        )

        cap = storage["storage_capacity_kWh"]
        eta_c = storage["charging_efficiency"]
        eta_d = storage["discharging_efficiency"]
        p_ch_max = storage["max_charging_power_ratio"] * cap
        p_dis_max = storage["max_discharging_power_ratio"] * cap
        soc_init = prefs["initial_soc_ratio"] * cap
        soc_final = prefs["final_soc_ratio"] * cap

        # Decision variables
        self.x = self.model.addVars(hours, name="x", lb=0)                  # PV used
        self.y = self.model.addVars(hours, name="y", lb=0)                  # import
        self.z = self.model.addVars(hours, name="z", lb=0)                  # export
        self.served = self.model.addVars(hours, name="served", lb=0, ub=d_hour)
        self.u = self.model.addVars(hours, name="u", lb=0)                  # deviation
        self.l = self.model.addVars(hours, name="l", lb=0)                  # explicit flexible (kept for API)

        # Battery variables
        self.charge = self.model.addVars(hours, name="charge", lb=0, ub=p_ch_max)
        self.discharge = self.model.addVars(hours, name="discharge", lb=0, ub=p_dis_max)
        self.soc = self.model.addVars(hours, name="soc", lb=0, ub=cap)

        # PV cap
        self.model.addConstrs((self.x[i] <= pv[i] for i in hours), name="PVcap")

        # Energy balance: served = PV + import + discharge - export - charge
        self.model.addConstrs(
            (self.served[i] == self.x[i] + self.y[i] + self.discharge[i] - self.z[i] - self.charge[i] for i in hours),
            name="Balance",
        )

        # Deviation definition
        self.model.addConstrs((self.u[i] >= self.served[i] - ref_load[i] for i in hours), name="Dev_pos")
        self.model.addConstrs((self.u[i] >= ref_load[i] - self.served[i] for i in hours), name="Dev_neg")

        # SOC dynamics
        self.model.addConstr(
            self.soc[0] == soc_init + eta_c * self.charge[0] - (1 / eta_d) * self.discharge[0],
            name="SOC_init",
        )
        self.model.addConstrs(
            (
                self.soc[i] == self.soc[i - 1] + eta_c * self.charge[i] - (1 / eta_d) * self.discharge[i]
                for i in hours
                if i > 0
            ),
            name="SOC_dyn",
        )
        self.model.addConstr(self.soc[max(hours)] == soc_final, name="SOC_final")  # final SOC

        # Maximize profit minus discomfort
        self.model.setObjective(
            gp.quicksum(
                self.z[i] * (s[i] - GE) - self.y[i] * (b[i] + GI) - lam * self.u[i]  # rev - cost - discomfort
                for i in hours
            ),
            GRB.MAXIMIZE,
        )

        self._built = True

    def run(self) -> None:
        if not self._built:
            self.build_model()
        self.model.optimize()
        self.results["status"] = int(self.model.status)
        if self.model.status == GRB.OPTIMAL:
            self._save_results()

    def _save_results(self) -> None:
        hours = self.params["hours"]

        import_cost = sum(self.y[i].X * (self.params["b"][i] + self.params["GI"]) for i in hours)
        export_rev = sum(self.z[i].X * (self.params["s"][i] - self.params["GE"]) for i in hours)
        discomfort = sum(self.params["lambda_discomfort"] * self.u[i].X for i in hours)

        self.results["objective"] = float(self.model.ObjVal)
        self.results["import_cost"] = import_cost
        self.results["export_revenue"] = export_rev
        self.results["discomfort_penalty"] = discomfort
        self.results["net_profit"] = export_rev - import_cost - discomfort

        # Hourly primals
        self.results["import"] = {i: self.y[i].X for i in hours}
        self.results["export"] = {i: self.z[i].X for i in hours}
        self.results["pv"] = {i: self.x[i].X for i in hours}
        self.results["served"] = {i: self.served[i].X for i in hours}
        self.results["deviation"] = {i: self.u[i].X for i in hours}
        self.results["reference_load"] = {i: self.params["ref_load"][i] for i in hours}

        # Battery details
        self.results["charge"] = {i: self.charge[i].X for i in hours}
        self.results["discharge"] = {i: self.discharge[i].X for i in hours}
        self.results["soc"] = {i: self.soc[i].X for i in hours}

        # Totals
        self.results["total_import"] = sum(self.results["import"].values())
        self.results["total_export"] = sum(self.results["export"].values())
        self.results["total_served"] = sum(self.results["served"].values())
        self.results["total_deviation"] = sum(self.results["deviation"].values())
        self.results["total_charge"] = sum(self.results["charge"].values())
        self.results["total_discharge"] = sum(self.results["discharge"].values())

        # Self-consumption: PV used to serve load (bounded by each)
        self.results["self_consumption"] = sum(min(self.results["pv"][i], self.results["served"][i]) for i in hours)

        # Duals
        get = self.model.getConstrByName
        self.results["dual_pv_cap"] = {i: get(f"PVcap[{i}]").Pi for i in hours}
        self.results["dual_balance"] = {i: get(f"Balance[{i}]").Pi for i in hours}
        self.results["dual_soc_dyn"] = {i: get(f"SOC_dyn[{i}]").Pi for i in hours if i > 0}
        self.results["dual_soc_init"] = get("SOC_init").Pi if get("SOC_init") else None
        self.results["dual_soc_final"] = get("SOC_final").Pi if get("SOC_final") else None





class OptimizationModel2b:
    """Flexible load + option of battery (2b): maximize profit - λ*deviation with storage dynamics."""

    def __init__(self, params: Dict[str, Any]):
        self.params = params
        self.model = gp.Model("Optimization2b")
        self.model.Params.LogToConsole = 0
        self.results: Dict[str, Any] = {}
        self._built = False

    def build_model(self) -> None:
        hours = self.params["hours"]
        pv = self.params["pv"]
        b = self.params["b"]
        s = self.params["s"]
        GE = self.params["GE"]
        GI = self.params["GI"]
        ref_load = self.params["ref_load"]
        d_hour = self.params["d_hour"]
        lam = self.params["lambda_discomfort"]

        # Battery params (normalize: storage and prefs may be lists)
        storage = (self.params["storage"][0] if isinstance(self.params["storage"], list) else self.params["storage"])
        prefs = (
            self.params["storage_preferences"][0]
            if isinstance(self.params["storage_preferences"], list)
            else self.params["storage_preferences"]
        )

        cap = storage["storage_capacity_kWh"]
        eta_c = storage["charging_efficiency"]
        eta_d = storage["discharging_efficiency"]
        p_ch_max = storage["max_charging_power_ratio"] * cap
        p_dis_max = storage["max_discharging_power_ratio"] * cap
        soc_init = prefs["initial_soc_ratio"] 
        soc_final = prefs["final_soc_ratio"]

        # Battery parameters
        T_max = storage["battery_lifetime_yrs"] * 365 * 24  # hours in lifetime (10 years)
        Bat_cost = storage["battery_cost_per_kWh"]  # DKK per kWh of capacity (value set to 150 in data)

        # Decision variables
        self.x = self.model.addVars(hours, name="x", lb=0)                  # PV used
        self.y = self.model.addVars(hours, name="y", lb=0)                  # import
        self.z = self.model.addVars(hours, name="z", lb=0)                  # export
        self.served = self.model.addVars(hours, name="served", lb=0, ub=d_hour)
        self.u = self.model.addVars(hours, name="u", lb=0)                  # deviation
        self.l = self.model.addVars(hours, name="l", lb=0)                  # explicit flexible (kept for API)

        # Battery variables
        self.charge = self.model.addVars(hours, name="charge", lb=0)
        self.discharge = self.model.addVars(hours, name="discharge", lb=0)
        self.soc = self.model.addVars(hours, name="soc", lb=0)

        # Additional battery investment scaling variable
        self.Bat_scale = self.model.addVar(name="Bat_scale", lb=0)
        self.Bat_cutoff = self.model.addVars(hours, lb=0, ub=1, name="Bat_cutoff")

        # PV cap
        self.model.addConstrs((self.x[i] <= pv[i] for i in hours), name="PVcap")

        # Energy balance: served = PV + import + discharge - export - charge
        self.model.addConstrs(
            (self.served[i] == self.x[i] + self.y[i] + self.discharge[i] - self.z[i] - self.charge[i] for i in hours),
            name="Balance",
        )

        # Deviation definition
        self.model.addConstrs((self.u[i] >= self.served[i] - ref_load[i] for i in hours), name="Dev_pos")
        self.model.addConstrs((self.u[i] >= ref_load[i] - self.served[i] for i in hours), name="Dev_neg")

        # SOC dynamics
        self.model.addConstr(
            self.soc[0] == (soc_init * cap * self.Bat_scale) + eta_c * self.charge[0] - (1 / eta_d) * self.discharge[0],
            name="SOC_init",
        )
        self.model.addConstrs(
            (
                self.soc[i] == self.soc[i - 1] + eta_c * self.charge[i] - (1 / eta_d) * self.discharge[i]
                for i in hours
                if i > 0
            ),
            name="SOC_dyn",
        )

        # Battery characteristics scaling constraints
        self.model.addConstr(self.soc[max(hours)] == soc_final *cap * self.Bat_scale, name="SOC_final")  # final SOC

        # New SOC upper bound scaling with investment
        self.model.addConstrs((self.soc[i] <= cap * self.Bat_scale for i in hours), name="SOC_cap")
        self.model.addConstrs((self.charge[i] <= p_ch_max * self.Bat_scale for i in hours), name="Charge_cap")
        self.model.addConstrs((self.discharge[i] <= p_dis_max * self.Bat_scale for i in hours), name="Discharge_cap")

        # Battery turnoff constraint after T_max is hit
        self.model.addConstrs((self.Bat_cutoff[i]*i <= T_max for i in hours), name="Battery_turnoff")

        # Maximize profit minus discomfort
        self.model.setObjective((
            gp.quicksum(
                self.z[i] * (s[i] - GE) - self.y[i] * (b[i] + GI) - lam * self.u[i]  # rev - cost - discomfort
                for i in hours
            ) - Bat_cost * cap * self.Bat_scale), # subtracting battery cost
            GRB.MAXIMIZE,
        )

        self._built = True

    def run(self) -> None:
        if not self._built:
            self.build_model()
        self.model.optimize()
        self.results["status"] = int(self.model.status)
        if self.model.status == GRB.OPTIMAL:
            self._save_results()

    def _save_results(self) -> None:
        hours = self.params["hours"]

        import_cost = sum(self.y[i].X * (self.params["b"][i] + self.params["GI"]) for i in hours)
        export_rev = sum(self.z[i].X * (self.params["s"][i] - self.params["GE"]) for i in hours)
        discomfort = sum(self.params["lambda_discomfort"] * self.u[i].X for i in hours)
        battery_cost = self.params["storage"][0]["battery_cost_per_kWh"] * self.params["storage"][0]["storage_capacity_kWh"] * self.Bat_scale.X
        battery_scale = self.Bat_scale.X

        self.results["objective"] = float(self.model.ObjVal)
        self.results["import_cost"] = import_cost
        self.results["export_revenue"] = export_rev
        self.results["discomfort_penalty"] = discomfort
        self.results["battery_cost"] = battery_cost
        self.results["net_profit"] = export_rev - import_cost - discomfort - battery_cost

        # Hourly primals
        self.results["import"] = {i: self.y[i].X for i in hours}
        self.results["export"] = {i: self.z[i].X for i in hours}
        self.results["pv"] = {i: self.x[i].X for i in hours}
        self.results["served"] = {i: self.served[i].X for i in hours}
        self.results["deviation"] = {i: self.u[i].X for i in hours}
        self.results["reference_load"] = {i: self.params["ref_load"][i] for i in hours}

        # Battery details
        self.results["charge"] = {i: self.charge[i].X for i in hours}
        self.results["discharge"] = {i: self.discharge[i].X for i in hours}
        self.results["soc"] = {i: self.soc[i].X for i in hours}
        self.results["battery_scale"] = self.Bat_scale.X
        
        # Battery scaling factor
        self.results["battery_scale"] = battery_scale

        # Totals
        self.results["total_import"] = sum(self.results["import"].values())
        self.results["total_export"] = sum(self.results["export"].values())
        self.results["total_served"] = sum(self.results["served"].values())
        self.results["total_deviation"] = sum(self.results["deviation"].values())
        self.results["total_charge"] = sum(self.results["charge"].values())
        self.results["total_discharge"] = sum(self.results["discharge"].values())

        # Self-consumption: PV used to serve load (bounded by each)
        self.results["self_consumption"] = sum(min(self.results["pv"][i], self.results["served"][i]) for i in hours)

        # Duals
        get = self.model.getConstrByName
        self.results["dual_pv_cap"] = {i: get(f"PVcap[{i}]").Pi for i in hours}
        self.results["dual_balance"] = {i: get(f"Balance[{i}]").Pi for i in hours}
        self.results["dual_soc_dyn"] = {i: get(f"SOC_dyn[{i}]").Pi for i in hours if i > 0}
        self.results["dual_soc_init"] = get("SOC_init").Pi if get("SOC_init") else None
        self.results["dual_soc_final"] = get("SOC_final").Pi if get("SOC_final") else None
        self.results["dual_dev_pos"] = {i: get(f"Dev_pos[{i}]").Pi for i in hours}
        self.results["dual_dev_neg"] = {i: get(f"Dev_neg[{i}]").Pi for i in hours}
        self.results["dual_soc_cap"] = {i: get(f"SOC_cap[{i}]").Pi for i in hours}
        self.results["dual_charge_cap"] = {i: get(f"Charge_cap[{i}]").Pi for i in hours}
        self.results["dual_discharge_cap"] = {i: get(f"Discharge_cap[{i}]").Pi for i in hours}


# ---- SWEEP FUNCTIONS (1c) ----
# For sensitivity analysis on 1c

def sweep_GE_1c(GE: float, lambda_discomfort: float = 1.5) -> Dict[str, Any]:
    loader = DataLoader1c()
    DER_prod = loader.load_der_production()
    app_params = loader.load_appliance_params()
    bus_params = loader.load_bus_params()
    usage = loader.load_usage_preferences()

    hours = range(len(DER_prod))
    PV_capacity = app_params["DER"][0]["max_power_kW"]
    pv = {i: PV_capacity * DER_prod[i] for i in hours}

    b = {i: bus_params["energy_price_DKK_per_kWh"][i] for i in hours}
    s = b.copy()  # parity
    GI = bus_params["import_tariff_DKK/kWh"]

    ratios = usage["load_preferences"][0]["hourly_profile_ratio"]
    d_hour = app_params["load"][0]["max_load_kWh_per_hour"]
    ref_load = {i: d_hour * ratios[i] for i in hours}

    storage = app_params["storage"]
    prefs = usage["storage_preferences"]

    params = {
        "hours": hours,
        "pv": pv,
        "b": b,
        "s": s,
        "GE": GE,
        "GI": GI,
        "ref_load": ref_load,
        "d_hour": d_hour,
        "lambda_discomfort": lambda_discomfort,
        "storage": storage,
        "storage_preferences": prefs,
    }

    model = OptimizationModel1c(params)
    model.run()
    res = model.results.copy()
    res["GE"] = GE
    return res


def sweep_buying_factor_1c(factor: float, lambda_discomfort: float = 1.5) -> Dict[str, Any]:
    loader = DataLoader1c()
    DER_prod = loader.load_der_production()
    app_params = loader.load_appliance_params()
    bus_params = loader.load_bus_params()
    usage = loader.load_usage_preferences()

    hours = range(len(DER_prod))
    PV_capacity = app_params["DER"][0]["max_power_kW"]
    pv = {i: PV_capacity * DER_prod[i] for i in hours}

    s = {i: bus_params["energy_price_DKK_per_kWh"][i] for i in hours}
    b = {i: factor * s[i] for i in hours}  # buying price scaled by factor
    GI = bus_params["import_tariff_DKK/kWh"]
    GE = bus_params["export_tariff_DKK/kWh"]

    ratios = usage["load_preferences"][0]["hourly_profile_ratio"]
    d_hour = app_params["load"][0]["max_load_kWh_per_hour"]
    ref_load = {i: d_hour * ratios[i] for i in hours}

    storage = app_params["storage"]
    prefs = usage["storage_preferences"]

    params = {
        "hours": hours,
        "pv": pv,
        "b": b,
        "s": s,
        "GE": GE,
        "GI": GI,
        "ref_load": ref_load,
        "d_hour": d_hour,
        "lambda_discomfort": lambda_discomfort,
        "storage": storage,
        "storage_preferences": prefs,
    }

    model = OptimizationModel1c(params)
    model.run()
    res = model.results.copy()
    res["factor"] = factor
    return res


def sweep_omega_1c(lambda_discomfort: float, GE: float = 0.4) -> Dict[str, Any]:
    loader = DataLoader1c()
    DER_prod = loader.load_der_production()
    app_params = loader.load_appliance_params()
    bus_params = loader.load_bus_params()
    usage = loader.load_usage_preferences()

    hours = range(len(DER_prod))
    PV_capacity = app_params["DER"][0]["max_power_kW"]
    pv = {i: PV_capacity * DER_prod[i] for i in hours}

    b = {i: bus_params["energy_price_DKK_per_kWh"][i] for i in hours}
    s = b.copy()
    GI = bus_params["import_tariff_DKK/kWh"]

    ratios = usage["load_preferences"][0]["hourly_profile_ratio"]
    d_hour = app_params["load"][0]["max_load_kWh_per_hour"]
    ref_load = {i: d_hour * ratios[i] for i in hours}

    storage = app_params["storage"]
    prefs = usage["storage_preferences"]

    params = {
        "hours": hours,
        "pv": pv,
        "b": b,
        "s": s,
        "GE": GE,
        "GI": GI,
        "ref_load": ref_load,
        "d_hour": d_hour,
        "lambda_discomfort": lambda_discomfort,
        "storage": storage,
        "storage_preferences": prefs,
    }

    model = OptimizationModel1c(params)
    model.run()
    res = model.results.copy()
    res["omega"] = lambda_discomfort
    return res


def sweep_tolerance_1c(tolerance_ratio: float, lambda_discomfort: float = 1.5, GE: float = 0.4) -> Dict[str, Any]:
    loader = DataLoader1c()
    DER_prod = loader.load_der_production()
    app_params = loader.load_appliance_params()
    bus_params = loader.load_bus_params()
    usage = loader.load_usage_preferences()

    hours = range(len(DER_prod))
    PV_capacity = app_params["DER"][0]["max_power_kW"]
    pv = {i: PV_capacity * DER_prod[i] for i in hours}

    b = {i: bus_params["energy_price_DKK_per_kWh"][i] for i in hours}
    s = b.copy()
    GI = bus_params["import_tariff_DKK/kWh"]

    ratios = usage["load_preferences"][0]["hourly_profile_ratio"]
    d_hour = app_params["load"][0]["max_load_kWh_per_hour"]
    ref_load = {i: d_hour * ratios[i] for i in hours}
    tol = {i: tolerance_ratio * ref_load[i] for i in hours}

    storage = app_params["storage"]
    prefs = usage["storage_preferences"]

    params = {
        "hours": hours,
        "pv": pv,
        "b": b,
        "s": s,
        "GE": GE,
        "GI": GI,
        "ref_load": ref_load,
        "d_hour": d_hour,
        "lambda_discomfort": lambda_discomfort,
        "tolerance": tol,
        "storage": storage,
        "storage_preferences": prefs,
    }

    model = OptimizationModel1c(params)
    model.run()
    res = model.results.copy()
    res["tolerance_ratio"] = tolerance_ratio
    return res


# ------- 2b SWEEP FUNCTIONS -------
# For sensitivity analysis on 2b

def sweep_omega_2b(lambda_discomfort: float, GE: float = 0.4) -> Dict[str, Any]:
    loader = DataLoader2b()
    DER_prod = loader.load_der_production()
    app_params = loader.load_appliance_params()
    bus_params = loader.load_bus_params()
    usage = loader.load_usage_preferences()

    hours = range(len(DER_prod))
    PV_capacity = app_params["DER"][0]["max_power_kW"]
    pv = {i: PV_capacity * DER_prod[i] for i in hours}

    b = {i: bus_params["energy_price_DKK_per_kWh"][i] for i in hours}
    s = b.copy()
    GI = bus_params["import_tariff_DKK/kWh"]

    ratios = usage["load_preferences"][0]["hourly_profile_ratio"]
    d_hour = app_params["load"][0]["max_load_kWh_per_hour"]
    ref_load = {i: d_hour * ratios[i] for i in hours}

    storage = app_params["storage"]
    prefs = usage["storage_preferences"]

    params = {
        "hours": hours,
        "pv": pv,
        "b": b,
        "s": s,
        "GE": GE,
        "GI": GI,
        "ref_load": ref_load,
        "d_hour": d_hour,
        "lambda_discomfort": lambda_discomfort,
        "storage": storage,
        "storage_preferences": prefs,
    }

    model = OptimizationModel2b(params)
    model.run()
    res = model.results.copy()
    res["omega"] = lambda_discomfort
    return res


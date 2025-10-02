import gurobipy as gp
from gurobipy import GRB
gp.setParam('LogToConsole', 0)

class OptimizationModel1a:
    def __init__(self, params):
        self.params = params
        self.model = gp.Model("Optimization1a")
        self.model.Params.LogToConsole = 0
        self.results = {}
        self._built = False   # track whether model is built

    def build_model(self):
        hours = self.params["hours"]
        pv = self.params["pv"]
        b = self.params["b"]
        s = self.params["s"]
        GE = self.params["GE"]
        GI = self.params["GI"]
        D = self.params["D"]


        # Variables
        self.x = self.model.addVars(hours, name="x", lb=0)  # PV production
        self.y = self.model.addVars(hours, name="y", lb=0)  # imports
        self.z = self.model.addVars(hours, name="z", lb=0)  # exports

        # Constraints 
        self.PVcap = self.model.addConstrs(
            (self.x[i] <= pv[i] for i in hours), name="PVcap"
        )

        self.DailyDemand = self.model.addConstr(
            gp.quicksum(self.x[i] + self.y[i] - self.z[i] for i in hours) >= D,
            name="DailyDemand",
        )

        self.HourlyBalance = self.model.addConstrs(
            (self.x[i] - self.z[i] >= 0 for i in hours),
            name="HourlyBalance",
        )

        self.model.addConstrs((self.y[i] <= 1000 for i in hours), name="MaxImport") 
        self.model.addConstrs((self.z[i] <= 500 for i in hours), name="MaxExport") 

        # Objective 
        self.model.setObjective(
            gp.quicksum(
                self.z[i] * (s[i] - GE) - self.y[i] * (b[i] + GI)
                for i in hours
            ),
            GRB.MAXIMIZE,
        )

        self._built = True  # mark model as built

    def run(self):
        if not self._built:
            self.build_model()   # ensure model is built before running
        self.model.optimize()
        if self.model.status == GRB.OPTIMAL:
            self._save_results()
        else:
            print("Optimization was not successful. Status:", self.model.status)

    def _save_results(self):
        hours = self.params["hours"]

        # Objective components
        import_cost = sum(self.y[i].x * (self.params["b"][i] + self.params["GI"]) for i in hours)
        export_rev  = sum(self.z[i].x * (self.params["s"][i] - self.params["GE"]) for i in hours)

        # Objective + breakdown
        self.results["objective"] = self.model.ObjVal
        self.results["import_cost"] = import_cost
        self.results["export_revenue"] = export_rev
        self.results["net_profit"] = export_rev - import_cost

        # Hourly primal values
        self.results["import"] = {i: self.y[i].x for i in hours}
        self.results["export"] = {i: self.z[i].x for i in hours}
        self.results["pv"]     = {i: self.x[i].x for i in hours}
        self.results["demand_served"] = {
            i: self.x[i].x + self.y[i].x - self.z[i].x for i in hours
        }

        # Totals
        self.results["total_import"] = sum(self.results["import"].values())
        self.results["total_export"] = sum(self.results["export"].values())
        self.results["total_demand_served"] = sum(self.results["demand_served"].values())

        # Dual values
        self.results["dual_daily_demand"] = self.DailyDemand.Pi
        self.results["dual_hourly_balance"] = {i: self.HourlyBalance[i].Pi for i in hours}
        self.results["dual_pv_cap"] = {i: self.PVcap[i].Pi for i in hours}



class OptimizationModel1b:
    """Flexible load: minimize energy costs + discomfort from deviation (Question 1b)."""
    def __init__(self, params):
        self.params = params
        self.model = gp.Model("Optimization1b")
        self.model.Params.LogToConsole = 0
        self.results = {}

    def build_model(self):
        hours = self.params["hours"]
        pv = self.params["pv"]
        b = self.params["b"]
        s = self.params["s"]
        GE = self.params["GE"]
        GI = self.params["GI"]
        ref_load = self.params["ref_load"]
        d_hour = self.params["d_hour"]
        lam = self.params["lambda_discomfort"]

        # Variables
        self.x = self.model.addVars(hours, name="x", lb=0)        # PV
        self.y = self.model.addVars(hours, name="y", lb=0)        # import
        self.z = self.model.addVars(hours, name="z", lb=0)        # export
        self.served = self.model.addVars(hours, name="served", lb=0, ub=d_hour)
        self.u = self.model.addVars(hours, name="u", lb=0)        # deviation
        # Decision variable: flexible load served at each hour
        self.l = self.model.addVars(hours, name="l", lb=0)

        # Constraints
        self.model.addConstrs((self.x[i] <= pv[i] for i in hours), name="PVcap")
        self.model.addConstrs(
            (self.served[i] == self.x[i] + self.y[i] - self.z[i] for i in hours),
            name="Balance",
        )
        tol = self.params.get("tolerance", {i: 0.0 for i in hours})  # default = 0 (original behavior)

        self.model.addConstrs(
            (self.u[i] >= self.served[i] - ref_load[i] - tol[i] for i in hours),
            name="Dev_pos"
        )
        self.model.addConstrs(
            (self.u[i] >= ref_load[i] - self.served[i] - tol[i] for i in hours),
            name="Dev_neg"
)

        #self.model.addConstrs((self.y[i] <= 0 for i in hours), name="MaxImport") # assuming max_import is defined elsewhere

        # Objective: minimize cost + discomfort
        self.model.setObjective(
            gp.quicksum( self.z[i] * (s[i] - GE) - self.y[i] * (b[i] + GI) - lam * (self.u[i]) for i in hours),
            GRB.MAXIMIZE,
        )

    def run(self):
        self.build_model()
        self.model.optimize()
        if self.model.status == GRB.OPTIMAL:
            self._save_results()

    def _save_results(self):
        hours = self.params["hours"]

        # Objective components
        import_cost = sum(self.y[i].x * (self.params["b"][i] + self.params["GI"]) for i in hours)
        export_rev  = sum(self.z[i].x * (self.params["s"][i] - self.params["GE"]) for i in hours)
        discomfort  = sum(self.params["lambda_discomfort"] * self.u[i].x for i in hours)

        # Objective + breakdown
        self.results["objective"] = self.model.ObjVal
        self.results["import_cost"] = import_cost
        self.results["export_revenue"] = export_rev
        self.results["discomfort_penalty"] = discomfort
        self.results["net_profit"] = export_rev - import_cost - discomfort

        # Hourly primal values
        self.results["import"]   = {i: self.y[i].x for i in hours}
        self.results["export"]   = {i: self.z[i].x for i in hours}
        self.results["pv"]       = {i: self.x[i].x for i in hours}
        self.results["served"]   = {i: self.served[i].x for i in hours}
        self.results["deviation"]= {i: self.u[i].x for i in hours}
        self.results["reference_load"] = {i: self.params["ref_load"][i] for i in hours}

        # Totals
        self.results["total_import"] = sum(self.results["import"].values())
        self.results["total_export"] = sum(self.results["export"].values())
        self.results["total_served"] = sum(self.results["served"].values())
        self.results["total_deviation"] = sum(self.results["deviation"].values())

        # Duals
        get = self.model.getConstrByName
        self.results["dual_pv_cap"]  = {i: get(f"PVcap[{i}]").Pi for i in hours}
        self.results["dual_balance"] = {i: get(f"Balance[{i}]").Pi for i in hours}



class OptimizationModel1c:
    """Flexible load + battery: minimize energy costs + discomfort (extension of 1b)."""
    def __init__(self, params):
        self.params = params
        self.model = gp.Model("Optimization1c")
        self.model.Params.LogToConsole = 0
        self.results = {}

    def build_model(self):
        hours = self.params["hours"]
        pv = self.params["pv"]
        b = self.params["b"]
        s = self.params["s"]
        GE = self.params["GE"]
        GI = self.params["GI"]
        ref_load = self.params["ref_load"]
        d_hour = self.params["d_hour"]
        lam = self.params["lambda_discomfort"]

        # Battery parameters
        storage = self.params["storage"][0]
        prefs = self.params["storage_preferences"][0]
        cap = storage["storage_capacity_kWh"]
        eta_c = storage["charging_efficiency"]
        eta_d = storage["discharging_efficiency"]
        p_ch_max = storage["max_charging_power_ratio"] * cap
        p_dis_max = storage["max_discharging_power_ratio"] * cap
        soc_init = prefs["initial_soc_ratio"] * cap
        soc_final = prefs["final_soc_ratio"] * cap

        # Variables
        self.x = self.model.addVars(hours, name="x", lb=0)        # PV used
        self.y = self.model.addVars(hours, name="y", lb=0)        # import
        self.z = self.model.addVars(hours, name="z", lb=0)        # export
        self.served = self.model.addVars(hours, name="served", lb=0, ub=d_hour)
        self.u = self.model.addVars(hours, name="u", lb=0)        # deviation
        self.l = self.model.addVars(hours, name="l", lb=0)        # flexible load (explicit, not used yet)

        # Battery variables
        self.charge = self.model.addVars(hours, name="charge", lb=0, ub=p_ch_max)
        self.discharge = self.model.addVars(hours, name="discharge", lb=0, ub=p_dis_max)
        self.soc = self.model.addVars(hours, name="soc", lb=0, ub=cap)

        # Constraints
        # PV cap
        self.model.addConstrs((self.x[i] <= pv[i] for i in hours), name="PVcap")

        # Energy balance (served load = imports + PV + discharge - exports - charge)
        self.model.addConstrs(
            (self.served[i] == self.x[i] + self.y[i] + self.discharge[i] 
             - self.z[i] - self.charge[i] for i in hours),
            name="Balance",
        )

        # Deviation definition
        self.model.addConstrs((self.u[i] >= self.served[i] - ref_load[i] for i in hours), name="Dev_pos")
        self.model.addConstrs((self.u[i] >= ref_load[i] - self.served[i] for i in hours), name="Dev_neg")

        # Battery SOC dynamics
        self.model.addConstr(
            self.soc[0] == soc_init + eta_c * self.charge[0] - (1/eta_d) * self.discharge[0],
            name="SOC_init"
        )
        self.model.addConstrs(
            (self.soc[i] == self.soc[i-1] + eta_c * self.charge[i] - (1/eta_d) * self.discharge[i]
             for i in hours if i > 0),
            name="SOC_dyn"
        )

        # Final SOC requirement
        self.model.addConstr(self.soc[hours[-1]] == soc_final, name="SOC_final")

        # Objective: maximize profit - discomfort
        self.model.setObjective(
            gp.quicksum(
                self.z[i] * (s[i] - GE)        # revenue from selling
                - self.y[i] * (b[i] + GI)      # cost of imports
                - lam * self.u[i]              # discomfort penalty
                for i in hours
            ),
            GRB.MAXIMIZE,
        )

    def run(self):
        self.build_model()
        self.model.optimize()
        if self.model.status == GRB.OPTIMAL:
            self._save_results()

    def _save_results(self):
        hours = self.params["hours"]

        # Objective components
        import_cost = sum(self.y[i].x * (self.params["b"][i] + self.params["GI"]) for i in hours)
        export_rev  = sum(self.z[i].x * (self.params["s"][i] - self.params["GE"]) for i in hours)
        discomfort  = sum(self.params["lambda_discomfort"] * self.u[i].x for i in hours)

        # Objective + breakdown
        self.results["objective"] = self.model.ObjVal
        self.results["import_cost"] = import_cost
        self.results["export_revenue"] = export_rev
        self.results["discomfort_penalty"] = discomfort
        self.results["net_profit"] = export_rev - import_cost - discomfort

        # Hourly primal values
        self.results["import"]   = {i: self.y[i].x for i in hours}
        self.results["export"]   = {i: self.z[i].x for i in hours}
        self.results["pv"]       = {i: self.x[i].x for i in hours}
        self.results["served"]   = {i: self.served[i].x for i in hours}
        self.results["deviation"]= {i: self.u[i].x for i in hours}
        self.results["reference_load"] = {i: self.params["ref_load"][i] for i in hours}

        # Battery variables
        self.results["charge"]   = {i: self.charge[i].x for i in hours}
        self.results["discharge"]= {i: self.discharge[i].x for i in hours}
        self.results["soc"]      = {i: self.soc[i].x for i in hours}

        # Totals
        self.results["total_import"] = sum(self.results["import"].values())
        self.results["total_export"] = sum(self.results["export"].values())
        self.results["total_served"] = sum(self.results["served"].values())
        self.results["total_deviation"] = sum(self.results["deviation"].values())
        self.results["total_charge"] = sum(self.results["charge"].values())
        self.results["total_discharge"] = sum(self.results["discharge"].values())

        # Self-consumption KPI
        self.results["self_consumption"] = sum(
            min(self.results["pv"][i], self.results["served"][i]) for i in hours
        )

        # Duals
        get = self.model.getConstrByName
        self.results["dual_pv_cap"]  = {i: get(f"PVcap[{i}]").Pi for i in hours}
        self.results["dual_balance"] = {i: get(f"Balance[{i}]").Pi for i in hours}
        self.results["dual_soc_dyn"] = {i: get(f"SOC_dyn[{i}]").Pi for i in hours if i > 0}
        self.results["dual_soc_init"]= get("SOC_init").Pi if get("SOC_init") else None
        self.results["dual_soc_final"]= get("SOC_final").Pi if get("SOC_final") else None


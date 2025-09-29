import gurobipy as gp
from gurobipy import GRB

class OptimizationModel1a:
    def __init__(self, params):
        self.params = params
        self.model = gp.Model("Optimization1a")
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
            (self.x[i] + self.y[i] - self.z[i] >= 0 for i in hours),
            name="HourlyBalance",
        )

        self.model.addConstrs((self.y[i] <= 1000 for i in hours), name="MaxImport") # assuming max_import is defined elsewhere
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

        # Primal values
        self.results["objective"] = self.model.ObjVal
        self.results["demand_served"] = {
            i: self.x[i].x + self.y[i].x - self.z[i].x for i in hours
        }
        self.results["import"] = {i: self.y[i].x for i in hours}
        self.results["export"] = {i: self.z[i].x for i in hours}
        self.results["pv"] = {i: self.x[i].x for i in hours}
        self.results["total_demand"] = sum(self.results["demand_served"].values())

        # Dual values (shadow prices) 
        self.results["dual_daily_demand"] = self.DailyDemand.Pi
        self.results["dual_hourly_balance"] = {i: self.HourlyBalance[i].Pi for i in hours}
        self.results["dual_pv_cap"] = {i: self.PVcap[i].Pi for i in hours}


class OptimizationModel1b:
    """Flexible load: minimize energy costs + discomfort from deviation (Question 1b)."""
    def __init__(self, params):
        self.params = params
        self.model = gp.Model("Optimization1b")
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
        self.model.addConstrs((self.u[i] >= self.served[i] - ref_load[i] for i in hours), name="Dev_pos")
        self.model.addConstrs((self.u[i] >= ref_load[i] - self.served[i] for i in hours), name="Dev_neg")

        # Objective: minimize cost + discomfort
        self.model.setObjective(
            gp.quicksum(self.y[i] * (b[i] + GI) - self.z[i] * (s[i] - GE) for i in hours)
            + lam * gp.quicksum(self.u[i] for i in hours),
            GRB.MINIMIZE,
        )

    def run(self):
        self.build_model()
        self.model.optimize()
        if self.model.status == GRB.OPTIMAL:
            self._save_results()

    def _save_results(self):
        hours = self.params["hours"]
        self.results["objective"] = self.model.ObjVal
        self.results["import"] = {i: self.y[i].x for i in hours}
        self.results["export"] = {i: self.z[i].x for i in hours}
        self.results["pv"] = {i: self.x[i].x for i in hours}
        self.results["served"] = {i: self.served[i].x for i in hours}
        self.results["deviation"] = {i: self.u[i].x for i in hours}
        self.results["ref_load"] = self.params["ref_load"]  # pass reference for plotting
        self.results["flexible_load"] = {i: self.l[i].x for i in hours}
        ref_load = self.params["ref_load"]   # grab it back from params
        self.results["reference_load"] = {i: ref_load[i] for i in hours}

        

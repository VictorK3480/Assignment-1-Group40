from src.data_ops.data_loader import DataLoader1a, DataLoader1b, DataLoader1c
from src.opt_model.opt_model import OptimizationModel1a, OptimizationModel1b, OptimizationModel1c

# Base run 
def run_optimization_1a(scenario=None):
    loader = DataLoader1a()
    DER_prod = loader.load_der_production()
    app_params = loader.load_appliance_params()
    bus_params = loader.load_bus_params()
    usage = loader.load_usage_preferences()

    hours = range(len(DER_prod))
    PV_capacity = app_params["DER"][0]["max_power_kW"]
    pv = {i: PV_capacity * DER_prod[i] for i in hours}
    b_list = bus_params["energy_price_DKK_per_kWh"]
    s_list = b_list.copy()  # start with parity

    GI = bus_params["import_tariff_DKK/kWh"]
    GE = bus_params["export_tariff_DKK/kWh"]   # stays at base value here
    D = usage["load_preferences"][0]["min_total_energy_per_day_hour_equivalent"]

    # You can still allow scenario tweaks if you want
    if scenario:
        if "GI" in scenario: GI = scenario["GI"]
        if "GE" in scenario: GE = scenario["GE"]

    params = {
        "hours": hours,
        "pv": pv,
        "b": {i: b_list[i] for i in hours},
        "s": {i: s_list[i] for i in hours},
        "GI": GI,
        "GE": GE,
        "D": D,
    }

    opt = OptimizationModel1a(params)
    opt.run()
    return opt.results


# Export tariff sweep 
def run_export_tariff_sweep(start=0.0, stop=2.6, step=0.1):
    loader = DataLoader1a()
    DER_prod = loader.load_der_production()
    app_params = loader.load_appliance_params()
    bus_params = loader.load_bus_params()
    usage = loader.load_usage_preferences()

    hours = range(len(DER_prod))
    PV_capacity = app_params["DER"][0]["max_power_kW"]
    pv = {i: PV_capacity * DER_prod[i] for i in hours}
    b_list = bus_params["energy_price_DKK_per_kWh"]
    s_list = b_list.copy()
    GI = bus_params["import_tariff_DKK/kWh"]
    D = usage["load_preferences"][0]["min_total_energy_per_day_hour_equivalent"]

    results_all = []

    ge = start
    while ge <= stop + 1e-9:  # safeguard
        params = {
            "hours": hours,
            "pv": pv,
            "b": {i: b_list[i] for i in hours},
            "s": {i: s_list[i] for i in hours},
            "GI": GI,
            "GE": ge,
            "D": D,
        }
        model = OptimizationModel1a(params)
        model.run()
        res = model.results.copy()   # <- copy!
        res["GE"] = round(ge, 2)
        results_all.append(res)
        ge += step

    return results_all

def run_buying_price_sweep():
    loader = DataLoader1a()
    DER_prod = loader.load_der_production()
    app_params = loader.load_appliance_params()
    bus_params = loader.load_bus_params()
    usage = loader.load_usage_preferences()

    # Parameters
    hours = range(len(DER_prod))
    PV_capacity = app_params["DER"][0]["max_power_kW"]
    pv = {i: PV_capacity * DER_prod[i] for i in hours}
    s = {i: bus_params["energy_price_DKK_per_kWh"][i] for i in hours}  # selling price
    GE = bus_params["export_tariff_DKK/kWh"]
    GI = bus_params["import_tariff_DKK/kWh"]
    D = usage["load_preferences"][0]["min_total_energy_per_day_hour_equivalent"]

    # Sweep factors [0, 0.1, ..., 1.0]
    factors = [i / 10 for i in range(11)]
    results_all = []

    for f in factors:
        b = {i: f * s[i] for i in hours}  # buying price is factor * selling price

        params = {
            "hours": hours,
            "pv": pv,
            "b": b,
            "s": s,
            "GE": GE,
            "GI": GI,
            "D": D,
        }

        opt = OptimizationModel1a(params)
        opt.run()

        res = opt.results.copy()     # <- copy!
        res["factor"] = f
        results_all.append(res)

        for r in results_all:
            print(f"factor={r['factor']}, objective={r.get('objective')}, status={r.get('status','ok')}")

    return results_all


def run_optimization_1b(lambda_discomfort=0.5, tolerance_ratio=0.0):
    loader = DataLoader1b()
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
    GE = bus_params["export_tariff_DKK/kWh"]

    ratios = usage["load_preferences"][0]["hourly_profile_ratio"]
    d_hour = app_params["load"][0]["max_load_kWh_per_hour"]
    ref_load = {i: d_hour * ratios[i] for i in hours}

    # tolerance in kWh per hour
    tol = {i: tolerance_ratio * ref_load[i] for i in hours}

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
    }

    opt = OptimizationModel1b(params)
    opt.run()
    res = opt.results.copy()
    res["omega"] = lambda_discomfort
    res["tolerance_ratio"] = tolerance_ratio
    res["total_deviation"] = sum(res["deviation"].values())
    return res

import numpy as np

def sweep_1b():
    omegas = np.arange(0, 4.01, 0.1)        # discomfort sweep
    tolerances = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8]      # 0%–50% free deviation
    all_results = []

    for tau in tolerances:
        for om in omegas:
            res = run_optimization_1b(lambda_discomfort=om, tolerance_ratio=tau)
            all_results.append(res)
    return all_results

    
def run_optimization_1c(lambda_discomfort=2):
    """Run Question 1c model (flexible load + battery with discomfort)."""
    loader = DataLoader1c()   # still using same loader
    DER_prod = loader.load_der_production()
    app_params_raw = loader.load_appliance_params()
    bus_params = loader.load_bus_params()
    usage_raw = loader.load_usage_preferences()

    # If JSON returned a list, unwrap
    app_params = app_params_raw[0] if isinstance(app_params_raw, list) else app_params_raw
    usage = usage_raw[0] if isinstance(usage_raw, list) else usage_raw

    hours = range(len(DER_prod))
    PV_capacity = app_params["DER"][0]["max_power_kW"]
    pv = {i: PV_capacity * DER_prod[i] for i in hours}

    b = {i: bus_params["energy_price_DKK_per_kWh"][i] for i in hours}
    s = b.copy()
    GI = bus_params["import_tariff_DKK/kWh"]
    GE = bus_params["export_tariff_DKK/kWh"]

    ratios = usage["load_preferences"][0]["hourly_profile_ratio"]
    d_hour = app_params["load"][0]["max_load_kWh_per_hour"]
    ref_load = {i: d_hour * ratios[i] for i in hours}

    # Storage
    storage = app_params["storage"][0]
    prefs = usage["storage_preferences"][0]

    # Pack
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
        "storage": [storage],
        "storage_preferences": [prefs],
    }

    opt = OptimizationModel1c(params)
    opt.run()
    return opt.results

from typing import Dict, Any, List
import numpy as np

from src.data_ops.data_loader import DataLoader1a, DataLoader1b, DataLoader1c, DataLoader2b
from src.opt_model.opt_model import (
    OptimizationModel1a,
    OptimizationModel1b,
    OptimizationModel1c,
    OptimizationModel2b,
    sweep_GE_1c,
    sweep_buying_factor_1c,
    sweep_omega_1c,
    sweep_tolerance_1c,
    sweep_omega_2b,
)


# ===== Model 1a =====
def run_optimization_1a(scenario: Dict[str, Any] | None = None) -> Dict[str, Any]:
    loader = DataLoader1a()
    DER_prod = loader.load_der_production()
    app_params = loader.load_appliance_params()
    bus_params = loader.load_bus_params()
    usage = loader.load_usage_preferences()

    hours = range(len(DER_prod))
    PV_capacity = app_params["DER"][0]["max_power_kW"]
    pv = {i: PV_capacity * DER_prod[i] for i in hours}

    b_list = bus_params["energy_price_DKK_per_kWh"]
    s_list = b_list.copy()  # parity by default
    GI = bus_params["import_tariff_DKK/kWh"]
    GE = bus_params["export_tariff_DKK/kWh"]
    D = usage["load_preferences"][0]["min_total_energy_per_day_hour_equivalent"]

    # Optional scenario overrides (e.g., different tariffs)
    if scenario:
        GI = scenario.get("GI", GI)
        GE = scenario.get("GE", GE)

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


def run_export_tariff_sweep(start: float = 0.0, stop: float = 2.6, step: float = 0.1) -> List[Dict[str, Any]]:
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

    results_all: List[Dict[str, Any]] = []

    ge = start
    while ge <= stop + 1e-9:  # numeric safety
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
        res = model.results.copy()
        res["GE"] = round(ge, 2)
        results_all.append(res)
        ge += step

    return results_all


def run_buying_price_sweep() -> List[Dict[str, Any]]:
    loader = DataLoader1a()
    DER_prod = loader.load_der_production()
    app_params = loader.load_appliance_params()
    bus_params = loader.load_bus_params()
    usage = loader.load_usage_preferences()

    hours = range(len(DER_prod))
    PV_capacity = app_params["DER"][0]["max_power_kW"]
    pv = {i: PV_capacity * DER_prod[i] for i in hours}
    s = {i: bus_params["energy_price_DKK_per_kWh"][i] for i in hours}
    GE = bus_params["export_tariff_DKK/kWh"]
    GI = bus_params["import_tariff_DKK/kWh"]
    D = usage["load_preferences"][0]["min_total_energy_per_day_hour_equivalent"]

    factors = [i / 10 for i in range(11)]  # 0.0 .. 1.0
    results_all: List[Dict[str, Any]] = []

    for f in factors:
        b = {i: f * s[i] for i in hours}

        params = {"hours": hours, "pv": pv, "b": b, "s": s, "GE": GE, "GI": GI, "D": D}

        opt = OptimizationModel1a(params)
        opt.run()

        res = opt.results.copy()
        res["factor"] = f
        results_all.append(res)

    # Simple CLI printout (kept compact)
    for r in results_all:
        print(f"factor={r['factor']:.1f}, objective={r.get('objective')}")

    return results_all


# ===== Model 1b =====
def run_optimization_1b(lambda_discomfort: float = 1.5, tolerance_ratio: float = 0.0) -> Dict[str, Any]:
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

    # Tolerance is a proportional band around the reference load
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


def sweep_1b() -> List[Dict[str, Any]]:
    omegas = np.arange(0, 4.01, 0.1)  # discomfort sweep
    tolerances = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8]
    all_results: List[Dict[str, Any]] = []

    for tau in tolerances:
        for om in omegas:
            res = run_optimization_1b(lambda_discomfort=float(om), tolerance_ratio=float(tau))
            all_results.append(res)
    return all_results


# ===== Model 1c =====
def run_optimization_1c(lambda_discomfort: float = 1.5) -> Dict[str, Any]:
    loader = DataLoader1c()
    DER_prod = loader.load_der_production()
    app_params_raw = loader.load_appliance_params()
    bus_params = loader.load_bus_params()
    usage_raw = loader.load_usage_preferences()

    # Normalize list/dict to dicts
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

    storage = app_params["storage"][0]
    prefs = usage["storage_preferences"][0]

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


def run_GE_sweep_1c(start: float = 0.4, stop: float = 2.5, step: float = 0.05, lambda_discomfort: float = 1.5) -> List[Dict[str, Any]]:
    results_all: List[Dict[str, Any]] = []
    ge_values = np.arange(start, stop + 1e-9, step)
    for ge in ge_values:
        res = sweep_GE_1c(float(ge), lambda_discomfort=lambda_discomfort)
        res["GE"] = round(float(ge), 2)
        results_all.append(res)
    return results_all


def run_buying_factor_sweep_1c(factors: List[float] | None = None, lambda_discomfort: float = 1.5) -> List[Dict[str, Any]]:
    if factors is None:
        factors = [0.0, 0.5, 1.0]
    results_all: List[Dict[str, Any]] = []
    for f in factors:
        res = sweep_buying_factor_1c(factor=float(f), lambda_discomfort=lambda_discomfort)
        res["factor"] = float(f)
        results_all.append(res)
    return results_all


def run_omega_sweep_1c(omegas: List[float] | None = None, GE: float = 0.4) -> List[Dict[str, Any]]:
    if omegas is None:
        omegas = [1.0, 2.0, 3.0]
    results_all: List[Dict[str, Any]] = []
    for om in omegas:
        res = sweep_omega_1c(lambda_discomfort=float(om), GE=GE)
        res["omega"] = float(om)
        results_all.append(res)
    return results_all


def run_tolerance_sweep_1c(tolerances: List[float] | None = None, omega: float = 1.5, GE: float = 0.4) -> List[Dict[str, Any]]:
    if tolerances is None:
        tolerances = [0.2, 0.4, 0.6, 0.8]
    results_all: List[Dict[str, Any]] = []
    for tau in tolerances:
        res = sweep_tolerance_1c(tolerance_ratio=float(tau), lambda_discomfort=omega, GE=GE)
        res["tolerance_ratio"] = float(tau)
        results_all.append(res)
    return results_all

# ===== Model 2b =====
def run_optimization_2b(lambda_discomfort: float = 1.5) -> Dict[str, Any]:
    loader = DataLoader2b()
    DER_prod = loader.load_der_production()
    app_params_raw = loader.load_appliance_params()
    bus_params = loader.load_bus_params()
    usage_raw = loader.load_usage_preferences()

    # Normalize list/dict to dicts
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

    storage = app_params["storage"][0]
    prefs = usage["storage_preferences"][0]

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

    opt = OptimizationModel2b(params)
    opt.run()
    return opt.results

def run_omega_sweep_2b(GE: float = 0.4, steps: int = 20) -> List[Dict[str, Any]]:
    """Sweep omega between 0 and 3 (inclusive) with given steps."""
    omegas = np.linspace(1.5, 3, steps)
    results_all: List[Dict[str, Any]] = []
    for om in omegas:
        res = sweep_omega_2b(lambda_discomfort=float(om), GE=GE)
        res["omega"] = float(om)
        results_all.append(res)
    return results_all

def sweep_battery_cost(lambda_discomfort: float, GE: float = 0.4,
                       min_cost: float = 0.12, max_cost: float = 1, steps: int = 20):
    """Sweep battery cost per kWh and record scaling + objective."""
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

    costs = np.linspace(min_cost, max_cost, steps)
    results = []

    for cost in costs:
        # override battery cost
        storage[0]["battery_cost_per_kWh"] = cost  

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
        res["battery_cost_per_kWh"] = cost
        results.append(res)
        if "battery_scale" not in res:
            print(f"⚠️  Warning: no solution for cost={cost}, status={res.get('status')}")


    return results


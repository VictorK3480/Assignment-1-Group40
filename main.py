"""
Main entry point for running optimization models (1a, 1b, 1c)
and generating their plots. Cleaned for production use.
"""

from src.runner.runner import (
    run_buying_price_sweep,
    run_optimization_1a,
    run_export_tariff_sweep,
    run_optimization_1b,
    run_optimization_1c,
    run_optimization_2b,
    sweep_1b,
    run_GE_sweep_1c,
    run_buying_factor_sweep_1c,
    run_omega_sweep_1c,
    run_tolerance_sweep_1c,
    run_omega_sweep_2b,
    sweep_battery_cost
)
from src.data_ops.data_visualizer import DataVisualizer
from src.utils import print_results  


# MAIN EXECUTION
### NOTE: Uncomment desired sections to run specific models

if __name__ == "__main__":

    # --- Model 1a ---
    base_results = run_optimization_1a()
    print_results(base_results, model="1a")
    DataVisualizer.plot_hourly_energy_flows_base_1a(base_results)

    # GE Sensitivity analysis 
    results_sweep = run_export_tariff_sweep(0.0, 2.6, 0.05)
    DataVisualizer.plot_hourly_energy_flows_scenarios_1a(results_sweep)

    # Buying price Sensitivity analysis
    results_buying = run_buying_price_sweep()
    DataVisualizer.plot_buying_price_sweep_1a(results_buying)

    # --- Model 1b ---
    results_1b = run_optimization_1b()
    print_results(results_1b, model="1b")
    DataVisualizer.plot_hourly_energy_flows_1b(results_1b)

    # Omega and tolerance Sensitivity analysis
    results_sweep_1b = sweep_1b()
    DataVisualizer.plot_sweep_1b(results_sweep_1b)

    # --- Model 1c ---

    # Base case 
    results_1c = run_optimization_1c(lambda_discomfort=1.5)
    print_results(results_1c, model="1c")
    DataVisualizer.plot_hourly_energy_flows_1c(results_1c)
    DataVisualizer.plot_battery_soc_1c(results_1c)
    
    # GE Sensitivity analysis 
    ge_results = run_GE_sweep_1c()
    selected_GEs = [0.85, 1.3, 2.5]  # chosen export tariffs
    selected_ge_results = [
        r for r in ge_results if round(r["GE"], 2) in selected_GEs and "pv" in r
    ]

    for res in selected_ge_results:
        print_results(res, model=f"1c (GE={res['GE']})")

    DataVisualizer.plot_hourly_energy_flows_subplots_GE_1c(
        selected_ge_results, selected_GEs=selected_GEs
    )

    # Omega Sensitivity analysis  
    omega_results = run_omega_sweep_1c()
    for res in omega_results:
        print_results(res, model=f"1c (ω={res['omega']})")

    DataVisualizer.plot_hourly_energy_flows_subplots_omega_1c(
        omega_results, omegas=[1, 2, 3]
    )

    # Tolerance Sensitivity analysis 
    tol_results = run_tolerance_sweep_1c()
    for res in tol_results:
        print_results(res, model=f"1c (τ={res['tolerance_ratio']})")

    DataVisualizer.plot_hourly_energy_flows_subplots_tolerance_1c(
        tol_results, tolerances=[0.2, 0.4, 0.6, 0.8], omega=1.5
    )


    # --- Model 2b ---

    results_2b = run_optimization_2b(lambda_discomfort=1.5)
    print_results(results_2b, model="2b")
    DataVisualizer.plot_hourly_energy_flows_2b(results_2b)
    DataVisualizer.plot_battery_soc_2b(results_2b)

    # Omega Sensitivity analysis   
    results_omega = run_omega_sweep_2b(GE=0.4, steps=20)
    DataVisualizer.plot_omega_sweep(results_omega)

    # Battery cost Sensitivity analysis  
    results_cost = sweep_battery_cost(lambda_discomfort=1.5, min_cost=0.12, max_cost=1, steps=20)
    DataVisualizer.plot_battery_cost_sweep(results_cost)



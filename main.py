from src.runner.runner import (
    run_buying_price_sweep,
    run_optimization_1a,
    run_export_tariff_sweep,
    run_optimization_1b,
    run_optimization_1c,
    sweep_1b,
)
from src.data_ops.data_visualizer import DataVisualizer


def print_results(res, model="1a"):
    """Pretty print results with units for models 1a, 1b, 1c."""
    print("\n============================")
    print(f" Results for model {model} ")
    print("============================")

    # Objective breakdown
    print(f"Objective value       : {res.get('objective', 0):.3f} DKK")
    if "import_cost" in res:
        print(f"  Import cost         : {res['import_cost']:.3f} DKK")
    if "export_revenue" in res:
        print(f"  Export revenue      : {res['export_revenue']:.3f} DKK")
    if "discomfort_penalty" in res:
        print(f"  Discomfort penalty  : {res['discomfort_penalty']:.3f} DKK")
    if "net_profit" in res:
        print(f"  Net profit          : {res['net_profit']:.3f} DKK")

    # Totals
    print("\n--- Energy totals ---")
    if "total_import" in res:
        print(f"  Total import        : {res['total_import']:.3f} kWh")
    if "total_export" in res:
        print(f"  Total export        : {res['total_export']:.3f} kWh")
    if "total_served" in res:
        print(f"  Total served load   : {res['total_served']:.3f} kWh")
    if "total_demand" in res:
        print(f"  Total demand        : {res['total_demand']:.3f} kWh")
    if "total_deviation" in res:
        print(f"  Total deviation     : {res['total_deviation']:.3f} kWh")
    if "total_charge" in res:
        print(f"  Total charge        : {res['total_charge']:.3f} kWh")
    if "total_discharge" in res:
        print(f"  Total discharge     : {res['total_discharge']:.3f} kWh")

    # Duals
    print("\n--- Dual values (shadow prices) ---")
    if "dual_daily_demand" in res:
        print(f"  Daily demand shadow price : {res['dual_daily_demand']:.3f} DKK/kWh")
    if "dual_hourly_balance" in res:
        avg_bal = sum(res['dual_hourly_balance'].values()) / len(res['dual_hourly_balance'])
        print(f"  Avg hourly balance price  : {avg_bal:.3f} DKK/kWh")
    if "dual_pv_cap" in res:
        max_pv_dual = max(res['dual_pv_cap'].values())
        print(f"  Max PV cap shadow price   : {max_pv_dual:.3f} DKK/kWh")
    if "dual_soc_final" in res:
        print(f"  Final SOC shadow price    : {res['dual_soc_final']:.3f} DKK/kWh")
    if "dual_soc_init" in res and res["dual_soc_init"] is not None:
        print(f"  Initial SOC shadow price  : {res['dual_soc_init']:.3f} DKK/kWh")


if __name__ == "__main__":

    ##### 1a #####
    # base_results = run_optimization_1a()
    # print_results(base_results, model="1a")
    # DataVisualizer.plot_hourly_energy_flows_base(base_results)

    # ##### 1b #####
    # results_1b = run_optimization_1b()
    # print_results(results_1b, model="1b")
    # DataVisualizer.plot_hourly_energy_flows_1b(results_1b)

    # # Sweep ω and tolerance
    # results_sweep_1b = sweep_1b()
    # DataVisualizer.plot_sweep_1b(results_sweep_1b)

    #### 1c #####
    results_1c = run_optimization_1c(lambda_discomfort=2)
    print_results(results_1c, model="1c")
    DataVisualizer.plot_hourly_energy_flows_1c(results_1c)
    DataVisualizer.plot_battery_soc_1c(results_1c)

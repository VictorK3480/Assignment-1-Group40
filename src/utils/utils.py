def print_results(res, model="2b") -> None:
    """Pretty-print optimization results."""
    print("\n============================")
    print(f" Results for model {model} ")
    print("============================")

    # Objective breakdown
    if "objective" in res:
        print(f"Objective value       : {res['objective']:.3f} DKK")
    if "import_cost" in res:
        print(f"  Import cost         : {res['import_cost']:.3f} DKK")
    if "export_revenue" in res:
        print(f"  Export revenue      : {res['export_revenue']:.3f} DKK")
    if "discomfort_penalty" in res:
        print(f"  Discomfort penalty  : {res['discomfort_penalty']:.3f} DKK")
    if "battery_cost" in res:
        print(f"  Battery cost        : {res['battery_cost']:.3f} DKK")
    if "net_profit" in res:
        print(f"  Net profit          : {res['net_profit']:.3f} DKK")

    print("\n--- Energy totals ---")
    for key in ["total_import", "total_export", "total_served", "total_demand",
                "total_deviation", "total_charge", "total_discharge"]:
        if key in res:
            print(f"  {key.replace('_', ' ').title():22s}: {res[key]:.3f} kWh")

    #print battery scaling factor
    if model == "2b" and "battery_scale" in res:
        print(f"\n--- Battery Scaling ---")
        print(f"  Battery scaling factor    : {res['battery_scale']:.3f}")

    print("\n--- Duals (shadow prices) ---")
    if "dual_daily_demand" in res:
        print(f"  Daily demand shadow price : {res['dual_daily_demand']:.3f}")
    if "dual_pv_cap" in res:
        print(f"  Max PV cap shadow price   : {max(res['dual_pv_cap'].values()):.3f}")
    if "dual_balance" in res:
        avg = sum(res['dual_balance'].values()) / len(res['dual_balance'])
        print(f"  Avg balance shadow price  : {avg:.3f}")
    if "dual_soc_final" in res:
        print(f"  Final SOC shadow price    : {res['dual_soc_final']:.3f}")
    if "dual_charge_cap" in res:
        print(f"  Max charge cap shadow     : {max(res['dual_charge_cap'].values()):.3f}")
    if "dual_discharge_cap" in res: 
        print(f"  Max discharge cap shadow  : {max(res['dual_discharge_cap'].values()):.3f}")
    #print soc capacity shadow price if present
    if model == "2b" and "dual_soc_capacity" in res:
        print(f"  SOC capacity shadow price : {res['dual_soc_capacity']:.3f}")


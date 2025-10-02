import matplotlib.pyplot as plt
import pandas as pd

class DataVisualizer:
    @staticmethod
    def plot_profit_vs_GE_1a(results_all, base_GE=0.4, base_profit=None):
        """Plot profit vs export tariff GE, optionally marking the base case."""
        GEs = [r["GE"] for r in results_all]
        profits = [r["objective"] for r in results_all]

        plt.figure(figsize=(8, 2))
        plt.plot(GEs, profits, marker="o", label="Sweep")

        if base_profit is not None:
            plt.scatter([base_GE], [base_profit],
                        color="red", zorder=5, label=f"Base Case (GE={base_GE})")

        plt.xlabel("Export Tariff GE [DKK/kWh]")
        plt.ylabel("Profit [DKK]")
        plt.title("Profit vs Export Tariff")
        plt.legend()
        plt.grid(True, linestyle="--", alpha=0.7)
        plt.tight_layout()
        plt.show()

    @staticmethod
    def plot_hourly_energy_flows_base_1a(results):
        """Plot hourly PV, Import, Export, Demand for the base case."""
        hours = list(results["pv"].keys())
        pv_vals = list(results["pv"].values())
        imp_vals = list(results["import"].values())
        exp_vals = list(results["export"].values())
        demand_vals = list(results["demand_served"].values())

        plt.figure(figsize=(12, 4))
        plt.plot(hours, pv_vals, marker="o", label="PV Produced", color="goldenrod")
        plt.plot(hours, imp_vals, marker="s", label="Import", color="tomato")
        plt.plot(hours, exp_vals, marker="^", label="Export", color="cornflowerblue")
        plt.plot(hours, demand_vals, marker="d", label="Demand Met", color="seagreen")

        plt.xlabel("Hour of Day")
        plt.ylabel("Energy [kWh]")
        plt.title("Hourly Energy Flows – Base Case")
        plt.legend()
        plt.grid(True, linestyle="--", alpha=0.7)
        plt.tight_layout()
        plt.show()

    @staticmethod
    def plot_hourly_energy_flows_scenarios_1a(results_list, labels=None):
        """
        Plot 4 subplots: each scenario (GE value) has PV, Import, Export, Demand vs hours.
        results_list: list of results dicts (each from OptimizationModel)
        labels: list of scenario names (optional)
        """
        if labels is None:
            labels = [f"GE={r['GE']}" for r in results_list]

        hours = list(results_list[0]["pv"].keys())

        fig, axs = plt.subplots(len(results_list), 1, figsize=(12, 2*len(results_list)), sharex=True)

        # If only one scenario, axs is not iterable
        if len(results_list) == 1:
            axs = [axs]

        for idx, res in enumerate(results_list):
            pv_vals = list(res["pv"].values())
            imp_vals = list(res["import"].values())
            exp_vals = list(res["export"].values())
            demand_vals = list(res["demand_served"].values())

            axs[idx].plot(hours, pv_vals, marker="o", label="PV Produced", color="goldenrod")
            axs[idx].plot(hours, imp_vals, marker="s", label="Import", color="tomato")
            axs[idx].plot(hours, exp_vals, marker="^", label="Export", color="cornflowerblue")
            axs[idx].plot(hours, demand_vals, marker="d", label="Demand Met", color="seagreen")

            axs[idx].set_title(f"Hourly Energy Flows – {labels[idx]}")
            axs[idx].set_ylabel("Energy [kWh]")
            axs[idx].legend()
            axs[idx].grid(True, linestyle="--", alpha=0.6)
            axs[idx].set_title(f"Hourly Energy Flows – GE={res['GE']:.2f}")


        axs[-1].set_xlabel("Hour of Day")
        plt.tight_layout()
        plt.show()
    
    @staticmethod
    def plot_profit_vs_buying_factor_1a(results_all):
        factors = [r["factor"] for r in results_all]
        profits = [r["objective"] for r in results_all]

        plt.figure(figsize=(8, 2))
        plt.plot(factors, profits, marker="o", label="Profit")
        plt.xlabel("Buying Price Factor (× Selling Price)")
        plt.ylabel("Profit [DKK]")
        plt.title("Profit vs Buying Price Factor")
        plt.grid(True)
        plt.tight_layout()
        plt.show()

    @staticmethod
    def plot_hourly_energy_flows_buying_price_subplots_1a(results_all, factors_to_plot=[0, 0.5]):
        """Create subplots for hourly energy flows at selected buying price factors."""
        fig, axs = plt.subplots(len(factors_to_plot), 1, figsize=(12, 2*len(factors_to_plot)), sharex=True)

        # If only one factor, axs is not iterable
        if len(factors_to_plot) == 1:
            axs = [axs]

        for idx, f in enumerate(factors_to_plot):
            res = next(r for r in results_all if abs(r["factor"] - f) < 1e-6 and "pv" in r)
            hours = list(res["pv"].keys())
            pv = list(res["pv"].values())
            imports = list(res["import"].values())
            exports = list(res["export"].values())
            demand = list(res["demand_served"].values())

            axs[idx].plot(hours, pv, label="PV Production", marker="o")
            axs[idx].plot(hours, imports, label="Import", marker="s")
            axs[idx].plot(hours, exports, label="Export", marker="^")
            axs[idx].plot(hours, demand, label="Demand Served", marker="d")

            axs[idx].set_ylabel("Energy [kWh]")
            axs[idx].set_title(f"Hourly Flows – Buying Price = {f} × Selling Price")
            axs[idx].legend()
            axs[idx].grid(True, linestyle="--", alpha=0.6)

        axs[-1].set_xlabel("Hour of Day")
        plt.tight_layout()
        plt.show()


    @staticmethod
    def plot_hourly_flexible_1a(results):
        """
        Plot hourly reference load vs optimized flexible load (1b case).
        """
        hours = list(results["served"].values())
        ref_load = list(results["reference_load"].values())
        opt_load = list(results["flexible_load"].values())

        plt.figure(figsize=(12, 6))
        plt.plot(hours, ref_load, marker="o", label="Reference Load", color="gray")
        plt.plot(hours, opt_load, marker="s", label="Optimized Flexible Load", color="seagreen")

        # Highlight difference (discomfort)
        diff = [abs(o - r) for o, r in zip(opt_load, ref_load)]
        plt.bar(hours, diff, alpha=0.2, color="tomato", label="Discomfort (|Δ|)")

        plt.xlabel("Hour of Day")
        plt.ylabel("Energy [kWh]")
        plt.title("Reference vs Optimized Flexible Load – 1b Case")
        plt.legend()
        plt.grid(True, linestyle="--", alpha=0.7)
        plt.tight_layout()
        plt.show()

    @staticmethod
    def plot_hourly_energy_flows_1b(results):
        """Plot hourly PV, Import, Export, Served Load, Reference Load (case 1b)."""
        hours = list(results["pv"].keys())
        pv_vals = list(results["pv"].values())
        imp_vals = list(results["import"].values())
        exp_vals = list(results["export"].values())
        served_vals = list(results["served"].values())
        ref_vals = list(results["reference_load"].values())

        plt.figure(figsize=(12, 4))
        plt.plot(hours, pv_vals, marker="o", label="PV Produced", color="goldenrod")
        plt.plot(hours, imp_vals, marker="s", label="Import", color="tomato")
        plt.plot(hours, exp_vals, marker="^", label="Export", color="cornflowerblue")
        plt.plot(hours, served_vals, marker="d", label="Served Load", color="seagreen")
        plt.plot(hours, ref_vals, marker="x", linestyle="--", label="Reference Load", color="gray")

        plt.xlabel("Hour of Day")
        plt.ylabel("Energy [kWh]")
        plt.title("Hourly Energy Flows – Case 1b")
        plt.legend()
        plt.grid(True, linestyle="--", alpha=0.7)
        plt.tight_layout()
        plt.show()

    @staticmethod
    def plot_sweep_1b(results):
        import pandas as pd
        import matplotlib.pyplot as plt

        df = pd.DataFrame(results)

        # --- Plot 1: Profit vs ω (tolerance = 0) ---
        df_tau0 = df[df["tolerance_ratio"] == 0.0]
        plt.figure(figsize=(6,4))
        plt.plot(df_tau0["omega"], df_tau0["objective"], marker="o")
        plt.xlabel("Discomfort weight ω")
        plt.ylabel("Profit [DKK]")
        plt.title("Profit vs ω (τ = 0)")
        plt.grid(True, ls="--", alpha=0.6)
        plt.tight_layout()
        plt.show()

        # --- Plot 2: Profit vs tolerance (ω = 2) ---
        df_w2 = df[abs(df["omega"] - 2.0) < 1e-6]   # select ω=2
        plt.figure(figsize=(6,4))
        plt.plot(df_w2["tolerance_ratio"], df_w2["objective"], marker="s")
        plt.xlabel("Tolerance ratio")
        plt.ylabel("Profit [DKK]")
        plt.title("Profit vs tolerance (ω = 2)")
        plt.grid(True, ls="--", alpha=0.6)
        plt.tight_layout()
        plt.show()


    @staticmethod
    def plot_hourly_energy_flows_1c(results, start_hour=18, end_hour=23):
        """Plot hourly PV, Import, Export, Served Load, Reference Load, Battery Charge/Discharge (restricted hours)."""
        # Select the range of hours
        hours = [h for h in results["pv"].keys() if start_hour <= h <= end_hour]

        pv_vals = [results["pv"][h] for h in hours]
        imp_vals = [results["import"][h] for h in hours]
        exp_vals = [results["export"][h] for h in hours]
        served_vals = [results["served"][h] for h in hours]
        ref_vals = [results["reference_load"][h] for h in hours]
        charge_vals = [results["charge"][h] for h in hours]
        discharge_vals = [results["discharge"][h] for h in hours]

        plt.figure(figsize=(10, 5))
        plt.plot(hours, pv_vals, marker="o", label="PV Produced", color="goldenrod")
        plt.plot(hours, imp_vals, marker="s", label="Import", color="tomato")
        plt.plot(hours, exp_vals, marker="^", label="Export", color="cornflowerblue")
        plt.plot(hours, served_vals, marker="d", label="Served Load", color="seagreen")
        plt.plot(hours, ref_vals, marker="x", linestyle="--", label="Reference Load", color="gray")
        plt.plot(hours, charge_vals, marker="<", label="Battery Charge", color="purple")
        plt.plot(hours, discharge_vals, marker=">", label="Battery Discharge", color="orchid")

        plt.xlabel("Hour of Day")
        plt.ylabel("Energy [kWh]")
        plt.title(f"Hourly Energy Flows – Case 1c (Hours {start_hour}–{end_hour})")
        plt.legend()
        plt.grid(True, linestyle="--", alpha=0.7)
        plt.tight_layout()
        plt.show()


    @staticmethod
    def plot_battery_soc_1c(results):
        """Plot battery State of Charge (SOC) trajectory."""
        hours = list(results["soc"].keys())
        soc_vals = list(results["soc"].values())

        plt.figure(figsize=(10, 4))
        plt.step(hours, soc_vals, where="mid", marker="o", color="slateblue", label="SOC")
        plt.xlabel("Hour of Day")
        plt.ylabel("SOC [kWh]")
        plt.title("Battery State of Charge – Case 1c")
        plt.grid(True, linestyle="--", alpha=0.7)
        plt.legend()
        plt.tight_layout()
        plt.show()
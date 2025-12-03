import matplotlib.pyplot as plt
import pandas as pd
from typing import List, Dict, Any


class DataVisualizer:
    # ===== 1a =====
    @staticmethod
    def plot_profit_vs_GE_1a(results_all: List[Dict[str, Any]], base_GE: float = 0.4, base_profit: float | None = None) -> None:
        GEs = [r["GE"] for r in results_all]
        profits = [r["objective"] for r in results_all]

        plt.figure(figsize=(8, 2.5))
        plt.plot(GEs, profits, marker="o", label="Sweep")
        if base_profit is not None:
            plt.scatter([base_GE], [base_profit], color="red", zorder=5, label=f"Base (GE={base_GE})")
        plt.xlabel("Export Tariff GE [DKK/kWh]")
        plt.ylabel("Profit [DKK]")
        plt.title("Profit vs Export Tariff (1a)")
        plt.legend()
        plt.grid(True, linestyle="--", alpha=0.7)
        plt.tight_layout()
        plt.show()

    @staticmethod
    def plot_hourly_energy_flows_base_1a(results: Dict[str, Any]) -> None:
        hours = list(results["pv"].keys())
        pv_vals = list(results["pv"].values())
        imp_vals = list(results["import"].values())
        exp_vals = list(results["export"].values())
        demand_vals = list(results["demand_served"].values())

        plt.figure(figsize=(12, 4))
        plt.plot(hours, pv_vals, marker="o", label="PV")
        plt.plot(hours, imp_vals, marker="s", label="Import")
        plt.plot(hours, exp_vals, marker="^", label="Export")
        plt.plot(hours, demand_vals, marker="d", label="Demand Served")
        plt.xlabel("Hour")
        plt.ylabel("Energy [kWh]")
        plt.title("Hourly Energy Flows – 1a")
        plt.legend()
        plt.grid(True, linestyle="--", alpha=0.7)
        plt.tight_layout()
        plt.show()

    @staticmethod
    def plot_buying_price_sweep_1a(results: List[Dict[str, Any]]) -> None:
        df = pd.DataFrame(results)

        plt.figure(figsize=(8, 2.5))
        plt.plot(df["factor"], df["objective"], marker="o")
        plt.xlabel("Buying Price Factor")
        plt.ylabel("Profit [DKK]")
        plt.title("Profit vs Buying Price Factor (1a)")
        plt.grid(True, ls="--", alpha=0.6)
        plt.tight_layout()
        plt.show()

    @staticmethod
    def plot_hourly_energy_flows_scenarios_1a(results_list: List[Dict[str, Any]], labels: List[str] | None = None) -> None:
        if labels is None:
            labels = [f"GE={r['GE']}" for r in results_list]

        hours = list(results_list[0]["pv"].keys())
        fig, axs = plt.subplots(len(results_list), 1, figsize=(12, 2.5 * len(results_list)), sharex=True)
        if len(results_list) == 1:
            axs = [axs]

        for idx, res in enumerate(results_list):
            pv_vals = list(res["pv"].values())
            imp_vals = list(res["import"].values())
            exp_vals = list(res["export"].values())
            demand_vals = list(res["demand_served"].values())

            axs[idx].plot(hours, pv_vals, marker="o", label="PV")
            axs[idx].plot(hours, imp_vals, marker="s", label="Import")
            axs[idx].plot(hours, exp_vals, marker="^", label="Export")
            axs[idx].plot(hours, demand_vals, marker="d", label="Demand Served")
            axs[idx].set_ylabel("Energy [kWh]")
            axs[idx].set_title(f"Hourly Energy Flows – {labels[idx]}")
            axs[idx].legend()
            axs[idx].grid(True, linestyle="--", alpha=0.6)

        axs[-1].set_xlabel("Hour")
        plt.tight_layout()
        plt.show()

    # ===== 1b =====
    @staticmethod
    def plot_hourly_energy_flows_1b(results: Dict[str, Any]) -> None:
        hours = list(results["pv"].keys())
        pv_vals = list(results["pv"].values())
        imp_vals = list(results["import"].values())
        exp_vals = list(results["export"].values())
        served_vals = list(results["served"].values())
        ref_vals = list(results["reference_load"].values())

        plt.figure(figsize=(12, 4))
        plt.plot(hours, pv_vals, marker="o", label="PV")
        plt.plot(hours, imp_vals, marker="s", label="Import")
        plt.plot(hours, exp_vals, marker="^", label="Export")
        plt.plot(hours, served_vals, marker="d", label="Served")
        plt.plot(hours, ref_vals, marker="x", linestyle="--", label="Reference")
        plt.xlabel("Hour")
        plt.ylabel("Energy [kWh]")
        plt.title("Hourly Energy Flows – 1b")
        plt.legend()
        plt.grid(True, linestyle="--", alpha=0.7)
        plt.tight_layout()
        plt.show()

    @staticmethod
    def plot_sweep_1b(results: List[Dict[str, Any]]) -> None:
        df = pd.DataFrame(results)

        # Profit vs ω at τ = 0
        df_tau0 = df[df["tolerance_ratio"] == 0.0]
        plt.figure(figsize=(12, 3))
        plt.plot(df_tau0["omega"], df_tau0["objective"], marker="o")
        plt.xlabel("Discomfort weight ω")
        plt.ylabel("Profit [DKK]")
        plt.title("Profit vs ω (τ = 0) – 1b")
        plt.grid(True, ls="--", alpha=0.6)
        plt.tight_layout()
        plt.show()

        # Profit vs tolerance at ω = 1.5 (aligns with runner default)
        df_w = df[abs(df["omega"] - 1.5) < 1e-6]
        plt.figure(figsize=(12, 3))
        plt.plot(df_w["tolerance_ratio"], df_w["objective"], marker="s")
        plt.xlabel("Tolerance ratio τ")
        plt.ylabel("Profit [DKK]")
        plt.title("Profit vs τ (ω = 1.5) – 1b")
        plt.grid(True, ls="--", alpha=0.6)
        plt.tight_layout()
        plt.show()

    @staticmethod
    def plot_hourly_energy_flows_subplots_1b(results_all: List[Dict[str, Any]], omegas_to_plot: List[float], tolerance: float = 0.0) -> None:
        fig, axs = plt.subplots(len(omegas_to_plot), 1, figsize=(12, 2.5 * len(omegas_to_plot)), sharex=True)
        if len(omegas_to_plot) == 1:
            axs = [axs]

        for idx, om in enumerate(omegas_to_plot):
            res = next(
                r for r in results_all if abs(r["omega"] - om) < 1e-6 and abs(r["tolerance_ratio"] - tolerance) < 1e-6
            )
            hours = list(res["pv"].keys())
            pv_vals = list(res["pv"].values())
            imp_vals = list(res["import"].values())
            exp_vals = list(res["export"].values())
            served_vals = list(res["served"].values())
            ref_vals = list(res["reference_load"].values())

            axs[idx].plot(hours, pv_vals, marker="o", label="PV")
            axs[idx].plot(hours, imp_vals, marker="s", label="Import")
            axs[idx].plot(hours, exp_vals, marker="^", label="Export")
            axs[idx].plot(hours, served_vals, marker="d", label="Served")
            axs[idx].plot(hours, ref_vals, linestyle="--", marker="x", label="Reference")
            axs[idx].set_ylabel("Energy [kWh]")
            axs[idx].set_title(f"Hourly Flows – ω={om}, τ={tolerance}")
            axs[idx].legend()
            axs[idx].grid(True, linestyle="--", alpha=0.6)

        axs[-1].set_xlabel("Hour")
        plt.tight_layout()
        plt.show()

    @staticmethod
    def plot_hourly_energy_flows_subplots_tolerance_1b(results_all: List[Dict[str, Any]], tolerances_to_plot: List[float], omega: float = 1.5) -> None:
        fig, axs = plt.subplots(len(tolerances_to_plot), 1, figsize=(12, 2.5 * len(tolerances_to_plot)), sharex=True)
        if len(tolerances_to_plot) == 1:
            axs = [axs]

        for idx, tau in enumerate(tolerances_to_plot):
            res = next(r for r in results_all if abs(r["tolerance_ratio"] - tau) < 1e-6 and abs(r["omega"] - omega) < 1e-6)
            hours = list(res["pv"].keys())
            pv = list(res["pv"].values())
            imports = list(res["import"].values())
            exports = list(res["export"].values())
            served = list(res["served"].values())
            ref_load = list(res["reference_load"].values())

            axs[idx].plot(hours, pv, label="PV", marker="o")
            axs[idx].plot(hours, imports, label="Import", marker="s")
            axs[idx].plot(hours, exports, label="Export", marker="^")
            axs[idx].plot(hours, served, label="Served", marker="d")
            axs[idx].plot(hours, ref_load, label="Reference", linestyle="--")
            axs[idx].set_ylabel("Energy [kWh]")
            axs[idx].set_title(f"Hourly Flows – ω={omega}, τ={tau}")
            axs[idx].legend()
            axs[idx].grid(True, linestyle="--", alpha=0.6)

        axs[-1].set_xlabel("Hour")
        plt.tight_layout()
        plt.show()

    # ===== 1c =====
    @staticmethod
    def plot_hourly_energy_flows_1c(results: Dict[str, Any], start_hour: int = 16, end_hour: int = 21) -> None:
        # Guard: clamp to provided keys
        all_hours = list(results["pv"].keys())
        hours = [h for h in all_hours if start_hour <= h <= end_hour]

        pv_vals = [results["pv"][h] for h in hours]
        imp_vals = [results["import"][h] for h in hours]
        exp_vals = [results["export"][h] for h in hours]
        served_vals = [results["served"][h] for h in hours]
        ref_vals = [results["reference_load"][h] for h in hours]
        charge_vals = [results["charge"][h] for h in hours]
        discharge_vals = [results["discharge"][h] for h in hours]

        plt.figure(figsize=(10, 3))
        plt.plot(hours, pv_vals, marker="o", label="PV")
        plt.plot(hours, imp_vals, marker="s", label="Import")
        plt.plot(hours, exp_vals, marker="^", label="Export")
        plt.plot(hours, served_vals, marker="d", label="Served")
        plt.plot(hours, ref_vals, marker="x", linestyle="--", label="Reference")
        plt.plot(hours, charge_vals, marker="<", label="Charge")
        plt.plot(hours, discharge_vals, marker=">", label="Discharge")
        plt.xlabel("Hour")
        plt.ylabel("Energy [kWh]")
        plt.title("Hourly Energy Flows – 1c")
        plt.legend()
        plt.grid(True, linestyle="--", alpha=0.7)
        plt.tight_layout()
        plt.show()

    @staticmethod
    def plot_battery_soc_1c(results: Dict[str, Any]) -> None:
        hours = list(results["soc"].keys())
        soc_vals = list(results["soc"].values())

        plt.figure(figsize=(10, 3))
        plt.step(hours, soc_vals, where="mid", marker="o", label="SOC")
        plt.xlabel("Hour")
        plt.ylabel("SOC [kWh]")
        plt.title("Battery SOC – 1c")
        plt.grid(True, linestyle="--", alpha=0.7)
        plt.legend()
        plt.tight_layout()
        plt.show()

    @staticmethod
    def plot_hourly_energy_flows_subplots_GE_1c(results_all: List[Dict[str, Any]], selected_GEs: List[float]) -> None:
        fig, axs = plt.subplots(len(selected_GEs), 1, figsize=(12, 2.5 * len(selected_GEs)), sharex=True)
        if len(selected_GEs) == 1:
            axs = [axs]

        for idx, ge in enumerate(selected_GEs):
            res = next(r for r in results_all if abs(r["GE"] - ge) < 1e-6)
            hours = list(res["pv"].keys())
            pv = list(res["pv"].values())
            imports = list(res["import"].values())
            exports = list(res["export"].values())
            served = list(res["served"].values())
            ref_load = list(res["reference_load"].values())
            charge = list(res["charge"].values())
            discharge = list(res["discharge"].values())

            axs[idx].plot(hours, pv, label="PV", marker="o")
            axs[idx].plot(hours, imports, label="Import", marker="s")
            axs[idx].plot(hours, exports, label="Export", marker="^")
            axs[idx].plot(hours, served, label="Served", marker="d")
            axs[idx].plot(hours, ref_load, label="Reference", linestyle="--")
            axs[idx].plot(hours, charge, label="Charge", marker="<")
            axs[idx].plot(hours, discharge, label="Discharge", marker=">")
            axs[idx].set_ylabel("Energy [kWh]")
            axs[idx].set_title(f"Hourly Flows – GE={ge}")
            axs[idx].legend()
            axs[idx].grid(True, linestyle="--", alpha=0.6)

        axs[-1].set_xlabel("Hour")
        plt.tight_layout()
        plt.show()

    @staticmethod
    def plot_hourly_energy_flows_subplots_buying_1c(results_all: List[Dict[str, Any]], factors: List[float]) -> None:
        fig, axs = plt.subplots(len(factors), 1, figsize=(12, 2.5 * len(factors)), sharex=True)
        if len(factors) == 1:
            axs = [axs]

        for idx, f in enumerate(factors):
            res = next(r for r in results_all if abs(r["factor"] - f) < 1e-6)
            hours = list(res["pv"].keys())
            pv = list(res["pv"].values())
            imports = list(res["import"].values())
            exports = list(res["export"].values())
            served = list(res["served"].values())
            ref_load = list(res["reference_load"].values())

            axs[idx].plot(hours, pv, label="PV", marker="o")
            axs[idx].plot(hours, imports, label="Import", marker="s")
            axs[idx].plot(hours, exports, label="Export", marker="^")
            axs[idx].plot(hours, served, label="Served", marker="d")
            axs[idx].plot(hours, ref_load, linestyle="--", label="Reference")
            axs[idx].set_ylabel("Energy [kWh]")
            axs[idx].set_title(f"Hourly Flows – Buying factor={f}")
            axs[idx].legend()
            axs[idx].grid(True, linestyle="--", alpha=0.6)

        axs[-1].set_xlabel("Hour")
        plt.tight_layout()
        plt.show()

    @staticmethod
    def plot_hourly_energy_flows_subplots_omega_1c(results_all: List[Dict[str, Any]], omegas: List[float]) -> None:
        fig, axs = plt.subplots(len(omegas), 1, figsize=(12, 2.5 * len(omegas)), sharex=True)
        if len(omegas) == 1:
            axs = [axs]

        for idx, om in enumerate(omegas):
            res = next(r for r in results_all if abs(r["omega"] - om) < 1e-6)
            hours = list(res["pv"].keys())
            pv = list(res["pv"].values())
            imports = list(res["import"].values())
            exports = list(res["export"].values())
            served = list(res["served"].values())
            ref_load = list(res["reference_load"].values())

            axs[idx].plot(hours, pv, label="PV", marker="o")
            axs[idx].plot(hours, imports, label="Import", marker="s")
            axs[idx].plot(hours, exports, label="Export", marker="^")
            axs[idx].plot(hours, served, label="Served", marker="d")
            axs[idx].plot(hours, ref_load, linestyle="--", label="Reference")
            axs[idx].set_ylabel("Energy [kWh]")
            axs[idx].set_title(f"Hourly Flows – ω={om}")
            axs[idx].legend()
            axs[idx].grid(True, linestyle="--", alpha=0.6)

        axs[-1].set_xlabel("Hour")
        plt.tight_layout()
        plt.show()

    @staticmethod
    def plot_hourly_energy_flows_subplots_tolerance_1c(results_all: List[Dict[str, Any]], tolerances: List[float], omega: float = 1.5) -> None:
        fig, axs = plt.subplots(len(tolerances), 1, figsize=(12, 2.5 * len(tolerances)), sharex=True)
        if len(tolerances) == 1:
            axs = [axs]

        for idx, tau in enumerate(tolerances):
            res = next(r for r in results_all if abs(r["tolerance_ratio"] - tau) < 1e-6)
            hours = list(res["pv"].keys())
            pv = list(res["pv"].values())
            imports = list(res["import"].values())
            exports = list(res["export"].values())
            served = list(res["served"].values())
            ref_load = list(res["reference_load"].values())

            axs[idx].plot(hours, pv, label="PV", marker="o")
            axs[idx].plot(hours, imports, label="Import", marker="s")
            axs[idx].plot(hours, exports, label="Export", marker="^")
            axs[idx].plot(hours, served, label="Served", marker="d")
            axs[idx].plot(hours, ref_load, linestyle="--", label="Reference")
            axs[idx].set_ylabel("Energy [kWh]")
            axs[idx].set_title(f"Hourly Flows – ω={omega}, τ={tau}")
            axs[idx].legend()
            axs[idx].grid(True, linestyle="--", alpha=0.6)

        axs[-1].set_xlabel("Hour")
        plt.tight_layout()
        plt.show()

    # ===== 2b =====
    @staticmethod
    def plot_hourly_energy_flows_2b(results: Dict[str, Any], start_hour: int = 0, end_hour: int = 87600) -> None:
        # Guard: clamp to provided keys
        all_hours = list(results["pv"].keys())
        hours = [h for h in all_hours if start_hour <= h <= end_hour]

        pv_vals = [results["pv"][h] for h in hours]
        imp_vals = [results["import"][h] for h in hours]
        exp_vals = [results["export"][h] for h in hours]
        served_vals = [results["served"][h] for h in hours]
        ref_vals = [results["reference_load"][h] for h in hours]
        charge_vals = [results["charge"][h] for h in hours]
        discharge_vals = [results["discharge"][h] for h in hours]

        plt.figure(figsize=(10, 3))
        plt.plot(hours, pv_vals, marker="o", label="PV")
        plt.plot(hours, imp_vals, marker="s", label="Import")
        plt.plot(hours, exp_vals, marker="^", label="Export")
        plt.plot(hours, served_vals, marker="d", label="Served")
        plt.plot(hours, ref_vals, marker="x", linestyle="--", label="Reference")
        plt.plot(hours, charge_vals, marker="<", label="Charge")
        plt.plot(hours, discharge_vals, marker=">", label="Discharge")
        plt.xlabel("Hour")
        plt.ylabel("Energy [kWh]")
        plt.title("Hourly Energy Flows – 2b")
        plt.legend()
        plt.grid(True, linestyle="--", alpha=0.7)
        plt.tight_layout()
        plt.show()

    @staticmethod
    def plot_battery_soc_2b(results: Dict[str, Any]) -> None:
        hours = list(results["soc"].keys())
        soc_vals = list(results["soc"].values())

        plt.figure(figsize=(10, 3))
        plt.step(hours, soc_vals, where="mid", marker="o", label="SOC")
        plt.xlabel("Hour")
        plt.ylabel("SOC [kWh]")
        plt.title("Battery SOC – 2b")
        plt.grid(True, linestyle="--", alpha=0.7)
        plt.legend()
        plt.tight_layout()
        plt.show()

    @staticmethod
    def plot_omega_sweep(results):
        # filter valid runs
        valid_results = [r for r in results if "battery_scale" in r and "objective" in r]
        if not valid_results:
            print("No valid results to plot (all runs failed).")
            return

        omegas = [r["omega"] for r in valid_results]
        scales = [r["battery_scale"] for r in valid_results]
        objectives = [r["objective"] for r in valid_results]

        fig, ax1 = plt.subplots()

        color = "tab:blue"
        fig, ax1 = plt.subplots(figsize=(10, 3))
        ax1.set_xlabel("Omega (λ_discomfort)")
        ax1.set_ylabel("Battery scaling factor", color=color)
        ax1.plot(omegas, scales, marker="o", color=color)
        ax1.tick_params(axis="y", labelcolor=color)

        ax2 = ax1.twinx()
        color = "tab:red"
        ax2.set_ylabel("Objective value (DKK)", color=color)
        ax2.plot(omegas, objectives, marker="s", color=color)
        ax2.tick_params(axis="y", labelcolor=color)

        fig.tight_layout()
        plt.title("Sensitivity of battery scale & objective to omega")
        plt.show()

    @staticmethod
    def plot_battery_cost_sweep(results):
        # filter out runs without battery_scale
        valid_results = [r for r in results if "battery_scale" in r and "objective" in r]

        if not valid_results:
            print("No valid results to plot.")
            return
        
        costs = [r["battery_cost_per_kWh"] for r in results]
        scales = [r["battery_scale"] for r in results]
        objectives = [r["objective"] for r in results]

        fig, ax1 = plt.subplots()

        color = "tab:blue"
        fig, ax1 = plt.subplots(figsize=(10, 3))
        ax1.set_xlabel("Battery cost per kWh (DKK)")
        ax1.set_ylabel("Battery scaling factor", color=color)
        ax1.plot(costs, scales, marker="o", color=color, label="Battery scale")
        ax1.tick_params(axis="y", labelcolor=color)

        ax2 = ax1.twinx()
        color = "tab:red"
        ax2.set_ylabel("Objective value (DKK)", color=color)
        ax2.plot(costs, objectives, marker="s", color=color, label="Objective")
        ax2.tick_params(axis="y", labelcolor=color)

        fig.tight_layout()
        plt.title("Sensitivity of battery scale & objective to battery cost")
        plt.show()



"""
Script to plot hourly shadow prices (dual variables) from the demand/supply 
balance constraint in optimization model 1b.

The shadow price represents the marginal value of one additional unit of energy 
at each hour - essentially the economic value of relaxing the energy balance constraint.
"""

import matplotlib.pyplot as plt
from src.runner.runner import run_optimization_1b


def plot_shadow_prices_1b(results: dict) -> None:
    """
    Plot the hourly shadow prices from the balance constraint in model 1b.
    
    Parameters:
    -----------
    results : dict
        Results dictionary from run_optimization_1b containing 'dual_balance' key
    """
    hours = list(results["dual_balance"].keys())
    shadow_prices = list(results["dual_balance"].values())
    
    plt.figure(figsize=(12, 5))
    plt.plot(hours, shadow_prices, marker='o', linewidth=2, markersize=6, color='#2E86AB')
    plt.xlabel("Hour", fontsize=12)
    plt.ylabel("Shadow Price [DKK/kWh]", fontsize=12)
    plt.title("Hourly Shadow Prices - Energy Balance Constraint (Model 1b)", fontsize=14, fontweight='bold')
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.axhline(y=0, color='red', linestyle='-', alpha=0.3, linewidth=0.8)
    plt.tight_layout()
    plt.show()
    
    # Print summary statistics
    print("\n=== Shadow Price Statistics ===")
    print(f"Maximum shadow price: {max(shadow_prices):.4f} DKK/kWh at hour {hours[shadow_prices.index(max(shadow_prices))]}")
    print(f"Minimum shadow price: {min(shadow_prices):.4f} DKK/kWh at hour {hours[shadow_prices.index(min(shadow_prices))]}")
    print(f"Average shadow price: {sum(shadow_prices)/len(shadow_prices):.4f} DKK/MWh")
    print(f"Total hours with positive shadow price: {sum(1 for sp in shadow_prices if sp > 1e-6)}")
    print(f"Total hours with negative shadow price: {sum(1 for sp in shadow_prices if sp < -1e-6)}")


def main():
    """
    Main execution: run model 1b and plot shadow prices.
    """
    print("Running optimization model 1b...")
    
    # Run with default parameters (lambda_discomfort=1.5, tolerance_ratio=0.0)
    results = run_optimization_1b()
    
    if results.get("status") == 2:  # GRB.OPTIMAL = 2
        print("✓ Optimization successful!")
        print(f"Objective value: {results['objective']:.2f} DKK")
        print(f"Total import: {results['total_import']:.2f} kWh")
        print(f"Total export: {results['total_export']:.2f} kWh")
        print(f"Total served: {results['total_served']:.2f} kWh")
        
        # Plot the shadow prices
        plot_shadow_prices_1b(results)
    else:
        print(f"⚠ Optimization failed with status: {results.get('status')}")


if __name__ == "__main__":
    main()

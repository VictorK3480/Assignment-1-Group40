# Assignment 1

This is the repository for Group 40 for the first Assignment for Optimisation in Modern Power Systems

### Getting Started

1. Install dependencies:
   ```bash
   pip install gurobipy matplotlib pandas numpy
2. Run from the project root:
   ```bash
   python main.py
3. Please note: 

### Code Structure

```bash
project_root/
│
├── main.py                       # Entry point for running experiments
│
├── data/
│   ├── question_1a/              # Inputs for Model 1a
│   ├── question_1b/              # Inputs for Model 1b
│   ├── question_1c/              # Inputs for Model 1c
│   └── question_2b/              # Inputs for Model 2b
│
├── src/
│   ├── data_ops/                 
│   │   ├── data_loader.py        # Data loading functions
│   │   ├── data_processor.py     
│   │   └── data_visualizer.py    # Plotting functions
│   │
│   ├── opt_model/                # Optimization model definitions (for problems 1a, 1b, 1c, and 2b)
│   │   └── opt_model.py
│   │
│   ├── runner/                   # Runs optimisation models and senstivity analyses
│   │   └── runner.py
│   │
│   └── utils/                    # Result printing and summaries
│       └── utils.py
│
├── LICENSE
└── README.md
```

### Input Data Structure

The repositories include base datasets under the `data/question_name` directories, organized as follows:

- **Consumers Data (`consumers.json`)**  
    Contains a list of consumers, each with:
    - `consumer_id`: Unique identifier for the consumer
    - `connection_bus`: Bus ID where the consumer is connected
    - `list_appliances`: List of appliance IDs owned by the consumer

- **Appliances Data (`appliance_params.json`)**  
    Contains a list of all appliances and their technical characteristics. Each appliance entry includes:

    - **For DERs (Distributed Energy Resources):**
        - `DER_id`: Unique identifier for the DER appliance
        - `DER_type`: DER technology type (e.g., "PV" for solar photovoltaic, "wind" for wind turbine)
        - `max_power_kW`: Maximum power output (kW)
        - `min_power_ratio`: Minimum operating power as a fraction of max power (unitless, 0–1)
        - `max_ramp_rate_up_ratio`: Maximum allowed increase in power per time step, as a fraction of max power (unitless, 0–1)
        - `max_ramp_rate_down_ratio`: Maximum allowed decrease in power per time step, as a fraction of max power (unitless, 0–1)

    - **For Loads:**
        - `load_id`: Unique identifier for the load appliance
        - `load_type`: Type of load (e.g., "EV", "heater")
        - `max_load_kWh_per_hour`: Maximum energy consumption per hour (kWh/h)
        - `max_ramp_rate_up_ratio`: Maximum allowed increase in load per time step, as a fraction of max load (unitless, 0–1)
        - `max_ramp_rate_down_ratio`: Maximum allowed decrease in load per time step, as a fraction of max load (unitless, 0–1)
        - `min_on_time_h`: Minimum consecutive hours the load must stay ON (h)
        - `min_off_time_h`: Minimum consecutive hours the load must stay OFF (h)

    - **For Storages:**
        - `storage_id`: Unique identifier for the storage appliance
        - `storage_capacity_kWh`: Total energy storage capacity (kWh)
        - `max_charging_power_ratio`: Maximum charging power as a fraction of storage capacity per hour (unitless, 0–1)
        - `max_discharging_power_ratio`: Maximum discharging power as a fraction of storage capacity per hour (unitless, 0–1)
        - `charging_efficiency`: Fraction of energy retained during charging (unitless, 0–1)
        - `discharging_efficiency`: Fraction of energy retained during discharging (unitless, 0–1)

**Note:** All ratios are relative to the respective appliance's maximum capacity or power. Units are indicated in parentheses.
    

- **Usage Preferences (`usage_preference.json`)**  
    Specifies user-defined preferences and constraints for energy usage and appliance operation. Example structure:
    - `consumer_id`: Unique identifier for the consumer
    - `_preferences`: containing
        - **Grid preferences**: Preferences for grid interaction (e.g., "prefer self-consumption", "allow export up to X kWh")
        - **DER preferences**: Preferences for usage of distributed energy resources (e.g., "curtailment cost", "limit wind export", "green consumption ratio")
        - **Load preferences**: Preferences for consumption (daily/hourly) and flexibility:
            - `load_id`: Unique load identifier
            - `min_total_energy_per_day_hour_equivalent`: Minimum daily energy usage (kWh or equivalent hours)
            - `max_total_energy_per_day_hour_equivalent`: Maximum daily energy usage (kWh or equivalent hours)
            - `hourly_profile_ratio`: Desired hourly usage pattern (array of ratios)
        - **Storages**: Preferences for usage of energy storage:
            - `storage_id`: Unique storage identifier
            - `initial_soc_ratio`: Initial state of charge (0–1)
            - `final_soc_ratio`: Desired final state of charge (0–1)
        - **Heat pumps**: Preferences for heat pump operation (e.g., "min runtime", "preferred hours")

- **DER Production (`DER_production.json`)**  
    Contains time series data for DER output profiles at each consumer location.
    - `consumer_id`: Location where the DER is evaluated
    - `DER_type`: Type of DER (e.g., "PV", "wind")
    - `hourly_profile_ratio`: Array of normalized hourly production values (0–1)

- **Bus Data (`bus_params.json`)**  
    Defines technical and economic parameters for each network bus.
    - `bus_id`: Unique bus identifier
    - `import_tariff`: Tariff for net energy import (DKK/kWh)
    - `export_tariff`: Tariff for net energy export (DKK/kWh)
    - `max_import_kw`: Maximum allowed import power (kW)
    - `max_export_kw`: Maximum allowed export power (kW)
    - `price_DKK_per_kWh`: Additional price information if applicable




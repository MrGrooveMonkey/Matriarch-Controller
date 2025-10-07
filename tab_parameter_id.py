from data.parameter_definitions import PARAMETERS, get_parameters_by_category

# Check total parameters
print(f"Total parameters defined: {len(PARAMETERS)}")

# Check parameters 0-75 (excluding 76)
params_0_75 = [p for p in PARAMETERS.keys() if 0 <= p <= 75 and p != 76]
print(f"Parameters in range 0-75 (excluding 76): {len(params_0_75)}")

# Check by category
categories = get_parameters_by_category()
for cat, params in categories.items():
    count_0_75 = len([p for p in params if 0 <= p.param_id <= 75 and p.param_id != 76])
    print(f"{cat}: {count_0_75} parameters in 0-75 range")
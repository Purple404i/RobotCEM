def calculate_printing_cost(volume_cm3: float, material: str, infill: float = 20.0) -> dict:
    """Calculate 3D printing cost estimate"""
    
    material_costs = {
        "PLA": 20.0,
        "ABS": 25.0,
        "PETG": 30.0,
        "Nylon": 80.0
    }
    
    cost_per_kg = material_costs.get(material, 50.0)
    density = 1.25  # g/cm³ for PLA
    
    mass_g = volume_cm3 * density * (infill / 100)
    material_cost = (mass_g / 1000) * cost_per_kg
    
    print_time_hours = volume_cm3 / 10.0
    machine_cost = print_time_hours * 0.10
    
    total = material_cost + machine_cost
    
    return {
        "material_cost_usd": round(material_cost, 2),
        "machine_cost_usd": round(machine_cost, 2),
        "total_cost_usd": round(total, 2),
        "print_time_hours": round(print_time_hours, 1)
    }

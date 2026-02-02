import aiohttp
import asyncio
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ComponentPrice:
    mpn: str
    supplier: str
    price_usd: float
    stock_quantity: int
    moq: int  # Minimum order quantity
    lead_time_days: int
    datasheet_url: str
    last_updated: datetime

@dataclass
class MaterialCost:
    material_name: str
    cost_per_kg: float
    availability: str
    supplier: str
    last_updated: datetime

class MaterialPricingEngine:
    def __init__(self, config: Dict):
        self.octopart_api_key = config.get("octopart_api_key")
        self.digikey_client_id = config.get("digikey_client_id")
        self.digikey_client_secret = config.get("digikey_client_secret")
        self.cache = {}
        self.cache_duration = timedelta(hours=6)
        
        # Material pricing database ($/kg)
        self.material_base_prices = {
            "PLA": 20.0,
            "ABS": 25.0,
            "PETG": 30.0,
            "Nylon": 80.0,
            "TPU": 60.0,
            "ASA": 35.0,
            "Carbon_Fiber_PLA": 120.0,
            "Aluminum_6061": 15.0,
            "Steel_1045": 5.0,
            "Stainless_316": 12.0,
            "Titanium_Ti6Al4V": 350.0
        }

        # Local fallback pricing for common MPNS when external API is unavailable
        self.local_component_prices = {
            "MG996R": {"supplier": "Generic", "price_usd": 8.50, "stock_quantity": 100},
            "SG90": {"supplier": "Generic", "price_usd": 2.50, "stock_quantity": 500},
            "17HS4401": {"supplier": "Generic", "price_usd": 12.00, "stock_quantity": 200},
            "28BYJ-48": {"supplier": "Generic", "price_usd": 3.00, "stock_quantity": 400},
            "608ZZ": {"supplier": "Generic", "price_usd": 0.50, "stock_quantity": 1000}
        }
    
    async def get_component_pricing(
        self,
        mpn: str,
        quantity: int = 1
    ) -> Optional[ComponentPrice]:
        """Fetch real-time component pricing from Octopart"""
        
        cache_key = f"component:{mpn}:{quantity}"
        
        # Check cache
        if cache_key in self.cache:
            cached = self.cache[cache_key]
            if datetime.now() - cached["timestamp"] < self.cache_duration:
                return cached["data"]
        
        try:
            async with aiohttp.ClientSession() as session:
                url = "https://octopart.com/api/v4/rest/parts/search"
                
                headers = {
                    "Authorization": f"Token {self.octopart_api_key}",
                    "Content-Type": "application/json"
                }
                
                payload = {
                    "queries": [{
                        "mpn": mpn,
                        "limit": 5,
                        "start": 0
                    }]
                }
                
                async with session.post(url, headers=headers, json=payload) as resp:
                    if resp.status != 200:
                        logger.error(f"Octopart API error: {resp.status}")
                        return None
                    
                    data = await resp.json()
                    
                    # Parse results
                    results = data.get("results", [])
                    if not results or not results[0].get("items"):
                        logger.warning(f"No results for MPN: {mpn}")
                        return None
                    
                    items = results[0]["items"]
                    if not items:
                        return None
                    
                    # Get best offer (lowest price with stock)
                    best_offer = None
                    best_price = float('inf')
                    
                    for item in items:
                        offers = item.get("offers", [])
                        for offer in offers:
                            if not offer.get("in_stock_quantity", 0):
                                continue
                            
                            prices = offer.get("prices", {}).get("USD", [])
                            if not prices:
                                continue
                            
                            # Find price for requested quantity
                            applicable_price = None
                            for price_break in prices:
                                if price_break[0] <= quantity:
                                    applicable_price = float(price_break[1])
                            
                            if applicable_price and applicable_price < best_price:
                                best_price = applicable_price
                                best_offer = offer
                    
                    if not best_offer:
                        return None
                    
                    component_price = ComponentPrice(
                        mpn=mpn,
                        supplier=best_offer.get("seller", {}).get("name", "Unknown"),
                        price_usd=best_price,
                        stock_quantity=best_offer.get("in_stock_quantity", 0),
                        moq=best_offer.get("moq", 1),
                        lead_time_days=best_offer.get("factory_lead_days", 0),
                        datasheet_url=items[0].get("datasheets", [{}])[0].get("url", ""),
                        last_updated=datetime.now()
                    )
                    
                    # Cache result
                    self.cache[cache_key] = {
                        "data": component_price,
                        "timestamp": datetime.now()
                    }
                    
                    return component_price
        
        except Exception as e:
            logger.error(f"Error fetching component pricing: {e}")
            # Fallback to local price database
            local = self.local_component_prices.get(mpn)
            if local:
                return ComponentPrice(
                    mpn=mpn,
                    supplier=local.get("supplier", "Local"),
                    price_usd=local.get("price_usd", 5.0),
                    stock_quantity=local.get("stock_quantity", 0),
                    moq=1,
                    lead_time_days=0,
                    datasheet_url="",
                    last_updated=datetime.now()
                )
            return None
    
    async def get_material_cost(self, material: str) -> MaterialCost:
        """Get material cost (mostly static, but can be updated)"""
        
        base_price = self.material_base_prices.get(material, 50.0)
        
        # Apply market fluctuations (could integrate real APIs here)
        # For now, just return base price
        
        return MaterialCost(
            material_name=material,
            cost_per_kg=base_price,
            availability="In Stock",
            supplier="Various",
            last_updated=datetime.now()
        )
    
    def calculate_printing_cost(
        self,
        volume_cm3: float,
        material: str,
        infill_percentage: float = 20.0,
        support_material_ratio: float = 0.0
    ) -> Dict:
        """Calculate complete 3D printing cost"""
        
        # Material density (g/cm³)
        densities = {
            "PLA": 1.25,
            "ABS": 1.05,
            "PETG": 1.27,
            "Nylon": 1.14,
            "TPU": 1.21,
            "ASA": 1.05,
            "Carbon_Fiber_PLA": 1.30
        }
        
        density = densities.get(material, 1.25)
        cost_per_kg = self.material_base_prices.get(material, 50.0)
        
        # Calculate masses
        solid_mass_g = volume_cm3 * density
        infill_mass_g = solid_mass_g * (infill_percentage / 100.0)
        support_mass_g = solid_mass_g * support_material_ratio
        total_mass_g = infill_mass_g + support_mass_g
        
        # Material cost
        material_cost = (total_mass_g / 1000.0) * cost_per_kg
        
        # Printing time estimation (very rough)
        # Assume ~10 cm³/hour for FDM
        print_time_hours = volume_cm3 / 10.0
        
        # Machine cost ($0.10/hour for hobby printer, $2/hour for industrial)
        machine_cost_per_hour = 0.10
        machine_cost = print_time_hours * machine_cost_per_hour
        
        # Energy cost (~0.12 kWh at $0.15/kWh)
        energy_cost = print_time_hours * 0.12 * 0.15
        
        # Labor cost (setup + post-processing)
        labor_hours = 0.5 + (print_time_hours * 0.1)  # 10% supervision
        labor_cost_per_hour = 25.0  # USD
        labor_cost = labor_hours * labor_cost_per_hour
        
        total_cost = material_cost + machine_cost + energy_cost + labor_cost
        
        return {
            "material": material,
            "volume_cm3": volume_cm3,
            "solid_mass_g": solid_mass_g,
            "actual_mass_g": total_mass_g,
            "infill_percentage": infill_percentage,
            "material_cost_usd": round(material_cost, 2),
            "machine_cost_usd": round(machine_cost, 2),
            "energy_cost_usd": round(energy_cost, 2),
            "labor_cost_usd": round(labor_cost, 2),
            "total_cost_usd": round(total_cost, 2),
            "print_time_hours": round(print_time_hours, 1),
            "cost_breakdown": {
                "material": round(material_cost / total_cost * 100, 1),
                "machine": round(machine_cost / total_cost * 100, 1),
                "energy": round(energy_cost / total_cost * 100, 1),
                "labor": round(labor_cost / total_cost * 100, 1)
            }
        }
    
    async def generate_bom(self, design_spec: Dict, stl_analysis: Dict) -> Dict:
        """Generate complete Bill of Materials with real-time pricing"""
        
        bom_items = []
        
        # 3D Printed parts
        if "printed_parts" in design_spec or stl_analysis.get("volume_cm3"):
            volume = stl_analysis.get("volume_cm3", 0)
            material = design_spec.get("material_preferences", ["PLA"])[0]
            
            print_cost = self.calculate_printing_cost(
                volume,
                material,
                infill_percentage=design_spec.get("infill_percentage", 20.0)
            )
            
            bom_items.append({
                "category": "3D Printed Parts",
                "item": design_spec.get("device_type", "Custom Part"),
                "material": material,
                "quantity": 1,
                "unit_cost_usd": print_cost["total_cost_usd"],
                "total_cost_usd": print_cost["total_cost_usd"],
                "details": print_cost,
                "supplier": "In-house/Service Bureau"
            })
        
        # Electronic components
        component_tasks = []
        for component in design_spec.get("components", []):
            if "mpn" in component:
                component_tasks.append(
                    self.get_component_pricing(
                        component["mpn"],
                        component.get("quantity", 1)
                    )
                )
        
        # Fetch all component prices concurrently
        component_prices = await asyncio.gather(*component_tasks, return_exceptions=True)
        
        for i, component in enumerate(design_spec.get("components", [])):
            price_data = component_prices[i]
            
            if isinstance(price_data, Exception) or price_data is None:
                # Use fallback pricing
                unit_cost = component.get("estimated_cost", 5.0)
                supplier = "TBD"
                stock = "Unknown"
            else:
                unit_cost = price_data.price_usd
                supplier = price_data.supplier
                stock = price_data.stock_quantity
            
            quantity = component.get("quantity", 1)
            
            bom_items.append({
                "category": "Electronic Components",
                "item": component.get("name", "Component"),
                "mpn": component.get("mpn", ""),
                "quantity": quantity,
                "unit_cost_usd": unit_cost,
                "total_cost_usd": unit_cost * quantity,
                "supplier": supplier,
                "stock": stock,
                "specifications": component.get("specifications", {})
            })
        
        # Hardware (screws, nuts, etc.)
        for hardware in design_spec.get("hardware", []):
            bom_items.append({
                "category": "Hardware",
                "item": hardware["name"],
                "specification": hardware.get("spec", ""),
                "quantity": hardware["quantity"],
                "unit_cost_usd": hardware.get("unit_cost", 0.10),
                "total_cost_usd": hardware["quantity"] * hardware.get("unit_cost", 0.10),
                "supplier": "McMaster-Carr / Fastenal"
            })
        
        # Calculate totals
        subtotal = sum(item["total_cost_usd"] for item in bom_items)
        shipping = subtotal * 0.05  # 5% shipping estimate
        tax = subtotal * 0.08  # 8% tax estimate
        total = subtotal + shipping + tax
        
        return {
            "items": bom_items,
            "summary": {
                "subtotal_usd": round(subtotal, 2),
                "shipping_usd": round(shipping, 2),
                "tax_usd": round(tax, 2),
                "total_usd": round(total, 2),
                "item_count": len(bom_items),
                "total_weight_g": sum(
                    item.get("details", {}).get("actual_mass_g", 0)
                    for item in bom_items
                )
            },
            "generated_at": datetime.now().isoformat(),
            "currency": "USD"
        }
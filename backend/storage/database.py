from sqlalchemy import create_engine, Column, String, Integer, Float, JSON, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os
import json
import logging
import asyncio
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./robotcem.db")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ============================================================================
# SQLAlchemy Models (Legacy + Enhanced)
# ============================================================================

class DesignJob(Base):
    __tablename__ = "design_jobs"
    
    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, index=True)
    prompt = Column(String)
    status = Column(String)  # queued, processing, completed, failed
    progress = Column(Integer, default=0)
    specification = Column(JSON)
    validation = Column(JSON)
    stl_path = Column(String, nullable=True)
    bom = Column(JSON, nullable=True)
    error_message = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

class ComponentCache(Base):
    __tablename__ = "component_cache"
    
    mpn = Column(String, primary_key=True, index=True)
    data = Column(JSON)
    price = Column(Float)
    stock = Column(Integer)
    supplier = Column(String)
    cached_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)

class MaterialPricing(Base):
    __tablename__ = "material_pricing"
    
    material = Column(String, primary_key=True, index=True)
    price_per_kg = Column(Float)
    availability = Column(String)
    supplier = Column(String)
    updated_at = Column(DateTime, default=datetime.utcnow)

class SourcedComponent(Base):
    """Track sourced components from marketplace"""
    __tablename__ = "sourced_components"
    
    id = Column(String, primary_key=True, index=True)
    component_name = Column(String, index=True)
    category = Column(String, index=True)
    manufacturer = Column(String)
    supplier = Column(String)
    material = Column(String)
    specifications = Column(JSON)
    price = Column(Float)
    currency = Column(String)
    lead_time_days = Column(Integer)
    stock_availability = Column(String)
    datasheet_url = Column(String, nullable=True)
    last_price_check = Column(DateTime, default=datetime.utcnow)
    design_job_id = Column(String, index=True, nullable=True)

Base.metadata.create_all(bind=engine)

# ============================================================================
# Data Classes (from parts_database.py)
# ============================================================================

@dataclass
class ComponentPart:
    """Represents a component part with pricing and availability"""
    id: str
    name: str
    category: str
    manufacturer: str
    supplier: str
    material: str
    specifications: Dict[str, Any]
    price: float
    currency: str
    last_price_check: datetime
    lead_time_days: int
    stock_availability: str
    datasheet_url: str
    compatible_with: List[str]
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "manufacturer": self.manufacturer,
            "supplier": self.supplier,
            "material": self.material,
            "specifications": self.specifications,
            "price": self.price,
            "currency": self.currency,
            "last_price_check": self.last_price_check.isoformat(),
            "lead_time_days": self.lead_time_days,
            "stock_availability": self.stock_availability,
            "datasheet_url": self.datasheet_url,
            "compatible_with": self.compatible_with
        }

# ============================================================================
# Parts Database Manager (from parts_database.py)
# ============================================================================

class PartsDatabase:
    """Manages local parts inventory using SQLAlchemy and JSON fallback"""
    
    def __init__(self, db_session=None):
        self.db_session = db_session or SessionLocal()
        self.categories = self._initialize_categories()
    
    def _initialize_categories(self) -> List[str]:
        """Initialize standard component categories"""
        return [
            "bearings",
            "fasteners",
            "shafts",
            "gears",
            "motors",
            "sensors",
            "actuators",
            "connectors",
            "frames",
            "springs",
            "seals",
            "pulleys",
            "couplings",
            "valves",
            "pumps"
        ]
    
    def search_by_specs(self, category: str, specs: Dict[str, Any]) -> List[ComponentPart]:
        """Search database for parts matching specifications"""
        matches = []
        
        try:
            components = self.db_session.query(SourcedComponent).filter(
                SourcedComponent.category == category
            ).all()
            
            for component_data in components:
                if self._specs_match(component_data.specifications or {}, specs):
                    component = ComponentPart(
                        id=component_data.id,
                        name=component_data.component_name,
                        category=component_data.category,
                        manufacturer=component_data.manufacturer,
                        supplier=component_data.supplier,
                        material=component_data.material,
                        specifications=component_data.specifications,
                        price=component_data.price,
                        currency=component_data.currency,
                        last_price_check=component_data.last_price_check,
                        lead_time_days=component_data.lead_time_days,
                        stock_availability=component_data.stock_availability,
                        datasheet_url=component_data.datasheet_url or "",
                        compatible_with=[]
                    )
                    matches.append(component)
        except Exception as e:
            logger.warning(f"Database search failed: {e}")
        
        return sorted(matches, key=lambda x: x.price)
    
    def _specs_match(self, db_specs: Dict, search_specs: Dict) -> bool:
        """Check if component specs match search criteria"""
        for key, required_value in search_specs.items():
            if key not in db_specs:
                return False
            
            db_value = db_specs[key]
            
            # Numeric values: allow 10% tolerance
            if isinstance(required_value, (int, float)):
                tolerance = abs(required_value * 0.1)
                if not (db_value - tolerance <= required_value <= db_value + tolerance):
                    return False
            else:
                # String/exact match
                if db_value != required_value:
                    return False
        
        return True
    
    def add_component(self, component: ComponentPart, design_job_id: str = None) -> bool:
        """Add new component to database"""
        try:
            # Check if component already exists
            existing = self.db_session.query(SourcedComponent).filter(
                SourcedComponent.id == component.id
            ).first()
            
            if existing:
                logger.warning(f"Component {component.id} already exists")
                return False
            
            new_component = SourcedComponent(
                id=component.id,
                component_name=component.name,
                category=component.category,
                manufacturer=component.manufacturer,
                supplier=component.supplier,
                material=component.material,
                specifications=component.specifications,
                price=component.price,
                currency=component.currency,
                lead_time_days=component.lead_time_days,
                stock_availability=component.stock_availability,
                datasheet_url=component.datasheet_url,
                last_price_check=component.last_price_check,
                design_job_id=design_job_id
            )
            
            self.db_session.add(new_component)
            self.db_session.commit()
            logger.info(f"Added component {component.name} to database")
            return True
        except Exception as e:
            logger.error(f"Failed to add component: {e}")
            self.db_session.rollback()
            return False
    
    def update_prices(self, component_id: str, new_price: float) -> bool:
        """Update component price from market search"""
        try:
            component = self.db_session.query(SourcedComponent).filter(
                SourcedComponent.id == component_id
            ).first()
            
            if component:
                component.price = new_price
                component.last_price_check = datetime.utcnow()
                self.db_session.commit()
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to update price: {e}")
            self.db_session.rollback()
            return False

# ============================================================================
# Marketplace Searcher (from parts_database.py)
# ============================================================================

class MarketplaceSearcher:
    """Searches online marketplaces for parts and pricing"""
    
    def __init__(self):
        self.suppliers = {
            "digi_key": {"base_url": "https://api.digikey.com/", "api_key": None},
            "mouser": {"base_url": "https://api.mouser.com/", "api_key": None},
            "newark": {"base_url": "https://www.newark.com/", "api_key": None},
            "amazon_business": {"base_url": "https://business.amazon.com/", "api_key": None},
            "alibaba": {"base_url": "https://www.alibaba.com/", "api_key": None},
        }
    
    async def search_online(self, component_name: str, specs: Dict[str, Any],
                          budget: Optional[float] = None) -> List[Dict[str, Any]]:
        """Search multiple online marketplaces for component"""
        results = []
        
        logger.info(f"Searching online for: {component_name}")
        
        mock_results = await self._mock_marketplace_search(component_name, specs, budget)
        results.extend(mock_results)
        
        return sorted(results, key=lambda x: x["price"])
    
    async def _mock_marketplace_search(self, name: str, specs: Dict, budget: Optional[float]) -> List[Dict]:
        """Mock marketplace search (replace with real API calls)"""
        base_results = [
            {
                "name": f"{name} - Standard",
                "supplier": "Digi-Key",
                "price": 45.99,
                "currency": "USD",
                "stock": "In Stock",
                "lead_time": 1,
                "url": f"https://digikey.example.com/{name}",
                "rating": 4.8
            },
            {
                "name": f"{name} - Industrial Grade",
                "supplier": "Mouser",
                "price": 62.50,
                "currency": "USD",
                "stock": "In Stock",
                "lead_time": 2,
                "url": f"https://mouser.example.com/{name}",
                "rating": 4.9
            },
            {
                "name": f"{name} - Budget",
                "supplier": "Alibaba",
                "price": 22.00,
                "currency": "USD",
                "stock": "In Stock",
                "lead_time": 15,
                "url": f"https://alibaba.example.com/{name}",
                "rating": 3.5
            },
        ]
        
        if budget:
            base_results = [r for r in base_results if r["price"] <= budget]
        
        return base_results
    
    async def get_alternatives(self, component_name: str, specs: Dict[str, Any],
                              reason: str = "unavailable") -> List[Dict[str, Any]]:
        """Find alternative components based on specs"""
        logger.info(f"Searching alternatives for {component_name}: {reason}")
        
        alternatives = [
            {
                "name": f"{component_name} (Alternative A)",
                "similarity": 0.92,
                "price": 55.00,
                "improvements": ["Better efficiency", "Same form factor"],
                "tradeoffs": ["Slightly higher cost"]
            },
            {
                "name": f"{component_name} (Alternative B)",
                "similarity": 0.87,
                "price": 38.00,
                "improvements": ["Lower cost"],
                "tradeoffs": ["Slightly lower performance"]
            },
        ]
        
        return alternatives

# ============================================================================
# Component Sourcing Engine (from parts_database.py)
# ============================================================================

class ComponentSourcingEngine:
    """Main engine for component sourcing according to plan"""
    
    def __init__(self, db_session=None):
        self.database = PartsDatabase(db_session)
        self.marketplace = MarketplaceSearcher()
        self.sourcing_log = []
    
    async def find_component(self, component_name: str, specs: Dict[str, Any],
                            budget: Optional[float] = None,
                            max_lead_time: int = 30,
                            design_job_id: str = None) -> Tuple[Optional[ComponentPart], Dict]:
        """
        Main sourcing workflow per plan:
        1. Search local database
        2. If not found, search online marketplace
        3. Check pricing
        4. Add to database if new
        5. Return alternatives if needed
        """
        sourcing_result = {
            "component": component_name,
            "specs": specs,
            "budget": budget,
            "source": None,
            "part": None,
            "price": None,
            "alternatives": [],
            "status": "pending"
        }
        
        # Step 1: Search database
        logger.info(f"Step 1: Searching local database for {component_name}")
        category = specs.get("category", "general")
        db_results = self.database.search_by_specs(category, specs)
        
        if db_results:
            selected = db_results[0]
            sourcing_result["source"] = "database"
            sourcing_result["part"] = selected
            sourcing_result["price"] = selected.price
            sourcing_result["status"] = "found_in_database"
            logger.info(f"Found in database: {selected.name} at ${selected.price}")
            self.sourcing_log.append(sourcing_result)
            return selected, sourcing_result
        
        # Step 2: Search online marketplace
        logger.info(f"Step 2: Searching online marketplace for {component_name}")
        market_results = await self.marketplace.search_online(component_name, specs, budget)
        
        if market_results:
            selected = market_results[0]
            
            # Step 4: Add to database if new
            if not budget or selected["price"] <= budget:
                new_component = ComponentPart(
                    id=f"{component_name}_{selected['supplier']}_{datetime.utcnow().timestamp()}",
                    name=selected["name"],
                    category=category,
                    manufacturer=selected.get("manufacturer", "Unknown"),
                    supplier=selected["supplier"],
                    material=specs.get("material", "Unknown"),
                    specifications=specs,
                    price=selected["price"],
                    currency=selected.get("currency", "USD"),
                    last_price_check=datetime.utcnow(),
                    lead_time_days=selected.get("lead_time", max_lead_time),
                    stock_availability=selected.get("stock", "Unknown"),
                    datasheet_url=selected.get("url", ""),
                    compatible_with=[]
                )
                self.database.add_component(new_component, design_job_id)
                sourcing_result["source"] = "marketplace"
                sourcing_result["part"] = new_component
                sourcing_result["price"] = selected["price"]
                sourcing_result["status"] = "found_and_added"
                logger.info(f"Found online: {selected['name']} at ${selected['price']}")
                self.sourcing_log.append(sourcing_result)
                return new_component, sourcing_result
        
        # Step 5: Component not found or exceeds budget
        logger.warning(f"Component {component_name} not found or exceeds budget")
        reason = "budget_exceeded" if budget and market_results and market_results[0]["price"] > budget else "unavailable"
        alternatives = await self.marketplace.get_alternatives(component_name, specs, reason)
        
        sourcing_result["status"] = reason
        sourcing_result["alternatives"] = alternatives
        self.sourcing_log.append(sourcing_result)
        
        return None, sourcing_result

# ============================================================================
# Database Functions
# ============================================================================

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


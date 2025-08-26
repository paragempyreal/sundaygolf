import requests
from typing import Dict, List, Optional, Any
from ..models.models import Product
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone

class FulfilService:
    """Service for interacting with Fulfil's 3PL API"""
    
    def __init__(self, subdomain: str, api_key: str):
        self.subdomain = subdomain
        self.api_key = api_key
        self.base_url = f"https://{subdomain}.fulfil.io/services/3pl/v1"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "accept": "application/json"
        }
    
    def get_products(self, page: int = 1, per_page: int = 50, updated_at_min: Optional[str] = None, updated_at_max: Optional[str] = None) -> Dict[str, Any]:
        """
        Fetch products from Fulfil API with optional date filters
        
        Args:
            page: Page number to fetch
            per_page: Number of products per page
            updated_at_min: Minimum updated date (ISO format)
            updated_at_max: Maximum updated date (ISO format)
            
        Returns:
            Dict containing products and pagination info
        """
        url = f"{self.base_url}/products.json"
        params = {
            "page": page,
            "per_page": per_page
        }
        
        # Add date filters if provided
        if updated_at_min:
            params["updated_at_min"] = updated_at_min
        if updated_at_max:
            params["updated_at_max"] = updated_at_max
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to fetch products from Fulfil: {str(e)}")
    
    def _extract_products(self, data: Any) -> List[Dict[str, Any]]:
        """Extract product list from various possible response shapes."""
        if isinstance(data, list):
            return data  # API returned a raw list of products
        if not isinstance(data, dict):
            return []
        # Common keys used by APIs for list payloads
        for key in ("data", "products", "results", "items"):
            value = data.get(key)
            if isinstance(value, list):
                return value
        return []
    
    def _has_more_pages(self, data: Any, products_count: int, per_page: int) -> bool:
        """Best-effort detection of additional pages across common response shapes."""
        if isinstance(data, dict):
            # next URL style
            if data.get("next"):
                return True
            # has_more boolean style
            if data.get("has_more") is True:
                return True
            # page/total_pages style
            page = data.get("page")
            total_pages = data.get("total_pages")
            if isinstance(page, int) and isinstance(total_pages, int):
                return page < total_pages
        # Fallback: if we got a full page, there might be more
        return products_count >= per_page
    
    def get_all_products(self, updated_at_min: Optional[str] = None, updated_at_max: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Fetch all products from Fulfil API with optional date filters
        
        Args:
            updated_at_min: Minimum updated date (ISO format)
            updated_at_max: Maximum updated date (ISO format)
            
        Returns:
            List of all products
        """
        all_products = []
        page = 1
        per_page = 50
        
        while True:
            data = self.get_products(page, per_page, updated_at_min, updated_at_max)
            products = self._extract_products(data)
            
            if not products:
                break
                
            all_products.extend(products)
            
            # Check if there are more pages
            if not self._has_more_pages(data, len(products), per_page):
                break
                
            page += 1
        
        return all_products
    
    def get_products_for_initial_sync(self) -> List[Dict[str, Any]]:
        """
        Fetch all products for initial sync (no date filters)
        
        Returns:
            List of all products
        """
        return self.get_all_products()
    
    def get_products_for_incremental_sync(self, last_sync_time: datetime) -> List[Dict[str, Any]]:
        """
        Fetch products updated since the last sync
        
        Args:
            last_sync_time: Last sync timestamp
            
        Returns:
            List of updated products
        """
        # Format the last sync time for the API
        updated_at_min = last_sync_time.strftime("%Y-%m-%dT%H:%M:%S")
        # Set max to current time
        updated_at_max = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
        
        return self.get_all_products(updated_at_min, updated_at_max)
    
    def parse_product_data(self, fulfil_product: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse Fulfil product data into our internal format
        
        Args:
            fulfil_product: Raw product data from Fulfil API
            
        Returns:
            Parsed product data
        """
        # Extract codes (UPC, ASIN, Buyer SKU)
        upc = None
        asin = None
        buyer_sku = None
        
        codes = fulfil_product.get("codes", [])
        for code in codes:
            if code.get("type") == "upc":
                upc = code.get("value")
            elif code.get("type") == "asin":
                asin = code.get("value")
            elif code.get("type") == "buyer_sku":
                buyer_sku = code.get("value")
        
        # Extract weight information
        weight_gm = None
        weight_oz = None
        weight_data = fulfil_product.get("weight", {})
        if weight_data:
            weight_gm = weight_data.get("weight_gm")
            weight_oz = weight_data.get("weight_oz")
        
        # Extract dimensions
        length_cm = None
        width_cm = None
        height_cm = None
        length_in = None
        width_in = None
        height_in = None
        
        dimensions_data = fulfil_product.get("dimensions", {})
        if dimensions_data:
            length_cm = dimensions_data.get("length_cm")
            width_cm = dimensions_data.get("width_cm")
            height_cm = dimensions_data.get("height_cm")
            length_in = dimensions_data.get("length_in")
            width_in = dimensions_data.get("width_in")
            height_in = dimensions_data.get("height_in")
        
        # Extract customs information
        hs_code = None
        country_of_origin = None
        customs_description = None
        
        customs_info = fulfil_product.get("customs_information", {})
        if customs_info:
            hs_code = customs_info.get("hs_code")
            country_of_origin = customs_info.get("country_of_origin")
            customs_description = customs_info.get("customs_description")
        
        return {
            "fulfil_id": fulfil_product.get("id"),
            "code": fulfil_product.get("code"),
            "name": fulfil_product.get("name"),
            "template_name": fulfil_product.get("template_name"),
            "category_name": fulfil_product.get("category_name"),
            "variant_name": fulfil_product.get("name"),  # Using name as variant name
            "upc": upc,
            "asin": asin,
            "buyer_sku": buyer_sku,
            "weight_gm": weight_gm,
            "weight_oz": weight_oz,
            "length_cm": length_cm,
            "width_cm": width_cm,
            "height_cm": height_cm,
            "length_in": length_in,
            "width_in": width_in,
            "height_in": height_in,
            "dimension_unit": "cm",  # Defaulting to cm
            "weight_uom": "gm",  # Defaulting to grams
            "country_of_origin": country_of_origin,
            "hs_code": hs_code,
            "customs_description": customs_description,
            "quantity_per_case": fulfil_product.get("quantity_per_case"),
            "unit_of_measure": "each",  # Defaulting to each
            "image_url": fulfil_product.get("image_url")
        }

# Global instance
fulfil_service = None
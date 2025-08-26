import requests
from typing import Dict, Any, Optional, List
from ..models.models import Product
from sqlalchemy.orm import Session
import logging

class ShipHeroService:
    """Service for interacting with ShipHero's GraphQL API"""
    
    def __init__(self, refresh_token: str, oauth_url: str, api_base_url: str):
        self.refresh_token = refresh_token
        self.oauth_url = oauth_url
        self.api_base_url = api_base_url
        self.access_token = None
        self.logger = logging.getLogger(__name__)
        # Defaults that will be overridden by introspection (best-guess for ShipHero)
        self.create_input_arg_name = 'data'
        self.create_input_type_name = 'CreateProductInput'
        # For update, some schemas require an explicit id arg (e.g., id/legacy_id/sku),
        # while others accept only a single input object containing the identifier (e.g., sku inside data)
        # Default to None so we don't wrongly assume an id arg exists
        self.update_id_arg_name = None
        self.update_id_type_name = 'ID'
        self.update_input_arg_name = 'data'
        self.update_input_type_name = 'UpdateProductInput'
        self._authenticate()
        self._detect_product_mutation_shapes()
    
    def _authenticate(self) -> None:
        """Authenticate with ShipHero OAuth to get access token"""
        try:
            response = requests.post(
                self.oauth_url,
                json={
                    "refresh_token": self.refresh_token
                }
            )
            response.raise_for_status()
            data = response.json()
            self.access_token = data.get("access_token")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to authenticate with ShipHero: {str(e)}")
    
    def _deep_type_name(self, type_obj: Dict[str, Any]) -> str:
        while type_obj:
            if type_obj.get('name'):
                return type_obj['name']
            type_obj = type_obj.get('ofType') or {}
        return ''
    
    def _is_non_null(self, type_obj: Dict[str, Any]) -> bool:
        kind = type_obj.get('kind')
        if kind == 'NON_NULL':
            return True
        inner = type_obj.get('ofType') or {}
        return inner.get('kind') == 'NON_NULL'
    
    def _get_input_fields(self, type_name: str) -> List[Dict[str, Any]]:
        try:
            q = f"""
            query GetInput($name: String!) {{
              __type(name: $name) {{
                name
                inputFields {{
                  name
                  type {{ kind name ofType {{ kind name ofType {{ kind name }} }} }}
                }}
              }}
            }}
            """
            resp = self._make_request(q, {"name": type_name})
            return (resp.get('data', {})
                        .get('__type', {})
                        .get('inputFields', []))
        except Exception as e:
            self.logger.warning(f"Failed to introspect input type {type_name}: {e}")
            return []

    def _filter_input_payload(self, input_type_name: str, payload: Any) -> Any:
        """Filter a payload dict to only include fields allowed by the given input type.

        Handles nested input objects and lists recursively using schema introspection.
        """
        if payload is None:
            return None
        # Only dicts and lists need filtering; primitives pass through
        if not isinstance(payload, (dict, list)):
            return payload
        try:
            # When payload is a list, determine inner input type name from provided type
            if isinstance(payload, list):
                # For lists, we cannot infer element type without the field context; return as-is
                # since we only call this for nested fields where element types are already correct
                return [self._filter_input_payload(input_type_name, item) for item in payload]

            # payload is a dict
            input_fields = self._get_input_fields(input_type_name)
            allowed_by_name: Dict[str, Dict[str, Any]] = {f.get('name'): f for f in input_fields}
            filtered: Dict[str, Any] = {}
            for key, value in payload.items():
                fdef = allowed_by_name.get(key)
                if not fdef:
                    # Drop unknown field
                    continue
                # Determine nested input type if value is dict/list
                if isinstance(value, (dict, list)):
                    type_obj = fdef.get('type', {})
                    nested_type_name = self._deep_type_name(type_obj)
                    filtered[key] = self._filter_input_payload(nested_type_name, value)
                else:
                    filtered[key] = value
            return filtered
        except Exception as e:
            # On any introspection failure, prefer sending the original payload
            self.logger.warning(f"Failed filtering payload for {input_type_name}: {e}")
            return payload
    
    def _detect_product_mutation_shapes(self) -> None:
        """Introspect GraphQL schema to detect actual input types and arg names for product mutations."""
        try:
            introspection_query = """
            query Introspect {
              __schema {
                mutationType {
                  fields {
                    name
                    args {
                      name
                      type { kind name ofType { kind name ofType { kind name } } }
                    }
                  }
                }
              }
            }
            """
            resp = self._make_request(introspection_query)
            fields = (resp.get('data', {})
                        .get('__schema', {})
                        .get('mutationType', {})
                        .get('fields', []))
            def find_field(name: str):
                for f in fields:
                    if f.get('name') == name:
                        return f
                return None
            create_field = find_field('product_create')
            update_field = find_field('product_update')
            # Detect input arg name and type for create
            if create_field:
                for arg in create_field.get('args', []):
                    tname = self._deep_type_name(arg.get('type', {}) )
                    if 'Input' in tname or tname.endswith('Input'):
                        self.create_input_arg_name = arg.get('name', self.create_input_arg_name)
                        self.create_input_type_name = tname
                        break
            # Detect id arg name/type and input arg/type for update
            if update_field:
                # Prefer id, then legacy_id, then sku if present
                id_candidates = {}
                for arg in update_field.get('args', []):
                    tname = self._deep_type_name(arg.get('type', {}))
                    if tname in ['ID', 'String']:
                        id_candidates[arg.get('name', '')] = tname
                    if 'Input' in tname or tname.endswith('Input'):
                        self.update_input_arg_name = arg.get('name', self.update_input_arg_name)
                        self.update_input_type_name = tname
                for pref in ['id', 'legacy_id', 'sku', 'product_id']:
                    if pref in id_candidates:
                        self.update_id_arg_name = pref
                        self.update_id_type_name = id_candidates[pref]
                        break
            # Log detected shapes
            self.logger.info(
                f"ShipHero schema: create({self.create_input_arg_name}: {self.create_input_type_name}), "
                f"update({self.update_id_arg_name}: {self.update_id_type_name}, {self.update_input_arg_name}: {self.update_input_type_name})"
            )
        except Exception as e:
            # Non-fatal; fall back to defaults
            self.logger.warning(f"Failed to introspect ShipHero schema; using defaults. Reason: {e}")
    
    def _make_request(self, query: str, variables: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Make a GraphQL request to ShipHero API
        
        Args:
            query: GraphQL query string
            variables: Variables for the query
            
        Returns:
            Response data from ShipHero API
        """
        if not self.access_token:
            self._authenticate()
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "query": query
        }
        
        if variables:
            payload["variables"] = variables
        
        try:
            response = requests.post(
                f"{self.api_base_url}/graphql",
                json=payload,
                headers=headers
            )
            if not response.ok:
                raise Exception(f"HTTP {response.status_code} from ShipHero: {response.text}")
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to make request to ShipHero: {str(e)}")
    
    def _get_default_warehouse_id(self) -> Optional[str]:
        """Fetch a warehouse id to use for create payloads when required."""
        try:
            query = """
            query Warehouses {
              warehouses {
                request_id
                data {
                  id
                  legacy_id
                  name
                }
              }
            }
            """
            resp = self._make_request(query)
            data_list = resp.get('data', {}).get('warehouses', {}).get('data', [])
            if data_list:
                # Prefer id if available
                return data_list[0].get('id') or data_list[0].get('legacy_id')
        except Exception as e:
            self.logger.warning(f"Failed to fetch warehouses: {e}")
        return None
    
    def _ensure_required_create_fields(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure required fields for create mutation are present (e.g., warehouse_products)."""
        # Introspect create input type fields
        fields = self._get_input_fields(self.create_input_type_name)
        required_field_names = set()
        subfield_types: Dict[str, str] = {}
        for f in fields:
            if self._is_non_null(f.get('type', {})):
                required_field_names.add(f.get('name'))
            # Capture type name for sub-inputs
            tname = self._deep_type_name(f.get('type', {}))
            if tname:
                subfield_types[f.get('name')] = tname
        # If warehouse_products is required and missing, add minimal entry
        if 'warehouse_products' in required_field_names and not product_data.get('warehouse_products'):
            wh_id = self._get_default_warehouse_id()
            if wh_id:
                # Introspect warehouse product input for required fields
                wp_input_type = subfield_types.get('warehouse_products') or 'CreateWarehouseProductInput'
                wp_fields = self._get_input_fields(wp_input_type)
                wp_required = {f.get('name') for f in wp_fields if self._is_non_null(f.get('type', {}))}
                wp: Dict[str, Any] = {}
                if 'warehouse_id' in wp_required:
                    wp['warehouse_id'] = wh_id
                # Provide safe defaults for common required fields if present
                if 'on_hand' in wp_required:
                    wp['on_hand'] = 0
                if 'reorder_level' in wp_required:
                    wp['reorder_level'] = 0
                if 'price' in wp_required:
                    wp['price'] = "0.00"
                product_data['warehouse_products'] = [wp]
            else:
                self.logger.warning("ShipHero create requires warehouse_products but no warehouse_id available.")
        return product_data
    
    def create_product(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a product in ShipHero
        
        Args:
            product_data: Product data to create
            
        Returns:
            Created product data
        """
        arg_name = self.create_input_arg_name
        input_type = self.create_input_type_name
        safe_data = self._ensure_required_create_fields(dict(product_data))
        mutation = f"""
        mutation ($data: {input_type}!) {{
          product_create({arg_name}: $data) {{
            request_id
            complexity
            product {{
              id
              legacy_id
              account_id
              name
              sku
              barcode
              country_of_manufacture
              dimensions {{
                weight
                height
                width
                length
              }}
              tariff_code
              kit
              kit_build
              no_air
              final_sale
              customs_value
              customs_description
              not_owned
              dropship
              created_at
            }}
          }}
        }}
        """
        
        variables = {
            "data": safe_data
        }
        
        response = self._make_request(mutation, variables)
        
        if "errors" in response:
            raise Exception(f"Failed to create product in ShipHero: {response['errors']}")
        
        return response.get("data", {}).get("product_create", {})
    
    def update_product(self, identifier: Optional[str], product_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update a product in ShipHero
        
        Args:
            identifier: ShipHero product identifier (ID/SKU/etc. based on schema)
            product_data: Product data to update
            
        Returns:
            Updated product data
        """
        id_arg = self.update_id_arg_name
        id_type = self.update_id_type_name
        arg_name = self.update_input_arg_name
        input_type = self.update_input_type_name

        # Some ShipHero schemas expect only a single input object with sku inside data
        # Proactively strip fields that are commonly unavailable on update inputs
        disallowed_on_update = {
            'kit', 'kit_build', 'no_air', 'customs_value', 'not_owned', 'dropship'
        }
        base_payload = {k: v for k, v in dict(product_data).items() if k not in disallowed_on_update}

        if not id_arg:
            # Filter fields according to detected input type
            safe_data = self._filter_input_payload(input_type, base_payload)
            # Ensure sku is included when identifier points to SKU
            if 'sku' not in safe_data and identifier:
                safe_data['sku'] = identifier
            mutation = f"""
            mutation ($data: {input_type}!) {{
              product_update({arg_name}: $data) {{
                request_id
                complexity
                product {{
                  id
                  legacy_id
                  account_id
                  name
                  sku
                  barcode
                  country_of_manufacture
                  dimensions {{
                    weight
                    height
                    width
                    length
                  }}
                  tariff_code
                  kit
                  kit_build
                  no_air
                  final_sale
                  customs_value
                  customs_description
                  not_owned
                  dropship
                  created_at
                }}
              }}
            }}
            """
            variables = {
                "data": safe_data
            }
        else:
            # Filter fields according to detected input type
            safe_product_data = self._filter_input_payload(input_type, base_payload)
            mutation = f"""
            mutation (${id_arg}: {id_type}!, $data: {input_type}!) {{
              product_update({id_arg}: ${id_arg}, {arg_name}: $data) {{
                request_id
                complexity
                product {{
                  id
                  legacy_id
                  account_id
                  name
                  sku
                  barcode
                  country_of_manufacture
                  dimensions {{
                    weight
                    height
                    width
                    length
                  }}
                  tariff_code
                  kit
                  kit_build
                  no_air
                  final_sale
                  customs_value
                  customs_description
                  not_owned
                  dropship
                  created_at
                }}
              }}
            }}
            """
            variables = {
                id_arg: identifier,
                "data": safe_product_data
            }
        
        response = self._make_request(mutation, variables)
        
        if "errors" in response:
            raise Exception(f"Failed to update product in ShipHero: {response['errors']}")
        
        return response.get("data", {}).get("product_update", {})
    
    def get_product_by_sku(self, sku: str) -> Optional[Dict[str, Any]]:
        """
        Get a product from ShipHero by SKU
        
        Args:
            sku: Product SKU
            
        Returns:
            Product data if found, None otherwise
        """
        query = """
        query ($sku: String!) {
          products(sku: $sku) {
            request_id
            data {
              edges {
                node {
                  id
                  legacy_id
                  account_id
                  name
                  sku
                  barcode
                  country_of_manufacture
                  dimensions {
                    weight
                    height
                    width
                    length
                  }
                  tariff_code
                  kit
                  kit_build
                  no_air
                  final_sale
                  customs_value
                  customs_description
                  not_owned
                  dropship
                  created_at
                }
              }
            }
          }
        }
        """
        
        variables = {
            "sku": sku
        }
        
        response = self._make_request(query, variables)
        
        if "errors" in response:
            raise Exception(f"Failed to get product from ShipHero: {response['errors']}")
        
        products_obj = response.get("data", {}).get("products", {})
        data_section = products_obj.get("data")
        
        # Newer schema: data is a connection with edges -> node
        if isinstance(data_section, dict):
            edges = data_section.get("edges", [])
            if edges:
                node = edges[0].get("node")
                if node:
                    return node
        
        # Older/alternate schema: data is a list of products
        if isinstance(data_section, list) and len(data_section) > 0:
            return data_section[0]
        
        return None

# Global instance
shiphero_service = None
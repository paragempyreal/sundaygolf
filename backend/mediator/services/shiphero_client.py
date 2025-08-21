import requests
from datetime import datetime, timedelta, timezone

PRODUCT_CREATE = """
mutation ProductCreate($input: ProductCreateInput!) {
  product_create(data: $input) {
    request_id
    product { id sku }
    errors { message sku field }
  }
}
"""

PRODUCT_UPDATE = """
mutation ProductUpdate($input: ProductUpdateInput!) {
  product_update(data: $input) {
    request_id
    product { id sku }
    errors { message sku field }
  }
}
"""



class ShipHeroClient:
    def __init__(self, refresh_token: str, oauth_url: str = "https://public-api.shiphero.com/oauth", base_url: str = "https://public-api.shiphero.com"):
        self.refresh_token = refresh_token
        self.oauth_url = oauth_url
        self.base_url = base_url
        self.endpoint = f"{base_url}/graphql"

    def test_connection(self):
        """Test connection to ShipHero API"""
        try:
            # This is a placeholder test - in production you would make an actual API call
            if not self.refresh_token:
                return False
            # For now, just return True if refresh token is present
            return True
        except Exception:
            return False

    def _headers(self):
        # Placeholder implementation for token management
        # In production, you would implement proper OAuth flow
        return {"Authorization": f"Bearer {self.refresh_token}"}

    def _refresh(self, token):
        """Implement OAuth refresh flow per ShipHero documentation"""
        refresh_url = f"{self.oauth_url}/refresh"
        data = {
            "refresh_token": token["refresh_token"]
        }
        
        try:
            response = requests.post(refresh_url, json=data, timeout=30)
            response.raise_for_status()
            
            new_tokens = response.json()
            updated_token = {
                "access_token": new_tokens["access_token"],
                "refresh_token": new_tokens.get("refresh_token", token["refresh_token"]),
                "expires_at": datetime.now(timezone.utc) + timedelta(seconds=new_tokens["expires_in"])
            }
            
            return updated_token
            
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Failed to refresh ShipHero token: {e}")

    def graphql(self, query, variables):
        r = requests.post(
            self.endpoint, 
            json={"query": query, "variables": variables}, 
            headers=self._headers(), 
            timeout=30
        )
        r.raise_for_status()
        return r.json()

    def create(self, payload):
        return self.graphql(PRODUCT_CREATE, {"input": payload})

    def update(self, payload):
        return self.graphql(PRODUCT_UPDATE, {"input": payload})

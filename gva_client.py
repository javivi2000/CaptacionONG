import requests
import logging

class GVAClient:
    def __init__(self, base_url="https://dadesobertes.gva.es/api/3/action/datastore_search"):
        self.base_url = base_url
        self.logger = logging.getLogger(__name__)

    def fetch_resource(self, resource_id, filters=None, q=None, limit=100, offset=0):
        """
        Consulta un recurso específico de la GVA usando datastore_search.
        """
        params = {
            "resource_id": resource_id,
            "limit": limit,
            "offset": offset
        }
        if filters:
            import json
            params["filters"] = json.dumps(filters)
        if q:
            params["q"] = q
            
        try:
            response = requests.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            if data.get("success"):
                return data["result"]
            else:
                self.logger.error(f"Error en API GVA: {data.get('error')}")
                return None
        except Exception as e:
            self.logger.error(f"Error conectando con GVA: {e}")
            return None

    def search_all_pages(self, resource_id, filters=None, q=None, max_records=500):
        """
        Paginación automática hasta llegar al límite.
        """
        all_records = []
        offset = 0
        limit = 100
        
        while len(all_records) < max_records:
            result = self.fetch_resource(resource_id, filters, q, limit, offset)
            if not result or not result.get("records"):
                break
                
            records = result["records"]
            all_records.extend(records)
            
            if len(records) < limit:
                break
            offset += limit
            
        return all_records[:max_records]

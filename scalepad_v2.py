import os
import json
import requests
from dotenv import load_dotenv
from utils.logger import logger


class ScalePadV2Client:
    """
    Generic ScalePad API v2 client.
    Handles authentication and basic HTTP methods only.
    """

    def __init__(self, api_key=None, base_url="https://api.scalepad.com"):
        load_dotenv()

        self.api_key = api_key or os.getenv("SCALEPAD_API_KEY")
        if not self.api_key:
            raise ValueError("Missing SCALEPAD_API_KEY")

        self.base_url = base_url.rstrip("/")

        self.session = requests.Session()
        self.session.headers.update({
            "accept": "application/json",
            "content-type": "application/json",
            "x-api-key": self.api_key,
        })

    def _request(self, method, path, **kwargs):
        url = f"{self.base_url}/{path.lstrip('/')}"

        try:
            response = self.session.request(
                method=method,
                url=url,
                timeout=30,
                **kwargs
            )

            response.raise_for_status()

            if not response.text:
                return None

            return response.json()

        except requests.HTTPError as e:
            logger.error(f"ScalePad API error {response.status_code}: {response.text}")
            raise RuntimeError(
                f"ScalePad API error {response.status_code}: {response.text}"
            ) from e

        except requests.RequestException as e:
            logger.error(f"ScalePad connection error: {e}")
            raise

    def get(self, path, params=None):
        return self._request("GET", path, params=params)

    def post(self, path, data=None):
        return self._request("POST", path, json=data)

    def put(self, path, data=None):
        return self._request("PUT", path, json=data)

    def patch(self, path, data=None):
        return self._request("PATCH", path, json=data)

    def delete(self, path):
        return self._request("DELETE", path)


if __name__ == "__main__":
    logger.info("========================================")
    logger.info("Testing ScalePad API v2")
    logger.info("========================================")

    client = ScalePadV2Client()

#    endpoint = "/quoter/v1/quote-templates"
#    endpoint = "/quoter/v1/quotes"
    endpoint = "/quoter/v1/contracts"
#    endpoint = "/quoter/v1/customers"
#    endpoint = "/quoter/v1/products"

    try:
        result = client.get(endpoint)

        logger.info("✅ ScalePad API connection successful")
        logger.info(f"Endpoint: {endpoint}")

        if isinstance(result, dict):
            logger.info(f"Top-level keys: {list(result.keys())}")

            if "data" in result:
#                logger.info(f"Returned records: {len(result['data'])}")
                logger.info(f"Returned records: {len(result.get('data', []))}")

            if "next_cursor" in result:
                logger.info(f"Next cursor: {result['next_cursor']}")

            if "total_count" in result:
                logger.info(f"Total records: {result['total_count']}")

        print(json.dumps(result, indent=2))
    except Exception:
        logger.exception("❌ ScalePad API test failed")

import logging
import httpx # Make sure you have httpx installed: pip install httpx

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def is_online(test_url: str = "http://www.google.com", timeout: int = 5) -> bool:
    """
    Asynchronously checks if there is an active internet connection by attempting to reach a test URL.
    Uses httpx for non-blocking HTTP requests.
    Returns True if online, False otherwise.
    """
    try:
        # Use httpx.AsyncClient for asynchronous HTTP requests
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(test_url)
            response.raise_for_status() # Raises HTTPStatusError for 4xx/5xx responses
            logger.info(f"Network connection available to {test_url}")
            return True
    except httpx.RequestError as exc:
        logger.warning(f"Network connection failed for {test_url}: {exc}")
        return False
    except httpx.HTTPStatusError as exc:
        logger.warning(f"Network connection received HTTP error {exc.response.status_code} from {test_url}: {exc}")
        return False
    except Exception as e:
        logger.error(f"An unexpected error occurred during network check: {e}")
        return False
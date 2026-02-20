from patchright_airbnb_scraper import PatchrightAirbnbScraper

class SmartAirbnbScraper(PatchrightAirbnbScraper):
    """
    Alias for PatchrightAirbnbScraper to maintain compatibility
    with holland_agent.py and other components.
    """
    async def search_airbnb(self, region, checkin, checkout, adults=4):
        return await super().search_airbnb(region, checkin, checkout, adults)

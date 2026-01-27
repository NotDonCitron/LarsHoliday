"""
Favorites Manager for Vacation Deal Finder
Handles persistence of favorite deals using a JSON file.
"""

import json
import os
from typing import List, Dict

class FavoritesManager:
    def __init__(self, storage_path: str = "favorites.json"):
        self.storage_path = storage_path
        self.favorites = self.load_favorites()

    def load_favorites(self) -> List[Dict]:
        """Load favorites from the JSON file."""
        if not os.path.exists(self.storage_path):
            return []
        try:
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []

    def save_favorites(self):
        """Save the current list of favorites to the JSON file."""
        try:
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump(self.favorites, f, indent=4, ensure_ascii=False)
        except IOError as e:
            print(f"Error saving favorites: {e}")

    def add_favorite(self, deal: Dict) -> bool:
        """Add a deal to favorites if it doesn't already exist."""
        # Check if already in favorites by comparing URLs or Name+Location
        deal_url = deal.get('url')
        
        for fav in self.favorites:
            if deal_url and fav.get('url') == deal_url:
                return False
            if not deal_url and fav.get('name') == deal.get('name') and fav.get('location') == deal.get('location'):
                return False
        
        # Add timestamp
        deal_to_save = deal.copy()
        deal_to_save['date_added'] = json.dumps(str(type(deal_to_save))) # placeholder for metadata
        # Actually just add it
        self.favorites.append(deal_to_save)
        self.save_favorites()
        return True

    def remove_favorite(self, deal_url: str) -> bool:
        """Remove a deal from favorites by its URL."""
        initial_count = len(self.favorites)
        self.favorites = [f for f in self.favorites if f.get('url') != deal_url]
        
        if len(self.favorites) < initial_count:
            self.save_favorites()
            return True
        return False

    def get_all(self) -> List[Dict]:
        """Return all favorites."""
        return self.favorites

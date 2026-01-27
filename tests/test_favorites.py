
import os
import json
from favorites_manager import FavoritesManager

def test_favorites_persistence():
    test_file = "test_favorites.json"
    if os.path.exists(test_file):
        os.remove(test_file)
        
    manager = FavoritesManager(storage_path=test_file)
    deal = {"name": "Test Hotel", "url": "http://test.com", "price_per_night": 100, "location": "Test City"}
    
    # Add
    manager.add_favorite(deal)
    assert len(manager.get_all()) == 1
    
    # Persistence
    new_manager = FavoritesManager(storage_path=test_file)
    assert len(new_manager.get_all()) == 1
    assert new_manager.get_all()[0]['name'] == "Test Hotel"
    
    # Remove
    new_manager.remove_favorite("http://test.com")
    assert len(new_manager.get_all()) == 0
    
    os.remove(test_file)
    print("Favorites persistence test passed!")

if __name__ == "__main__":
    test_favorites_persistence()

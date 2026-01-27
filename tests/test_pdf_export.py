
import os
from report_generator import ReportGenerator

def test_pdf_generation():
    generator = ReportGenerator()
    
    deals = [
        {
            "name": "Test Hotel 1",
            "location": "Berlin",
            "price_per_night": 100,
            "rating": 4.5,
            "reviews": 120,
            "source": "booking",
            "pet_friendly": True,
            "url": "http://example.com/1"
        },
        {
            "name": "Test Apartment 2",
            "location": "Paris",
            "price_per_night": 200,
            "rating": 4.8,
            "reviews": 50,
            "source": "airbnb",
            "pet_friendly": True,
            "url": "http://example.com/2"
        }
    ]
    
    search_params = {
        "cities": ["Berlin", "Paris"],
        "checkin": "2026-06-01",
        "checkout": "2026-06-07",
        "nights": 6,
        "group_size": 2,
        "pets": 1,
        "budget_range": "EUR 50-250"
    }
    
    filename = "test_report.pdf"
    if os.path.exists(filename):
        os.remove(filename)
        
    success = generator.generate_report(deals, search_params, filename)
    
    assert success
    assert os.path.exists(filename)
    
    # Check file size is not empty
    assert os.path.getsize(filename) > 0
    
    # Cleanup
    os.remove(filename)
    print("PDF generation test passed!")

if __name__ == "__main__":
    test_pdf_generation()

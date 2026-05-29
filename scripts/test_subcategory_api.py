import requests

BASE_URL = "http://localhost:8000"

def test_subcategory():
    print("Fetching existing subcategories...")
    response = requests.get(f"{BASE_URL}/complaint-subcategories")
    if response.status_code != 200:
        print(f"FAILED to fetch subcategories: {response.text}")
        return
    
    subcategories = response.json()
    print(f"Found {len(subcategories)} subcategories.")
    
    if not subcategories:
        print("No subcategories found in DB. Creating one for testing...")
        # Get a category first
        cat_resp = requests.get(f"{BASE_URL}/complaint-categories")
        categories = cat_resp.json()
        if not categories:
            print("No categories found to link subcategory to. Test skipped.")
            return
        
        cat_id = categories[0]['id']
        create_payload = {
            "category_id": cat_id,
            "name": "Test Subcategory",
            "description": "Initial test description",
            "status": "Active"
        }
        create_resp = requests.post(f"{BASE_URL}/complaint-subcategories", json=create_payload)
        if create_resp.status_code != 200:
            print(f"FAILED to create test subcategory: {create_resp.text}")
            return
        print("Successfully created test subcategory!")
        subcategories = [create_resp.json()]

    # Test updating the description
    subcat = subcategories[0]
    subcat_id = subcat['id']
    original_description = subcat.get('description')
    print(f"Updating subcategory ID {subcat_id}...")
    
    update_payload = {
        "category_id": subcat['category_id'],
        "name": subcat['name'],
        "description": "Updated subcategory test description",
        "status": subcat['status']
    }
    
    update_resp = requests.put(f"{BASE_URL}/complaint-subcategories/{subcat_id}", json=update_payload)
    if update_resp.status_code != 200:
        print(f"FAILED to update subcategory description: {update_resp.text}")
        return
    
    updated_subcat = update_resp.json()
    print("Update Response:", updated_subcat)
    
    if updated_subcat.get('description') == "Updated subcategory test description":
        print("SUCCESS: Description was updated successfully!")
    else:
        print("FAILED: Description in response does not match the updated value.")
        
    # Revert it back to original description
    revert_payload = {
        "category_id": subcat['category_id'],
        "name": subcat['name'],
        "description": original_description,
        "status": subcat['status']
    }
    requests.put(f"{BASE_URL}/complaint-subcategories/{subcat_id}", json=revert_payload)
    print("Reverted description back to original.")

if __name__ == "__main__":
    test_subcategory()

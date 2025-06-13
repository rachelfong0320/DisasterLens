"""
This script defines a utility function to determine whether a given user location is in Malaysia.

Features:
- Contains a predefined list of Malaysian locations and states (in lowercase) as keywords.
- Provides `is_location_in_malaysia(location)` function that:
    - Converts the input location string to lowercase.
    - Checks if any Malaysian keyword is present in the location string.
    - Returns `True` if a match is found, otherwise `False`.

Use Case:
- Useful for filtering tweets to include only those originating from Malaysian locations.
"""

malaysia_keywords = [
        "malaysia", "kuala lumpur", "selangor", "johor", "penang", "pulau pinang",
        "perak", "kedah", "pahang", "terengganu", "kelantan", "melaka", "negeri sembilan",
        "sabah", "sarawak", "labuan", "putrajaya", "cyberjaya", "langkawi", "ipoh", "alor setar",
        "george town", "kuantan", "kuching", "kota kinabalu", "bintulu", "sibu", "miri"
    ]

def is_location_in_malaysia(location: str) -> bool:
    if not location:
        return False
    location = location.lower()
    return any(keyword in location for keyword in malaysia_keywords)

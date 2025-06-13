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

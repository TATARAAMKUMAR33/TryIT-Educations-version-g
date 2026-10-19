import random

NAMES = ["Aarav", "Vivaan", "Aditya", "Vihaan", "Arjun", "Sai", "Reyansh", "Ayaan", "Krishna", "Ishaan", "Diya", "Saanvi", "Ananya", "Aadhya", "Pari", "Anika", "Navya", "Avni", "Myra", "Sara", "Rohan", "Rahul", "Amit", "Priya", "Neha", "Pooja", "Ravi", "Kiran", "Sanjay", "Meera", "Karthik", "Sneha", "Vikram", "Riya", "Manish", "Kavya", "Deepak", "Nisha", "Ramesh", "Divya", "Harish", "Lakshmi", "Gopal", "Radha", "Suresh", "Anjali", "Vijay", "Kavita"]
CITIES = ["Mumbai", "Delhi", "Bengaluru", "Hyderabad", "Ahmedabad", "Chennai", "Kolkata", "Surat", "Pune", "Jaipur", "Lucknow", "Kanpur", "Nagpur", "Indore", "Thane", "Bhopal", "Visakhapatnam", "Patna", "Vadodara", "Ghaziabad", "Ludhiana", "Agra", "Nashik", "Faridabad", "Meerut", "Rajkot", "Varanasi", "Srinagar", "Aurangabad", "Amritsar", "Ranchi", "Coimbatore", "Jabalpur", "Gwalior", "Vijayawada", "Jodhpur", "Madurai", "Raipur", "Kota", "Guwahati"]
FESTIVALS = ["Diwali", "Holi", "Eid", "Christmas", "Pongal", "Onam", "Bihu", "Navratri", "Durga Puja", "Ganesh Chaturthi", "Makar Sankranti", "Vaisakhi", "Lohri", "Raksha Bandhan", "Janmashtami", "Maha Shivaratri", "Ugadi", "Chhath Puja"]
OCCUPATIONS = ["farmer", "teacher", "engineer", "doctor", "shopkeeper", "artisan", "weaver", "potter", "carpenter", "tailor", "driver", "chef", "scientist", "student", "professor", "banker", "police officer", "pilot", "astronaut"]
FOODS = ["samosa", "dosa", "biryani", "paneer tikka", "chole bhature", "idli", "vada pav", "pav bhaji", "rasgulla", "gulab jamun", "jalebi", "dhokla", "pongal", "momos", "pakora", "kheer", "halwa", "paratha", "poha"]

def get_context(topic_name=""):
    name = random.choice(NAMES)
    city = random.choice(CITIES)
    festival = random.choice(FESTIVALS)
    occupation = random.choice(OCCUPATIONS)
    food = random.choice(FOODS)
    
    scenarios = [
        f"{name}, a {occupation} from {city}, is organizing a stall for the {festival} festival and needs to buy {food}.",
        f"During the {festival} celebrations in {city}, {name} (a {occupation}) is calculating the total cost of distributing {food}.",
        f"{name}, a {occupation} living in {city}, is traveling to their village for {festival} and is packing {food}.",
        f"A group of students in {city}, led by {name}, are preparing a budget for a {festival} event and ordering {food}.",
        f"{name} is a {occupation} in {city} who is planning a {festival} party and buying {food}.",
        f"A {occupation} named {name} in {city} is building a wooden structure for the {festival} festival while sharing {food}."
    ]
    
    return f"CRITICAL INSTRUCTION: Frame the entire question around this exact scenario: {random.choice(scenarios)} Use Indian Rupees (Rs.) for any money calculations."

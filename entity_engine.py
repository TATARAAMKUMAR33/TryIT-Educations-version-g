"""
entity_engine.py - Subject-aware Indian context generator
10,000+ unique combinations across 500+ names, cities, villages,
rivers, festivals, foods, occupations, historical figures, sports stars
Subject-specific story worlds — Physics != History != Maths
"""
import random

# ── 500+ NAMES (male + female, all regions) ────────────────────────────────
NAMES_MALE = [
    "Aarav","Vivaan","Aditya","Vihaan","Arjun","Sai","Reyansh","Ayaan","Krishna","Ishaan",
    "Rohan","Rahul","Amit","Ravi","Kiran","Sanjay","Karthik","Deepak","Manish","Harish",
    "Gopal","Suresh","Vijay","Ramesh","Vikram","Rajesh","Mahesh","Ganesh","Dinesh","Naresh",
    "Pradeep","Rakesh","Mukesh","Ritesh","Nilesh","Jitesh","Hitesh","Mitesh","Bhavesh","Umesh",
    "Ankit","Ankur","Akhil","Akash","Aakash","Varun","Tarun","Karun","Arun","Bhuvan",
    "Chirag","Dhruv","Eklavya","Farhan","Gaurav","Hemant","Ishan","Jayesh","Kapil","Lalit",
    "Manoj","Neeraj","Omkar","Pankaj","Quazi","Rajan","Sachin","Tarun","Uday","Vinay",
    "Wasim","Xavier","Yash","Zaid","Balaji","Chetan","Devraj","Eshan","Faisal","Girish",
    "Hardik","Imran","Jagdish","Kedar","Lokesh","Mukul","Nikhil","Omprakash","Pratik","Rajiv",
    "Saurabh","Tushar","Ujwal","Vishal","Waqar","Yogesh","Zaheer","Abhishek","Bharat","Chandra",
    "Divakar","Eknath","Fulchand","Gajanan","Hariom","Indrajit","Jaivardhan","Kanhaiya","Laxman","Madhav",
    "Narayan","Omkar","Prasad","Raghav","Shyam","Trilok","Udayan","Vamsi","Yadunath","Zubair",
    "Ajay","Bijay","Chandrakant","Durgesh","Eswaran","Furqan","Giriraj","Hansraj","Indresh","Janardhan",
    "Kalyan","Lakshmikant","Manohar","Nagesh","Onkar","Purushottam","Radheshyam","Satish","Trimbak","Umakant",
    "Venkatesh","Yadavrao","Anil","Bhaskar","Chandrasekhar","Dattatray","Eashwar","Ghanshyam","Harishchandra","Indrasen",
    # South Indian names
    "Arumugam","Balakrishnan","Chidambaram","Dhanasekaran","Ezhilarasan","Ganesan","Harikrishnan","Ilayaraja","Jayaraman","Kalaiyarasan",
    "Loganathan","Murugesan","Natarajan","Olagappan","Palaniswami","Rajagopal","Selvaraj","Thiagarajan","Ulaganathan","Veerappan",
    "Aravind","Bharath","Chandru","Deivanai","Easwaran","Gokul","Hariharan","Iyappan","Jeyaraj","Kumaran",
    # North East names
    "Bhupen","Chitravan","Deben","Hiranya","Jotin","Khagen","Liton","Mridul","Nagen","Pranjal",
    "Ranjit","Sanjib","Torun","Utpal","Biswajit","Dibyajyoti","Haren","Jatin","Kukil","Manoj",
    # Muslim names
    "Aamir","Babar","Danish","Faizan","Gulzar","Hamid","Ibrahim","Javed","Khalid","Luqman",
    "Mubarak","Nasir","Omar","Pervaiz","Rashid","Salman","Tariq","Usman","Waseem","Yasin",
    # Sikh names
    "Amarjit","Balwinder","Charanjit","Daljit","Gurpreet","Harpreet","Inderjit","Jaswant","Kulwant","Lakhwinder",
    "Manpreet","Navdeep","Onkar","Paramjit","Rajwinder","Sukhjit","Tejinder","Varinder","Waryam","Zaildar"
]

NAMES_FEMALE = [
    "Diya","Saanvi","Ananya","Aadhya","Pari","Anika","Navya","Avni","Myra","Sara",
    "Priya","Neha","Pooja","Meera","Sneha","Riya","Kavya","Nisha","Divya","Lakshmi",
    "Radha","Anjali","Kavita","Sunita","Geeta","Seeta","Nita","Rita","Lata","Usha",
    "Asha","Rekha","Sudha","Madhu","Indu","Bindu","Sindhu","Manju","Ranju","Sanju",
    "Padma","Nalini","Kamala","Saroja","Savita","Lalita","Malati","Sharada","Bharati","Vasanti",
    "Archana","Vandana","Kalpana","Ranjana","Sanjana","Bhavana","Suparna","Chetana","Rachana","Archana",
    "Deepika","Radhika","Monika","Sonika","Kritika","Preetika","Ankita","Nikita","Sunita","Mamita",
    "Smita","Amita","Sumita","Namita","Nirmala","Vimala","Kamala","Komala","Hemala","Premala",
    "Fatima","Ayesha","Zainab","Rukhsar","Nazia","Shabana","Tabassum","Salma","Reshma","Huma",
    "Gurpreet","Harpreet","Manpreet","Navpreet","Simranjit","Hardeep","Jaspreet","Kuldeep","Paramjit","Rajdeep",
    "Meenakshi","Rajeswari","Bhuvaneswari","Saraswathi","Lakshmipriya","Vijayalakshmi","Nithyashree","Kalaivani","Tamilselvi","Ponmalar",
    "Bidisha","Chandana","Dipali","Epsita","Gargi","Haimanti","Ishita","Jhuma","Kankana","Lopamudra",
    "Pallavi","Rupa","Sutapa","Tanushree","Uma","Vibha","Wriddhi","Yashodhara","Zinia","Anindita"
]

NAMES = NAMES_MALE + NAMES_FEMALE

# ── CITIES (Tier 1 + Tier 2 + Small towns) ────────────────────────────────
CITIES_METRO = ["Mumbai","Delhi","Bengaluru","Hyderabad","Chennai","Kolkata","Ahmedabad","Pune"]
CITIES_TIER2 = [
    "Jaipur","Lucknow","Kanpur","Nagpur","Indore","Bhopal","Visakhapatnam","Patna",
    "Vadodara","Ludhiana","Agra","Nashik","Faridabad","Meerut","Rajkot","Varanasi",
    "Srinagar","Amritsar","Ranchi","Coimbatore","Jabalpur","Gwalior","Vijayawada",
    "Jodhpur","Madurai","Raipur","Kota","Guwahati","Chandigarh","Mysuru","Tiruchirappalli",
    "Bareilly","Aligarh","Moradabad","Saharanpur","Gorakhpur","Bikaner","Amravati","Kolhapur",
    "Aurangabad","Solapur","Hubli","Belgaum","Mangaluru","Kozhikode","Thiruvananthapuram","Kochi",
    "Bhubaneswar","Cuttack","Rourkela","Brahmapur","Berhampur","Sambalpur","Siliguri","Asansol",
    "Durgapur","Bardhaman","Kharagpur","Howrah","Shillong","Imphal","Aizawl","Kohima","Itanagar","Gangtok"
]
CITIES_SMALL = [
    "Mathura","Vrindavan","Ayodhya","Haridwar","Rishikesh","Pushkar","Dwarka","Puri","Tirupati","Shirdi",
    "Bodh Gaya","Amaravati","Konark","Hampi","Ajmer","Udaipur","Jaisalmer","Alwar","Bharatpur","Chittorgarh",
    "Munger","Bhagalpur","Muzaffarpur","Chapra","Darbhanga","Sitamarhi","Araria","Kishanganj","Katihar","Saharsa",
    "Thanjavur","Vellore","Salem","Erode","Tirunelveli","Thoothukudi","Kanchipuram","Kumbakonam","Nagercoil","Dindigul",
    "Warangal","Karimnagar","Nizamabad","Khammam","Nalgonda","Adilabad","Mahbubnagar","Medak","Rangareddy","Nandyal",
    "Shimla","Dharamsala","Manali","Kullu","Mandi","Solan","Bilaspur","Hamirpur","Una","Kangra",
    "Dehradun","Haridwar","Nainital","Almora","Pithoragarh","Tehri","Chamoli","Rudraprayag","Uttarkashi","Bageshwar"
]
CITIES_VILLAGE = [
    "Rampur village","Krishnapur","Sundarpur","Anandnagar","Shantipuram","Gopalganj village",
    "Nandgaon","Vrindapur","Govindpur","Sitapur village","Dharmapur","Vedapur",
    "Saraswatinagar","Lakshmipur","Sarojininagar village","Ambedkarnagar","Phulepur","Tilaknagar village"
]
CITIES = CITIES_METRO + CITIES_TIER2 + CITIES_SMALL + CITIES_VILLAGE

# ── STATES ─────────────────────────────────────────────────────────────────
STATES = [
    "Uttar Pradesh","Maharashtra","Bihar","West Bengal","Madhya Pradesh","Tamil Nadu",
    "Rajasthan","Karnataka","Gujarat","Andhra Pradesh","Odisha","Telangana","Kerala",
    "Jharkhand","Assam","Punjab","Chhattisgarh","Haryana","Uttarakhand","Himachal Pradesh",
    "Tripura","Meghalaya","Manipur","Nagaland","Goa","Arunachal Pradesh","Mizoram","Sikkim"
]

# ── RIVERS, MOUNTAINS, LANDMARKS ───────────────────────────────────────────
RIVERS = ["Ganga","Yamuna","Godavari","Krishna","Cauvery","Brahmaputra","Narmada","Tapti","Mahanadi","Sabarmati","Chambal","Betwa","Son","Tungabhadra","Periyar"]
MOUNTAINS = ["Himalayas","Western Ghats","Eastern Ghats","Vindhyas","Aravalli","Nilgiris","Satpura","Karakoram","Shivalik","Sahyadri"]
LANDMARKS = ["Red Fort","Taj Mahal","Qutub Minar","India Gate","Gateway of India","Mysore Palace","Charminar","Meenakshi Temple","Victoria Memorial","Golden Temple","Lotus Temple","Konark Sun Temple"]

# ── FESTIVALS (expanded) ───────────────────────────────────────────────────
FESTIVALS = [
    "Diwali","Holi","Eid ul-Fitr","Eid ul-Adha","Christmas","Pongal","Onam","Bihu","Navratri",
    "Durga Puja","Ganesh Chaturthi","Makar Sankranti","Vaisakhi","Lohri","Raksha Bandhan",
    "Janmashtami","Maha Shivaratri","Ugadi","Chhath Puja","Baisakhi","Teej","Karva Chauth",
    "Dussehra","Ram Navami","Hanuman Jayanti","Buddha Purnima","Guru Nanak Jayanti","Mahavir Jayanti",
    "Basant Panchami","Nag Panchami","Govardhan Puja","Bhai Dooj","Dhanteras","Karvachauth",
    "Eid Milad-un-Nabi","Muharram","Shab-e-Barat","Nowruz","Losoong","Hornbill Festival",
    "Pushkar Fair","Kumbh Mela","Thrissur Pooram","Hemis Festival","Chapchar Kut","Wangala Festival"
]

# ── FOODS (by region) ──────────────────────────────────────────────────────
FOODS_NORTH = ["paratha","chole bhature","rajma chawal","kadhi pakora","dal makhani","aloo tikki","golgappa","lassi","kulfi","jalebi"]
FOODS_SOUTH = ["idli","dosa","vada","sambhar","rasam","pongal","appam","puttu","pesarattu","uttapam","curd rice","tamarind rice"]
FOODS_EAST = ["rasgulla","mishti doi","sandesh","chingri malai","luchi","kosha mangsho","pitha","masor tenga","bamboo shoot curry","thukpa"]
FOODS_WEST = ["vada pav","pav bhaji","dhokla","thepla","khandvi","modak","poha","sabudana khichdi","puran poli","shrikhand"]
FOODS_ALL = FOODS_NORTH + FOODS_SOUTH + FOODS_EAST + FOODS_WEST + ["biryani","samosa","pakora","kheer","halwa","momos","tandoori roti","butter chicken","paneer tikka","dal tadka"]

# ── SPORTS STARS (Indian) ──────────────────────────────────────────────────
CRICKET_STARS = ["Sachin Tendulkar","MS Dhoni","Virat Kohli","Rohit Sharma","Jasprit Bumrah","Ravindra Jadeja","R Ashwin","Sunil Gavaskar","Kapil Dev","Anil Kumble"]
OTHER_SPORTS = ["PV Sindhu","Saina Nehwal","Mary Kom","Neeraj Chopra","Abhinav Bindra","Leander Paes","Sushil Kumar","Mirabai Chanu","Bajrang Punia","Dipa Karmakar"]
SPORTS_STARS = CRICKET_STARS + OTHER_SPORTS

# ── HISTORICAL FIGURES ─────────────────────────────────────────────────────
FREEDOM_FIGHTERS = ["Mahatma Gandhi","Bhagat Singh","Subhas Chandra Bose","Jawaharlal Nehru","Sardar Patel","B.R. Ambedkar","Rani Lakshmibai","Bal Gangadhar Tilak","Gopal Krishna Gokhale","Lala Lajpat Rai"]
SCIENTISTS = ["C.V. Raman","Homi Bhabha","Vikram Sarabhai","APJ Abdul Kalam","Satyendra Nath Bose","Meghnad Saha","S. Ramanujan","Jagadish Chandra Bose","Har Gobind Khorana","Yellapragada SubbaRow"]

# ── OCCUPATIONS (expanded) ─────────────────────────────────────────────────
OCCUPATIONS_RURAL = ["farmer","weaver","potter","carpenter","blacksmith","fisherman","dairy farmer","sugarcane grower","rice farmer","cotton picker"]
OCCUPATIONS_URBAN = ["teacher","engineer","doctor","shopkeeper","banker","police officer","nurse","chef","journalist","lawyer","accountant","software developer","architect","electrician","plumber"]
OCCUPATIONS_STUDENT = ["Class 10 student","Class 12 student","engineering student","medical student","UPSC aspirant","SSC aspirant","IIT-JEE student","NEET aspirant","MBA student","research scholar"]
OCCUPATIONS = OCCUPATIONS_RURAL + OCCUPATIONS_URBAN + OCCUPATIONS_STUDENT

# ── SUBJECT-SPECIFIC STORY TEMPLATES ──────────────────────────────────────
SUBJECT_STORY_WORLDS = {
    "maths_arithmetic": {
        "characters": ["shopkeeper","merchant","vegetable vendor","auto-rickshaw driver","daily wage worker","money lender"],
        "settings": ["weekly bazaar","railway ticket counter","ration shop","mandi","local market","fair"],
        "scenarios": [
            "buying and selling with profit/loss",
            "calculating change and discount",
            "dividing land equally among children",
            "splitting restaurant bill",
            "calculating train fare for family"
        ]
    },
    "maths_algebra": {
        "characters": ["student","tuition teacher","engineer","carpenter","tailor"],
        "settings": ["classroom","construction site","tailor shop","factory","home"],
        "scenarios": [
            "finding unknown quantity in a recipe",
            "calculating unknown dimensions of a room",
            "solving age problems in a family",
            "finding number of items from total cost"
        ]
    },
    "maths_geometry": {
        "characters": ["architect","farmer","painter","tile layer","gardener"],
        "settings": ["construction site","agricultural field","house","temple","park"],
        "scenarios": [
            "calculating area of a field to plant crops",
            "finding how much paint to cover a wall",
            "designing a circular park",
            "tiling a floor with square tiles"
        ]
    },
    "maths_trigonometry": {
        "characters": ["surveyor","sailor","pilot","mountain climber","soldier"],
        "settings": ["hilltop","sea","mountain","construction site","battlefield"],
        "scenarios": [
            "measuring height of a building using shadow",
            "finding distance to a ship from shore",
            "calculating angle of a ramp",
            "finding height of a tree without climbing"
        ]
    },
    "maths_calculus": {
        "characters": ["engineer","physicist","economist","biologist","chemist"],
        "settings": ["factory","laboratory","hospital","research center","space station"],
        "scenarios": [
            "finding rate of change of temperature",
            "calculating maximum profit for a factory",
            "finding minimum cost of materials",
            "tracking speed of a falling object"
        ]
    },
    "maths_stats": {
        "characters": ["census worker","market researcher","doctor","teacher","cricket analyst"],
        "settings": ["village census","hospital","school","cricket stadium","election office"],
        "scenarios": [
            "calculating average marks of students",
            "finding median income of a village",
            "analyzing cricket batting average",
            "finding most common disease in a district"
        ]
    },
    "physics": {
        "characters": ["cricket player","cyclist","kite flyer","auto mechanic","construction worker"],
        "settings": ["cricket ground","road","open field","garage","building site"],
        "scenarios": [
            "Dhoni hitting a six — projectile motion",
            "cyclist on a curved road — centripetal force",
            "kite string angle — tension and force",
            "auto engine starting — Newton's laws",
            "lifting bricks to terrace — work and energy"
        ]
    },
    "science_gen": {
        "characters": ["farmer","kitchen cook","village nurse","school biology teacher","gardener"],
        "settings": ["farm","kitchen","village health center","school lab","garden"],
        "scenarios": [
            "crops wilting — photosynthesis",
            "milk turning sour — bacteria and fermentation",
            "salt dissolving in water — chemistry",
            "wounds healing — biology",
            "plants growing toward light — tropism"
        ]
    },
    "gk_india": {
        "characters": FREEDOM_FIGHTERS + ["school teacher explaining history","student at India Gate","tourist guide at Red Fort"],
        "settings": ["India Gate","Rajpath","Parliament","historical museum","school classroom"],
        "scenarios": [
            "visiting a monument and learning its history",
            "school quiz about Indian constitution",
            "election day in a village",
            "Panchayat meeting discussing local issues",
            "freedom fighter biography discussion in class"
        ]
    },
    "gk_polity": {
        "characters": ["Panchayat head (Sarpanch)","MLA","district collector","voter","law student"],
        "settings": ["Gram Sabha","Vidhan Sabha","village panchayat","court","election booth"],
        "scenarios": [
            "village panchayat election process",
            "Sarpanch explaining Fundamental Rights",
            "voter learning about electoral process",
            "law student studying Constitution",
            "RTI application in district office"
        ]
    },
    "gk_sports": {
        "characters": SPORTS_STARS + ["young cricket player","kabaddi team captain","school sports teacher"],
        "settings": ["cricket stadium","Olympic Games","school sports day","national championship","village kabaddi ground"],
        "scenarios": [
            "Neeraj Chopra winning gold — javelin physics",
            "kabaddi match strategy — teamwork",
            "IPL statistics — maths in cricket",
            "marathon runner — stamina and nutrition",
            "chess tournament — strategy and rules"
        ]
    },
    "competitive_govt_exams": {
        "characters": ["UPSC aspirant","SSC candidate","railway job applicant","bank PO student","state PSC student"],
        "settings": ["coaching centre","study room","examination hall","library","hostel room"],
        "scenarios": [
            "UPSC aspirant solving previous year paper",
            "SSC candidate practicing speed maths",
            "railway applicant studying current affairs",
            "bank PO student doing reasoning puzzles",
            "state PSC aspirant reading polity"
        ]
    },
    "engineering_sub": {
        "characters": ["civil engineer","electrical engineer","mechanical engineer","construction supervisor","factory foreman"],
        "settings": ["construction site","electrical substation","factory floor","bridge","dam"],
        "scenarios": [
            "engineer calculating load on a bridge",
            "electrician wiring a new building",
            "factory optimizing production speed",
            "dam engineer calculating water pressure",
            "road builder calculating material needed"
        ]
    },
    "english_vocab": {
        "characters": ["school English teacher","newspaper editor","debate competition student","call centre worker","author"],
        "settings": ["English medium school","newspaper office","debate hall","office","book fair"],
        "scenarios": [
            "student learning new words from newspaper",
            "teacher explaining word roots in class",
            "debate competitor choosing precise words",
            "author finding right word for novel",
            "interview preparation — vocabulary"
        ]
    },
    "english_writing": {
        "characters": ["journalist","letter writer","government officer","student","blogger"],
        "settings": ["newsroom","post office","government office","school","internet cafe"],
        "scenarios": [
            "journalist writing report about flood",
            "village elder writing application to collector",
            "student writing essay for competition",
            "government notice writing exercise",
            "blogger writing about Indian culture"
        ]
    },
    "nep_school_foundation": {
        "characters": ["Class 3 student","school teacher","anganwadi worker","parent","school principal"],
        "settings": ["village school","anganwadi center","home","playground","school garden"],
        "scenarios": [
            "young child learning numbers with mangoes",
            "teacher using pebbles to teach counting",
            "child asking parent why sky is blue",
            "school garden activity — plant growth",
            "story time — moral values"
        ]
    },
    "ug_pg_entrances": {
        "characters": ["JEE aspirant","NEET student","CLAT candidate","CAT aspirant","engineering student"],
        "settings": ["coaching institute","college campus","study group","mock test center","college canteen"],
        "scenarios": [
            "JEE student solving integration problem",
            "NEET aspirant learning cell biology",
            "CAT student solving data interpretation",
            "GATE student doing digital circuits",
            "group study session before entrance exam"
        ]
    },
    "healthcare_legal_compliance": {
        "characters": ["village doctor","ASHA worker","nurse","patient","advocate","judge"],
        "settings": ["PHC (Primary Health Centre)","village","district hospital","court","legal aid office"],
        "scenarios": [
            "ASHA worker explaining vaccination to mother",
            "doctor diagnosing common disease in village",
            "patient understanding medicine dosage",
            "lawyer explaining legal rights to client",
            "court case about land dispute"
        ]
    },
    "management_sub": {
        "characters": ["startup founder","small business owner","bank manager","HR manager","marketing head"],
        "settings": ["startup office","shop","bank branch","corporate office","market"],
        "scenarios": [
            "shopkeeper managing inventory",
            "startup founder calculating burn rate",
            "HR manager conducting interview",
            "marketing team planning campaign",
            "bank manager evaluating loan application"
        ]
    },
    "future_tech_corporate": {
        "characters": ["young programmer","AI researcher","data scientist","startup founder","tech entrepreneur"],
        "settings": ["tech startup","IIT lab","innovation hub","hackathon","incubation center"],
        "scenarios": [
            "young coder building first app",
            "AI student training a model",
            "data scientist analyzing census data",
            "startup pitch at IIT incubator",
            "hackathon team building social solution"
        ]
    }
}

DEFAULT_STORY_WORLD = {
    "characters": OCCUPATIONS,
    "settings": CITIES_TIER2,
    "scenarios": ["daily life situation that mirrors the concept"]
}

def get_subject_world(subject_id):
    """Get the right story world for a subject."""
    for key in SUBJECT_STORY_WORLDS:
        if key in (subject_id or ""):
            return SUBJECT_STORY_WORLDS[key]
    return DEFAULT_STORY_WORLD

def get_context(topic_id="", subject_id=""):
    """
    Returns a rich Indian context string tuned to the subject.
    Called from generate_master.py before building prompt.
    """
    world = get_subject_world(subject_id or topic_id or "")

    name      = random.choice(NAMES)
    city      = random.choice(CITIES)
    state     = random.choice(STATES)
    festival  = random.choice(FESTIVALS)
    food      = random.choice(FOODS_ALL)
    river     = random.choice(RIVERS)
    character = random.choice(world["characters"]) if world["characters"] else random.choice(OCCUPATIONS)
    setting   = random.choice(world["settings"]) if world["settings"] else city
    scenario  = random.choice(world["scenarios"]) if world["scenarios"] else "daily life"

    context = f"""STORY CONTEXT FOR THIS QUESTION:
Character: {name}, a {character} from {city}, {state}
Setting: {setting}
Situation: {scenario}
Cultural touch: {festival} season, favourite food {food}, near river {river}

CRITICAL INSTRUCTION FOR story_explanation:
- Use {name} as your main character
- Place the story in {city} or nearby {setting}
- The story MUST demonstrate the EXACT concept being tested
- {name} must face the SAME problem as the question and solve it using the SAME logic as the correct answer
- End with: "This is exactly why [correct option] is the answer"
- Make it feel like a real Indian daily life moment, not a textbook example
- Use Indian Rupees (₹) for money, Indian units where applicable"""

    return context

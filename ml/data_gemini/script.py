import json
import random

# --- Configuration & Data Assets ---

categories = {
    "product_launch": 12,
    "daily_moment": 14,
    "promotion": 10,
    "engagement": 8,
    "brand_story": 6
}

products = [
    "Iced Latte", "Coconut Cold Brew", "Caramel Macchiato", "Dirty Coffee", 
    "Uji Matcha Latte", "Passion Frappe", "Americano", "Honey Lemon Ginger", 
    "Butterfly Pea Latte", "Pandan Latte", "Cappuccino", "Avocado Coffee"
]

locations = ["BKK1", "Toul Tom Poung", "Russian Market", "Riverside", "Santhormok", "Siem Reap"]

# --- Helper functions for varied generation ---

def generate_entry(idx, category):
    prod = random.choice(products)
    loc = random.choice(locations)
    
    entry = {
        "id": idx,
        "category": category,
        "metadata": {
            "product": prod,
            "promotion": None,
            "mood": "",
            "occasion": "",
            "target_audience": "young professionals, students"
        },
        "caption": {"en": "", "km": ""},
        "hashtags": {"en": [], "km": []}
    }

    if category == "product_launch":
        entry["metadata"]["promotion"] = "new menu item"
        entry["metadata"]["mood"] = "exciting, fresh"
        entry["metadata"]["occasion"] = "seasonal launch"
        entry["caption"]["en"] = f"Something new is brewing! ☕️✨\n\nMeet our {prod}—crafted for the perfect balance of flavor and freshness. Now available at all branches!\n\nCome try it today! 👇"
        entry["caption"]["km"] = f"អ្វីដែលថ្មីបានមកដល់ហើយ! ☕️✨\n\nសូមណែនាំ {prod}—ដែលចម្រាញ់ចេញពីតុល្យភាពនៃរសជាតិ និងភាពស្រស់ស្រាយ។ មានលក់នៅគ្រប់សាខាទាំងអស់!\n\nមកសាកល្បងថ្ងៃនេះទាំងអស់គ្នា! 👇"
        entry["hashtags"]["en"] = ["#NewMenu", f"#{prod.replace(' ', '')}", "#CoffeePP"]
        entry["hashtags"]["km"] = ["#ម៉ឺនុយថ្មី", "#ហាងកាហ្វេ", "#ភេសជ្ជៈថ្មី"]

    elif category == "daily_moment":
        entry["metadata"]["mood"] = "energizing, productive"
        entry["metadata"]["occasion"] = "morning fuel"
        entry["caption"]["en"] = f"The only way to start your morning right. ☀️\n\nA cup of {prod} and you're ready to take on the day. See you at our {loc} branch!\n\nTag a coffee lover! ❤️"
        entry["caption"]["km"] = f"វិធីតែមួយគត់ដើម្បីចាប់ផ្តើមព្រឹកព្រលឹមដ៏ល្អ។ ☀️\n\nមួយកែវនៃ {prod} នឹងជួយឱ្យអ្នកត្រៀមខ្លួនសម្រាប់ថ្ងៃថ្មី។ ជួបគ្នានៅសាខា {loc}!\n\nTag អ្នកចូលចិត្តកាហ្វេមក! ❤️"
        entry["hashtags"]["en"] = ["#MorningCoffee", "#DailyFuel", "#CafeVibes"]
        entry["hashtags"]["km"] = ["#កាហ្វេពេលព្រឹក", "#កម្លាំងចិត្ត", "#PhnomPenh"]

    elif category == "promotion":
        entry["metadata"]["promotion"] = "Buy 1 Get 1 Free"
        entry["metadata"]["mood"] = "urgent, exciting"
        entry["metadata"]["occasion"] = "Happy Hour"
        entry["caption"]["en"] = f"HAPPY HOUR ALERT! 📢✨\n\nBuy 1 Get 1 FREE on our {prod} from 2 PM - 5 PM today only! Don't miss this deal at {loc}.\n\nGrab a friend and come over! 🏃‍♂️💨"
        entry["caption"]["km"] = f"HAPPY HOUR មកដល់ហើយ! 📢✨\n\nទិញ ១ ថែម ១ ឥតគិតថ្លៃ សម្រាប់ {prod} ចាប់ពីម៉ោង ២ រសៀល ដល់ ៥ ល្ងាច ថ្ងៃនេះតែប៉ុណ្ណោះ! កុំឱ្យរំលងឱកាសនេះនៅសាខា {loc}។\n\nបបួលមិត្តភក្តិមកឥឡូវនេះ! 🏃‍♂️💨"
        entry["hashtags"]["en"] = ["#BOGO", "#SpecialOffer", "#HappyHour"]
        entry["hashtags"]["km"] = ["#ប្រូម៉ូសិន", "#ទិញ១ថែម១", "#កាហ្វេ"]

    elif category == "engagement":
        entry["metadata"]["mood"] = "playful, community"
        entry["metadata"]["occasion"] = "weekend poll"
        entry["caption"]["en"] = f"What’s your go-to vibe today? 🤔☕️\n\nAre you Team {prod} or Team Americano? Let us know your favorite in the comments below! 👇✨"
        entry["caption"]["km"] = f"តើអារម្មណ៍អ្នកថ្ងៃនេះចង់ញ៉ាំអ្វីជាងគេ? 🤔☕️\n\nតើអ្នកជា Team {prod} ឬ Team Americano? ប្រាប់យើងពីចំណូលចិត្តរបស់អ្នកនៅក្នុង comment ខាងក្រោមមក! 👇✨"
        entry["hashtags"]["en"] = ["#CoffeeDebate", "#WhichOne", "#Community"]
        entry["hashtags"]["km"] = ["#ជម្រើសអ្នក", "#ចូលចិត្តមួយណា", "#ហាងកាហ្វេ"]

    elif category == "brand_story":
        entry["metadata"]["mood"] = "authentic, inspiring"
        entry["metadata"]["occasion"] = "brand heritage"
        entry["caption"]["en"] = "Beyond the cup. 🇰🇭❤️\n\nWe source our beans directly from farmers in Mondulkiri to bring you the authentic taste of Cambodia. Quality you can trust.\n\nSupport local. Drink local. ✨"
        entry["caption"]["km"] = "លើសពីកាហ្វេមួយកែវ។ 🇰🇭❤️\n\nយើងប្រើប្រាស់គ្រាប់កាហ្វេដោយផ្ទាល់ពីកសិករនៅមណ្ឌលគិរី ដើម្បីនាំមកជូនអ្នកនូវរសជាតិពិតនៃកម្ពុជា។ គុណភាពដែលអ្នកអាចទុកចិត្តបាន។\n\nគាំទ្រផលិតផលក្នុងស្រុក។ ✨"
        entry["hashtags"]["en"] = ["#BrandStory", "#SupportLocal", "#MondulkiriCoffee"]
        entry["hashtags"]["km"] = ["#រឿងរ៉ាវយើង", "#ផលិតផលខ្មែរ", "#មណ្ឌលគិរី"]

    return entry

# --- Generation Loop ---

all_entries = []
current_id = 1

for cat, count in categories.items():
    for _ in range(count):
        all_entries.append(generate_entry(current_id, cat))
        current_id += 1

random.shuffle(all_entries)

final_data = {
    "dataset_info": {
        "total_captions": 50,
        "language_pair": "en-km",
        "created_for": "POSTNOW mBART fine-tuning",
        "categories": categories
    },
    "captions": all_entries
}

with open("postnow_training_data_50.json", "w", encoding="utf-8") as f:
    json.dump(final_data, f, ensure_ascii=False, indent=2)
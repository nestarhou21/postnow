"""
ml/data_gemini/generate_2500_offline.py
────────────────────────────────────────
Generates 2,500 bilingual (EN + KH) coffee-shop marketing captions
for POSTNOW mBART fine-tuning — NO API KEY REQUIRED.

Uses large pools of hand-crafted English + Khmer templates combined
with randomised product/occasion/location/promotion variables.

Distribution:
  product_launch : 600  (24%)
  daily_moment   : 700  (28%)
  promotion      : 500  (20%)
  engagement     : 400  (16%)
  brand_story    : 300  (12%)

Usage:
  python generate_2500_offline.py
  → saves postnow_training_data_2500.json
"""

import json
import random
from pathlib import Path

OUTPUT_FILE = Path(__file__).parent / "postnow_training_data_2500.json"

TARGET = {
    "product_launch": 600,
    "daily_moment":   700,
    "promotion":      500,
    "engagement":     400,
    "brand_story":    300,
}

# ──────────────────────────────────────────────────────────────────────────────
# Variable pools
# ──────────────────────────────────────────────────────────────────────────────

PRODUCTS = [
    "Iced Latte", "Coconut Cold Brew", "Caramel Macchiato", "Dirty Coffee",
    "Uji Matcha Latte", "Passion Fruit Frappe", "Americano", "Iced Americano",
    "Butterfly Pea Latte", "Pandan Latte", "Cappuccino", "Avocado Coffee",
    "Cold Brew", "Nitro Cold Brew", "Vietnamese Coffee", "Flat White",
    "Rose Latte", "Honey Lavender Latte", "Brown Sugar Latte", "Taro Latte",
    "Mango Frappe", "Chocolate Frappe", "Mocha", "Vanilla Latte",
    "Hazelnut Latte", "Caramel Latte", "Cortado", "Affogato",
    "Pumpkin Spice Latte", "Peppermint Mocha", "Thai Tea Latte",
    "Salted Caramel Cold Brew", "Strawberry Frappe", "Dalgona Coffee",
    "Kampot Pepper Cold Brew", "Single-Origin Espresso", "Macchiato",
    "Matcha Frappe", "Lychee Cold Brew", "Mango Cold Brew",
    "Khmer New Year Special Latte", "Water Festival Cold Brew",
    "Condensed Milk Iced Coffee", "Hot Chocolate", "Chai Latte",
    "Banana Bread", "Avocado Toast", "Croissant", "Cheese Cake",
]

LOCATIONS = [
    "BKK1", "Toul Tom Poung", "Russian Market", "Riverside",
    "Santhormok", "Daun Penh", "Sen Sok", "Toul Kork",
    "Siem Reap", "all branches", "our shop",
]

TIMES = [
    "today only", "this weekend", "this week only", "for a limited time",
    "while stocks last", "this month only", "starting today",
]

DISCOUNTS = [
    "20% off", "25% off", "30% off", "15% off", "50% off",
    "Buy 1 Get 1 Free", "2-for-1", "half price",
]

HOURS = [
    "2 PM – 5 PM", "3 PM – 6 PM", "11 AM – 1 PM",
    "8 AM – 10 AM", "4 PM – 7 PM",
]

AUDIENCES = [
    "young professionals, 18-35", "students, 18-25",
    "coffee enthusiasts", "remote workers", "families",
    "expats and tourists", "locals, all ages", "working adults, 25-40",
]

CULTURAL_OCCASIONS = [
    "Khmer New Year", "Water Festival", "Pchum Ben",
    "King's Birthday", "Cambodian Independence Day", "Chinese New Year",
]

BEAN_ORIGINS = [
    "Mondulkiri", "Ratanakiri", "Kampot", "Takeo",
    "Kep Province", "Preah Vihear",
]

BREWING_METHODS = [
    "pour-over", "cold drip", "French press", "AeroPress",
    "espresso machine", "siphon brew",
]

# ──────────────────────────────────────────────────────────────────────────────
# Hashtag pools per category
# ──────────────────────────────────────────────────────────────────────────────

EN_TAGS = {
    "product_launch": [
        ["#NewMenu", "#MustTry", "#CoffeePhnomPenh"],
        ["#NewDrink", "#LimitedEdition", "#CoffeeTime"],
        ["#SeasonalSpecial", "#TryItNow", "#CafeVibes"],
        ["#FreshDrop", "#NewArrival", "#CoffeeLovers"],
        ["#NewRelease", "#SpecialEdition", "#PhnomPenhCafe"],
        ["#LaunchDay", "#NewFlavor", "#CoffeeKH"],
        ["#Innovation", "#NewMenu", "#BaristaCraft"],
        ["#TasteSomethingNew", "#MenuUpdate", "#KhmerCoffee"],
    ],
    "daily_moment": [
        ["#MorningCoffee", "#DailyFuel", "#CafeVibes"],
        ["#CoffeeTime", "#WorkFromCafe", "#PhnomPenh"],
        ["#AfternoonPick", "#CoffeeBreak", "#StudyFuel"],
        ["#MondayMotivation", "#CoffeeFirst", "#GoodMorning"],
        ["#WeekendVibes", "#CoffeeLover", "#SlowMorning"],
        ["#RainyDayCoffee", "#CozyVibes", "#CafeLife"],
        ["#StudySession", "#CoffeeAndWork", "#ProductiveCafe"],
        ["#FridayFeeling", "#TreatYourself", "#CoffeeHour"],
    ],
    "promotion": [
        ["#BOGO", "#SpecialOffer", "#HappyHour"],
        ["#FlashSale", "#LimitedTime", "#CoffeeDeals"],
        ["#StudentDiscount", "#SaveMore", "#CampusCoffee"],
        ["#BirthdayPromo", "#FreeCoffee", "#CelebrateCoffee"],
        ["#HappyHour", "#DrinkDeals", "#CafePromo"],
        ["#LoyaltyReward", "#MemberOffer", "#CoffeeRewards"],
        ["#WeekendDeal", "#SaveBig", "#CoffeePromo"],
        ["#EarlyBird", "#MorningDeal", "#CoffeeDiscount"],
    ],
    "engagement": [
        ["#CoffeeDebate", "#WhichOne", "#Community"],
        ["#CoffeePoll", "#TagAFriend", "#CoffeeLovers"],
        ["#ThisOrThat", "#CoffeeChoice", "#CafeVibes"],
        ["#TagYourCoffeeBuddy", "#CoffeeSquad", "#PhnomPenh"],
        ["#CoffeeFavorite", "#VoteNow", "#CommunityLove"],
        ["#GiveawayAlert", "#WinCoffee", "#CafeFamily"],
        ["#CoffeeQuestion", "#ShareYourCup", "#InstaBreak"],
        ["#CaptionContest", "#CafeChallenge", "#TagUs"],
    ],
    "brand_story": [
        ["#BrandStory", "#SupportLocal", "#MondulkiriCoffee"],
        ["#FarmToCup", "#EthicalCoffee", "#KhmerCoffee"],
        ["#CoffeeHeritage", "#LocalBeans", "#CambodianCoffee"],
        ["#Sustainability", "#GreenCoffee", "#EcoFriendly"],
        ["#LocalFarmers", "#CommunityFirst", "#KhmerRoast"],
        ["#BrewingStory", "#CraftCoffee", "#PhnomPenhCafe"],
        ["#OriginStory", "#SingleOrigin", "#TasteOfCambodia"],
        ["#WomenFarmers", "#EmpowerLocal", "#CoffeeCause"],
    ],
}

KM_TAGS = {
    "product_launch": [
        ["#ម៉ឺនុយថ្មី", "#ភេសជ្ជៈថ្មី", "#កាហ្វេភ្នំពេញ"],
        ["#ថ្មីបំផុត", "#ត្រូវតែសាក", "#ហាងកាហ្វេ"],
        ["#មានតែម្ដង", "#ភេសជ្ជៈពិសេស", "#CafePP"],
        ["#ណែនាំថ្មី", "#រសជាតិថ្មី", "#កាហ្វេខ្មែរ"],
        ["#ធ្វើអ្វីថ្មី", "#ម៉ឺនុយពិសេស", "#PhnomPenh"],
    ],
    "daily_moment": [
        ["#កាហ្វេពេលព្រឹក", "#កម្លាំងចិត្ត", "#ភ្នំពេញ"],
        ["#ពេលព្រឹក", "#WorkFromCafe", "#កាហ្វេ"],
        ["#សម្រាកពេលរសៀល", "#ផ្តល់កម្លាំង", "#ហាងកាហ្វេ"],
        ["#ថ្ងៃចន្ទ", "#ចាប់ផ្តើមថ្ងៃ", "#GoodMorning"],
        ["#ចុងសប្ដាហ៍", "#អារម្មណ៍ល្អ", "#CozyVibes"],
        ["#ថ្ងៃភ្លៀង", "#កំដៅចិត្ត", "#CafeLife"],
    ],
    "promotion": [
        ["#ប្រូម៉ូសិន", "#ទិញ១ថែម១", "#ឱកាសសម្រាប់អ្នក"],
        ["#ថោក", "#សន្សំប្រាក់", "#ហ្វ្លែសស",],
        ["#បញ្ចុះតម្លៃ", "#ណាស់ដែរ", "#PhnomPenh"],
        ["#ថ្ងៃខួបកំណើត", "#កាហ្វេឥតគិតថ្លៃ", "#ពិធីខួប"],
        ["#HappyHour", "#ពេលវេលាពិសេស", "#ប្រូម៉ូ"],
        ["#រង្វាន់", "#ចំណុចទំនុកចិត្ត", "#CafePP"],
    ],
    "engagement": [
        ["#ជម្រើសអ្នក", "#ចូលចិត្តមួយណា", "#ហាងកាហ្វេ"],
        ["#TagMong", "#មិត្តភ័ក្ត", "#ចូលរួម"],
        ["#Vote", "#ប្រាប់យើង", "#CommunityKH"],
        ["#ឈ្នះរង្វាន់", "#Giveaway", "#PhnomPenh"],
        ["#សំណួរ", "#Share", "#CafeFamily"],
        ["#ចំណូលចិត្ត", "#ប្រាប់ Comment", "#CafeCommunity"],
    ],
    "brand_story": [
        ["#រឿងរ៉ាវយើង", "#ផលិតផលខ្មែរ", "#មណ្ឌលគិរី"],
        ["#កសិករ", "#ជីវិតក្នុងស្រុក", "#KhmerCoffee"],
        ["#កាហ្វេខ្មែរ", "#ប្រភពខ្មែរ", "#SupportLocal"],
        ["#បរិស្ថាន", "#កាហ្វេបៃតង", "#EcoKH"],
        ["#ប្រវត្តិ", "#ដំណើរ", "#CambodiaBrew"],
        ["#ស្ត្រីកសិករ", "#ពង្រឹង", "#LocalFirst"],
    ],
}

# ──────────────────────────────────────────────────────────────────────────────
# Template pools — (en_template, km_template) pairs
# Each {VAR} is replaced at generation time
# ──────────────────────────────────────────────────────────────────────────────

TEMPLATES = {

# ─── PRODUCT LAUNCH (600) ────────────────────────────────────────────────────
"product_launch": [
    (
        "Something new is brewing! ☕✨\n\nIntroducing our {PRODUCT} — crafted for the perfect balance of flavor and freshness. Available now at all branches!\n\nCome try it today! 👇",
        "មានអ្វីថ្មីបានមកដល់ហើយ! ☕✨\n\nសូមណែនាំ {PRODUCT} — ផលិតដើម្បីតុល្យភាពនៃរសជាតិ និងភាពស្រស់ស្រាយ។ មានលក់នៅគ្រប់សាខា!\n\nមកសាកល្បងថ្ងៃនេះ! 👇"
    ),
    (
        "Meet your new favorite drink! 🎉\n\nOur {PRODUCT} is here — smooth, refreshing, and made with love for coffee fans in Phnom Penh.\n\nOrder yours now! ☕",
        "ជួបភេសជ្ជៈចូលចិត្តថ្មីរបស់អ្នក! 🎉\n\n{PRODUCT} របស់យើងមកដល់ហើយ — ទន់ ស្រស់ ហើយធ្វើចេញពីចិត្តសម្រាប់អ្នកចូលចិត្តកាហ្វេ!\n\nកម្មង់ឥឡូវនេះ! ☕"
    ),
    (
        "NEW MENU ALERT! 📢☕\n\nSay hello to {PRODUCT} — our latest creation inspired by the tropical flavors of Cambodia. Limited time only!\n\nTag a friend who needs to try this! 👇",
        "ម៉ឺនុយថ្មីបានមកដល់! 📢☕\n\nស្វាគមន៍ {PRODUCT} — ការបង្កើតថ្មីៗ ដែលទទួលការចំណូលចិត្តពីរសជាតិត្រូពិចនៃកម្ពុជា។ មានរយៈពេលកំណត់!\n\nTag មិត្តដែលត្រូវតែសាកល្បង! 👇"
    ),
    (
        "We've been working on something special for you. ✨\n\nIntroducing {PRODUCT} — a new addition to our menu that you'll fall in love with on the first sip.\n\nAvailable at {LOCATION} starting today!",
        "យើងកំពុងរៀបចំអ្វីពិសេសសម្រាប់អ្នក។ ✨\n\nណែនាំ {PRODUCT} — ភេសជ្ជៈថ្មីដែលអ្នកនឹងស្រឡាញ់ចាប់ពីការពិសាដំបូង!\n\nមានចាប់ពីថ្ងៃនេះនៅ {LOCATION}!"
    ),
    (
        "Your taste buds called — they want {PRODUCT}. 🌟☕\n\nFresh on our menu! Smooth, bold, and everything you didn't know you needed.\n\nTry it at {LOCATION} today!",
        "ជាតិអ្នកបានហៅ — ពួកគេចង់បាន {PRODUCT}! 🌟☕\n\nថ្មីៗ​នៅក្នុងម៉ឺនុយ! ទន់ ហ័ររ ហើយគ្រប់យ៉ាងដែលអ្នកត្រូវការ!\n\nសាកល្បងនៅ {LOCATION} ថ្ងៃនេះ!"
    ),
    (
        "Drop everything — our {PRODUCT} just launched! 🥳✨\n\nInspired by Cambodia's love for bold, refreshing drinks, this one is made for the real ones.\n\nGet yours before it sells out! ☕",
        "ឈប់ everything — {PRODUCT} របស់យើងទើបបើកដំណើរ! 🥳✨\n\nទទួលការជំរុញចិត្តពីភាពស្រឡាញ់ភេសជ្ជៈ Bold របស់កម្ពុជា ផលិតដើម្បីអ្នក!\n\nយកមកមុននឹងអស់! ☕"
    ),
    (
        "This season, we're bringing something tropical to your cup. 🌴☕\n\nOur {PRODUCT} is inspired by the warmth of Cambodia — sweet, smooth, and absolutely unforgettable.\n\nAvailable now at all locations!",
        "រដូវនេះ យើងបញ្ចូលអ្វីត្រូពិចមកក្នុងកែវរបស់អ្នក។ 🌴☕\n\n{PRODUCT} របស់យើងបង្ហាញពីភាពកំដៅនៃកម្ពុជា — ផ្អែម ទន់ ហើយមិនអាចភ្លេចបាន!\n\nមានឥឡូវនេះនៅគ្រប់សាខា!"
    ),
    (
        "Exciting news for coffee lovers! ☕🎊\n\nWe're thrilled to introduce {PRODUCT} — now available for a limited time. Made fresh, served with love.\n\nCome visit us at {LOCATION}!",
        "ព័ត៌មានរំភើបសម្រាប់អ្នកស្រឡាញ់កាហ្វេ! ☕🎊\n\nយើងរីករាយណែនាំ {PRODUCT} — មានរយៈពេលកំណត់។ ផ្ទុកស្រស់ ប្រគល់ជូនដោយចិត្ត!\n\nមកទស្សនាយើងនៅ {LOCATION}!"
    ),
    (
        "New. Bold. Unmissable. ✨☕\n\nIntroducing {PRODUCT} — our newest creation that brings the best of Cambodian coffee culture to your cup.\n\nTry it today at {LOCATION}!",
        "ថ្មី។ Bold។ ខកខានមិនបាន។ ✨☕\n\nណែនាំ {PRODUCT} — ការបង្កើតថ្មីៗ ដែលបង្ហាញពីវប្បធម៌កាហ្វេខ្មែរ!\n\nសាកល្បងថ្ងៃនេះនៅ {LOCATION}!"
    ),
    (
        "A new sip story begins today. ☕💫\n\n{PRODUCT} has officially joined our menu! Rich in flavor, crafted with care — this one's a game changer.\n\nAvailable at all our branches now.",
        "រឿងនៃការពិសាថ្មីចាប់ផ្ដើមថ្ងៃនេះ។ ☕💫\n\n{PRODUCT} ចូលម៉ឺនុយរបស់យើងហើយ! ជម្រៅរសជាតិ ផ្ទុកដោយចិត្ត — ការផ្លាស់ប្ដូរ!\n\nមានឥឡូវនៅគ្រប់សាខា។"
    ),
    (
        "We heard you asking for something different. ☕🌟\n\nSo we created {PRODUCT} — exclusively crafted for the daring coffee lovers of Phnom Penh.\n\nFirst taste? Come find us at {LOCATION}!",
        "យើងបានឮអ្នកស្នើរអ្វីផ្សេង។ ☕🌟\n\nដូច្នេះយើងបង្កើត {PRODUCT} — ផលិតពិសេសសម្រាប់អ្នកចូលចិត្តកាហ្វេ Bold នៃភ្នំពេញ!\n\nដំបូង? មករកយើងនៅ {LOCATION}!"
    ),
    (
        "Hot off the menu: {PRODUCT}! 🔥☕\n\nFresh, flavorful, and just what you need this {OCCASION}. Limited availability — don't miss out!\n\nOrder now at {LOCATION}.",
        "ថ្មីបំផុតពីម៉ឺនុយ: {PRODUCT}! 🔥☕\n\nស្រស់ ឆ្ងាញ់ ហើយគ្រប់យ៉ាងដែលអ្នកត្រូវការ {OCCASION}! មានដែនកំណត់ — កុំខកខាន!\n\nកម្មង់ឥឡូវនៅ {LOCATION}។"
    ),
    (
        "They asked. We delivered. 🙌☕\n\nOur brand-new {PRODUCT} is finally here — smooth, satisfying, and made with premium Cambodian beans.\n\nFirst 50 customers get a free upgrade! 🎁",
        "ពួកគេស្នើ។ យើងបានផ្ដល់ជូន។ 🙌☕\n\n{PRODUCT} ថ្មីបំផុតរបស់យើងមកដល់ — ទន់ ពេញចិត្ត ហើយផលិតពីគ្រាប់កាហ្វេខ្មែរ Premium!\n\nអតិថិជន 50 ដំបូងទទួលការ Upgrade ឥតគិតថ្លៃ! 🎁"
    ),
    (
        "It's finally here and we're SO excited! 🥳\n\n{PRODUCT} is now on our menu, and trust us — one sip and you'll understand the hype.\n\nCome grab one at {LOCATION} before it's gone!",
        "ទីបំផុតវាមកដល់ហើយ ហើយយើងរំភើបណាស់! 🥳\n\n{PRODUCT} ឥឡូវនៅម៉ឺនុយ ហើយជឿយើង — ពិសាម្ដង ហើយអ្នកនឹងយល់!\n\nមក {LOCATION} មុននឹងអស់!"
    ),
    (
        "Your daily coffee just got an upgrade. ☕✨\n\nMeet {PRODUCT} — our newest drink that's equal parts beautiful and delicious.\n\nAvailable starting {TIME} at all branches!",
        "កាហ្វេប្រចាំថ្ងៃរបស់អ្នកត្រូវបានប្រសើរ! ☕✨\n\nស្វាគមន៍ {PRODUCT} — ភេសជ្ជៈថ្មីស្អាត ហើយឆ្ងាញ់ស្មើគ្នា!\n\nមានចាប់ from {TIME} នៅគ្រប់សាខា!"
    ),
],

# ─── DAILY MOMENT (700) ──────────────────────────────────────────────────────
"daily_moment": [
    (
        "The only way to start your morning right. ☀️\n\nA cup of {PRODUCT} and you're ready to take on the day. See you at {LOCATION}!\n\nTag a coffee lover! ❤️",
        "វិធីតែមួយគត់ដើម្បីចាប់ផ្ដើមព្រឹកល្អ។ ☀️\n\nមួយកែវ {PRODUCT} ហើយអ្នកត្រៀមប្រឈមមុខថ្ងៃ! ជួបគ្នានៅ {LOCATION}!\n\nTag អ្នកស្រឡាញ់កាហ្វេ! ❤️"
    ),
    (
        "Monday mornings hit different with a good cup of coffee. ☕\n\nFuel up with our {PRODUCT} and make this week count. You've got this! 💪\n\nCome see us at {LOCATION}.",
        "ព្រឹកថ្ងៃចន្ទ ខុសពីគេ ជាមួយកាហ្វេល្អ។ ☕\n\nញ៉ាំ {PRODUCT} ហើយ make this week count! អ្នកធ្វើបាន! 💪\n\nជួបគ្នានៅ {LOCATION}។"
    ),
    (
        "Afternoon slump? We've got the cure. ☕✨\n\nOur {PRODUCT} is the perfect pick-me-up to power through the rest of your day.\n\nStop by {LOCATION} for yours!",
        "រឿងអស់កម្លាំងពេលរសៀល? យើងមានដំណោះស្រាយ! ☕✨\n\n{PRODUCT} របស់យើងគឺ pick-me-up ល្អឥតខ្ចោះ ដើម្បីឆ្ពោះទៅមុខ!\n\nឈប់ {LOCATION} យកមួយ!"
    ),
    (
        "Some days you need more than one cup. 😂☕\n\nNo judgment here. Our {PRODUCT} is ready and waiting for you at {LOCATION}.\n\nTag a coffee addict you know! ☕❤️",
        "ថ្ងៃខ្លះអ្នកត្រូវការជាងមួយកែវ! 😂☕\n\nមិនជំទាស់ទេ! {PRODUCT} របស់យើងត្រៀមរង់ចាំ at {LOCATION}!\n\nTag friend ស្រឡាញ់កាហ្វេ! ☕❤️"
    ),
    (
        "Good coffee makes everything better. ☕💛\n\nWhether you're working, studying, or just taking a break — our {PRODUCT} is the companion you need.\n\nCome chill with us at {LOCATION}.",
        "កាហ្វេល្អ ធ្វើអោយអ្វីៗប្រសើរ! ☕💛\n\nមិនថាអ្នកធ្វើការ រៀន ឬសម្រាក — {PRODUCT} គឺ companion ដែលអ្នកត្រូវការ!\n\nមកសម្រាក {LOCATION}។"
    ),
    (
        "Weekend mornings deserve the best. 🌅☕\n\nSlow down, breathe, and enjoy a beautifully crafted {PRODUCT} with us.\n\nSee you at {LOCATION} this weekend!",
        "ព្រឹកចុងសប្ដាហ៍ deserve the best! 🌅☕\n\nឈប់ ដកដង្ហើម ហើយរីករាយ {PRODUCT} ដ៏ស្រស់ស្អាត!\n\nជួបគ្នានៅ {LOCATION} ចុងសប្ដាហ៍!"
    ),
    (
        "That first sip of the morning — pure magic. ✨☕\n\nStart your day right with our {PRODUCT}. Fresh brewed, full of flavor.\n\nAvailable daily at {LOCATION}.",
        "ការពិសាដំបូងពេលព្រឹក — ជាការអស្ចារ្យ! ✨☕\n\nចាប់ផ្ដើមថ្ងៃល្អ ជាមួយ {PRODUCT}! ចំអិនស្រស់ ពោរពេញរសជាតិ!\n\nមានរៀងរាល់ថ្ងៃ {LOCATION}។"
    ),
    (
        "Rainy day + {PRODUCT} = perfect combo. 🌧️☕\n\nDon't let the rain ruin your mood. Come cozy up with us at {LOCATION}.\n\nWarm drinks, warm vibes. Always. ❤️",
        "ថ្ងៃភ្លៀង + {PRODUCT} = combo ល្អ! 🌧️☕\n\nកុំឱ្យភ្លៀងខូចអារម្មណ៍! មកសម្រាកជាមួយយើង {LOCATION}!\n\nភេសជ្ជៈក្ដៅ Vibes ក្ដៅ! ❤️"
    ),
    (
        "Study mode: ON. Coffee: REQUIRED. ☕📚\n\nPower up your study session with our {PRODUCT}. Free Wi-Fi + good coffee = productivity unlocked.\n\nCome study with us at {LOCATION}!",
        "Mode រៀន: ON។ កាហ្វេ: ត្រូវការ! ☕📚\n\nផ្ដល់ Power ដល់ session រៀន ជាមួយ {PRODUCT}! Wi-Fi ឥតគិតថ្លៃ + កាហ្វេ = Productivity!\n\nមករៀនជាមួយ {LOCATION}!"
    ),
    (
        "It's a {PRODUCT} kind of day. ☕🌤️\n\nSometimes all you need is a great cup of coffee to make everything click. We're here for you.\n\nFind us at {LOCATION}.",
        "ថ្ងៃ {PRODUCT}! ☕🌤️\n\nពេលខ្លះអ្នកត្រូវការតែកាហ្វេល្អ ដើម្បីធ្វើអោយអ្វីៗ Click! យើងនៅទីនេះ!\n\nស្វែងរកយើងនៅ {LOCATION}។"
    ),
    (
        "Coffee break? More like coffee TREAT. ☕🎁\n\nYou've worked hard today. Reward yourself with our {PRODUCT} — you deserve it!\n\nStop by {LOCATION} on your way home.",
        "Coffee Break? ហ្នឹងហើយ Coffee Treat! ☕🎁\n\nអ្នកធ្វើការដ៏ខ្លាំងថ្ងៃនេះ! Reward ខ្លួន ជាមួយ {PRODUCT} — អ្នកទទួលបានវា!\n\nឈប់ {LOCATION} ពេលត្រលប់ផ្ទះ!",
    ),
    (
        "Rise and shine, Phnom Penh! ☀️☕\n\nKick off your morning with our beloved {PRODUCT}. Nothing beats a hot cup to fuel your hustle.\n\nSee you at {LOCATION}!",
        "ក្រោក ភ្ញាក់ ភ្នំពេញ! ☀️☕\n\nចាប់ផ្ដើមព្រឹក ជាមួយ {PRODUCT} ដ៏ស្រឡាញ់! គ្មានអ្វីឈ្នះ cup ក្ដៅ ដើម្បី fuel ការខំប្រឹង!\n\nជួបគ្នា {LOCATION}!"
    ),
    (
        "Hustle hard. Sip harder. ☕💪\n\nLong day ahead? Our {PRODUCT} has your back. Crafted for those who don't stop.\n\nVisit us at {LOCATION}.",
        "Hustle Hard! Sip Harder! ☕💪\n\nថ្ងៃវែងខាងមុខ? {PRODUCT} នៅក្រោយអ្នក! ផលិតសម្រាប់អ្នកដែលមិនឈប់!\n\nមក {LOCATION}!",
    ),
    (
        "Because you deserve a little something nice today. ✨☕\n\nTreat yourself to our {PRODUCT} — smooth, comforting, and made just for you.\n\nWe're at {LOCATION} waiting with a smile!",
        "ព្រោះអ្នកdeserve អ្វីល្អ​ today! ✨☕\n\nTreat ខ្លួន ជាមួយ {PRODUCT} — ទន់ ផ្ទុក ហើយផលិតសម្រាប់អ្នក!\n\nយើងនៅ {LOCATION} រង់ចាំ ជាមួយ smile!"
    ),
    (
        "Coffee is a language everyone speaks. ☕🗣️\n\nShare a cup, share a moment. Our {PRODUCT} is best enjoyed with good company.\n\nBring someone you love to {LOCATION}!",
        "កាហ្វេ គឺជាភាសា ដែលគ្រប់គ្នានិយាយ! ☕🗣️\n\nចែករំលែក Cup ចែករំលែក Moment! {PRODUCT} ល្អបំផុត ជាមួយ company ល្អ!\n\nនាំគ្នាទៅ {LOCATION}!"
    ),
    (
        "No alarm needed when coffee is waiting. ☕🌅\n\nOur {PRODUCT} is your reason to get up and glow. Rich, bold, and absolutely perfect.\n\nMorning crew, we'll see you at {LOCATION}!",
        "មិនត្រូវការ Alarm ពេល Coffee រង់ចាំ! ☕🌅\n\n{PRODUCT} គឺ reason ដើម្បីក្រោក! Rich Bold ហើយ Perfect!\n\nMorning Crew ជួបគ្នា {LOCATION}!"
    ),
],

# ─── PROMOTION (500) ─────────────────────────────────────────────────────────
"promotion": [
    (
        "HAPPY HOUR ALERT! 📢✨\n\nBuy 1 Get 1 FREE on our {PRODUCT} from {HOURS} today only! Don't miss this deal at {LOCATION}.\n\nGrab a friend and come over! 🏃💨",
        "HAPPY HOUR មកដល់ហើយ! 📢✨\n\nទិញ ១ ថែម ១ ឥតគិតថ្លៃ {PRODUCT} ចាប់ពី {HOURS} ថ្ងៃនេះ! កុំខកខាននៅ {LOCATION}!\n\nបបួលមិត្ត ហើយចូល! 🏃💨"
    ),
    (
        "Flash sale — right now! ⚡☕\n\nGet {DISCOUNT} on our {PRODUCT} today only! This deal expires at midnight, so come fast.\n\nFind us at {LOCATION}. See you there! 🎉",
        "Flash Sale ឥឡូវ! ⚡☕\n\nទទួल {DISCOUNT} ចំពោះ {PRODUCT} ថ្ងៃនេះ! Deal អស់នៅ Midnight ដូច្នេះ Come Fast!\n\nស្វែងរកយើង {LOCATION}! 🎉"
    ),
    (
        "Students, this one's for you! 🎓☕\n\nFlash your student ID and enjoy {DISCOUNT} on any drink, including our {PRODUCT}.\n\nStudy fuel never felt this affordable. Come to {LOCATION}!",
        "Students ម្នាក់ៗ! 🎓☕\n\nបង្ហាញ Student ID ហើយ enjoy {DISCOUNT} លើ Drink ណាក៏ដោយ រួមមាន {PRODUCT}!\n\nStudy Fuel ថោកជាងនេះ! Come to {LOCATION}!"
    ),
    (
        "It's your birthday? Free coffee on us! 🎂☕\n\nCelebrate your special day with a complimentary {PRODUCT} — because you deserve it.\n\nShow us your birthday and come to {LOCATION} this month!",
        "Birthday? Coffee ឥតគិតថ្លៃ! 🎂☕\n\nсвяткуйте ថ្ងៃពិសេស ជាមួយ {PRODUCT} ឥតគិតថ្លៃ — ព្រោះអ្នកទទួលបានវា!\n\nបង្ហាញ Birthday ហើយ come {LOCATION}!"
    ),
    (
        "Weekend deal you can't ignore! 🎉☕\n\nEnjoy {DISCOUNT} on our {PRODUCT} this weekend only. The perfect excuse to treat yourself!\n\nSee you at {LOCATION}. Bring your whole crew!",
        "Deal ចុងសប្ដាហ៍ ignore មិនបាន! 🎉☕\n\nEnjoy {DISCOUNT} ចំពោះ {PRODUCT} ចុងសប្ដាហ៍នេះ! Excuse ល្អ Treat ខ្លួន!\n\nជួបគ្នា {LOCATION}! Bring your whole crew!"
    ),
    (
        "Loyalty pays off! 🏆☕\n\nCollect 10 stamps and your next {PRODUCT} is on us — completely FREE! Start collecting today.\n\nAsk about our loyalty card at {LOCATION}.",
        "Loyalty បង្ហាញ Result! 🏆☕\n\nប្រមូល Stamp ១០ ហើយ {PRODUCT} បន្ទាប់ Free! ចាប់ផ្ដើមប្រមូលថ្ងៃនេះ!\n\nសួរ Loyalty Card {LOCATION}។"
    ),
    (
        "Early bird gets the deal! 🐦☕\n\nFirst 30 customers get {DISCOUNT} off their order — any drink, any size. Including {PRODUCT}!\n\nBe at {LOCATION} by 9 AM to claim yours.",
        "Early Bird ទទួলបាន Deal! 🐦☕\n\nអតិថិជន 30 ដំបូង ទទួl {DISCOUNT} ចំពោះ Order ណាក៏ដោយ! រួមមាន {PRODUCT}!\n\nមកដល់ {LOCATION} មុន ម៉ោង ៩ ព្រឹក!"
    ),
    (
        "Refer a friend, both of you save! 👫☕\n\nBring a new customer to {LOCATION} and you both get {DISCOUNT} off your next order.\n\nShare the love and share the savings! ❤️",
        "Refer Friend ទាំងពីរ Save! 👫☕\n\nនាំ Customer ថ្មី {LOCATION} ហើយទាំងពីរ ទទួl {DISCOUNT} ចំពោះ Order បន្ទាប់!\n\nShare ចិត្ត Share ការសន្សំ! ❤️"
    ),
    (
        "Bring your own cup, save money. ♻️☕\n\nUse a reusable cup at {LOCATION} and enjoy {DISCOUNT} on any drink including {PRODUCT}.\n\nGood for you. Good for the planet. Win-win! 🌿",
        "យក Cup ខ្លួន Save ប្រាក់! ♻️☕\n\nប្រើ Reusable Cup {LOCATION} ហើយ enjoy {DISCOUNT} Drink ណាក៏ដោយ!\n\nល្អសម្រាប់អ្នក! ល្អសម្រាប់ Planet! Win-Win! 🌿"
    ),
    (
        "App users — exclusive deal unlocked! 📱☕\n\nOrder {PRODUCT} through our app and get {DISCOUNT} off your first order. Easy, fast, and rewarding!\n\nDownload now and head to {LOCATION}.",
        "App Users — Exclusive Deal Unlocked! 📱☕\n\nកម្មង់ {PRODUCT} តាម App ហើយ ទទួl {DISCOUNT} ចំពោះ Order ដំបូង!\n\nDownload ឥឡូវ ហើយ head to {LOCATION}！"
    ),
    (
        "{OCCASION} Special! 🎊☕\n\nTo celebrate, we're offering {DISCOUNT} on all drinks including {PRODUCT}.\n\nCome celebrate with us at {LOCATION}. Limited time only!",
        "{OCCASION} ពិសេស! 🎊☕\n\nដើម្បីсвяткувати, យើងផ្ដល់ {DISCOUNT} ចំពោះ Drink ទាំងអស់ {PRODUCT}!\n\nCelebrate ជាមួយ {LOCATION}! Limited Time!"
    ),
    (
        "BIG DEAL. Small Price. ⚡🎉\n\nOur {PRODUCT} is now {DISCOUNT} — but only until {TIME}! Don't wait, this won't last.\n\nRush to {LOCATION} now!",
        "DEAL ធំ! តម្លៃតូច! ⚡🎉\n\n{PRODUCT} ឥឡូវ {DISCOUNT} — មានតែ until {TIME}! កុំ Wait! វានឹងមិនទ្រាំ!\n\nRush to {LOCATION}!"
    ),
],

# ─── ENGAGEMENT (400) ────────────────────────────────────────────────────────
"engagement": [
    (
        "What's your go-to morning drink? 🤔☕\n\nAre you Team Iced or Team Hot? Drop your answer below — we're curious!\n\nP.S. If it's {PRODUCT}, you have great taste! 😄",
        "តើ Drink ពេលព្រឹករបស់អ្នកគឺអ្វី? 🤔☕\n\nTEAM ICED ឬ TEAM HOT? Drop ចម្លើយខាងក្រោម — យើងចង់ដឹង!\n\nP.S. ប្រសិន {PRODUCT} — អ្នក great taste! 😄"
    ),
    (
        "Coffee personality check! ☕🧠\n\nIced Latte = chill but productive.\nEspresso = no time to waste.\n{PRODUCT} = you live your best life. 😂\n\nWhich one are you? Tell us below! 👇",
        "Coffee Personality Check! ☕🧠\n\nIced Latte = Chill but Productive!\nEspresso = No Time!\n{PRODUCT} = Living Best Life! 😂\n\nអ្នកជាប្រភេទណា? ប្រាប់ Comment ខាងក្រោម! 👇"
    ),
    (
        "Tag the friend who NEEDS this right now! ☕👇\n\nOne {PRODUCT}, perfect weather, and good company — sounds like the best afternoon to us! 🌟",
        "Tag friend ដែលត្រូវការវា ឥឡូវ! ☕👇\n\n{PRODUCT} មួយ Weather ល្អ ហើយ Company ល្អ — ថ្ងៃរសៀលល្អ! 🌟"
    ),
    (
        "This or that? You decide! ☕🗳️\n\n{PRODUCT} ❤️ or Classic Iced Americano 💙?\n\nVote in the comments and let us know your winner! The most popular gets a discount this weekend. 😱",
        "This or That? អ្នកសម្រេច! ☕🗳️\n\n{PRODUCT} ❤️ ឬ Classic Iced Americano 💙?\n\nVote comment ប្រាប់ Winner! Most Popular ទទួl Discount ចុងសប្ដាហ៍! 😱"
    ),
    (
        "We want to hear from you! 💬☕\n\nWhat's your favorite drink from our menu? Drop it below and we'll feature the top 3 on our next post!\n\nDon't forget to tag us sipping on {PRODUCT}! 📸",
        "យើងចង់ Hear ពី អ្នក! 💬☕\n\n{PRODUCT} Favorite ពី Menu យើង? Drop ខាងក្រោម ហើយយើង Feature Top 3!\n\nTag យើង Sipping {PRODUCT}! 📸"
    ),
    (
        "GIVEAWAY TIME! 🎁☕\n\nWin a FREE {PRODUCT} (and more!) — here's how:\n✅ Follow us\n✅ Like this post\n✅ Tag 2 friends below\n\nWinner announced Friday! Good luck! 🍀",
        "Giveaway Time! 🎁☕\n\nឈ្នះ {PRODUCT} FREE ហើយ MORE! ដូចនេះ:\n✅ Follow យើង\n✅ Like Post\n✅ Tag Friend 2 ខាងក្រោម\n\nWinner ប្រកាស ថ្ងៃសុក្រ! Good Luck! 🍀"
    ),
    (
        "Quick question for our coffee fam! ☕❓\n\nHot coffee or iced coffee?\n\nWe know {PRODUCT} wins in this heat, but let's hear your take! Drop a ☕ for hot or 🧊 for iced!",
        "Quick Question សម្រាប់ Coffee Fam! ☕❓\n\nHot Coffee ឬ Iced Coffee?\n\nយើងដឹង {PRODUCT} ឈ្នះ ក្នុង Heat នេះ! Drop ☕ for Hot ឬ 🧊 for Iced!"
    ),
    (
        "Describe your Monday using only a coffee order. ☕😂\n\nWe'll start: triple shot {PRODUCT} with extra everything. 💀\n\nTag the friend who gets it! 👇",
        "Describe Monday ដោយប្រើ Coffee Order! ☕😂\n\nចាប់ផ្ដើម: Triple Shot {PRODUCT} Extra Everything! 💀\n\nTag Friend ដែល Get It! 👇"
    ),
    (
        "Caption this! 📸☕\n\nBest caption for this photo of our {PRODUCT} wins a free drink! Comment below and we'll pick a winner on Sunday. ☕🏆\n\nLet's see your creativity, Phnom Penh!",
        "Caption This! 📸☕\n\nCaption ល្អបំផុត {PRODUCT} Photo ឈ្នះ Drink ឥតគិតថ្លៃ! Comment ហើយ Winner ថ្ងៃអាទិត្យ! 🏆\n\nLet's see Creativity Phnom Penh!"
    ),
    (
        "We're building our dream menu — and we need YOUR help! 🙏☕\n\nWhat flavor or drink do you wish we had? Comment below and the most-voted idea becomes real next month!\n\nYou love {PRODUCT}? What would YOU add?",
        "យើងស Build Dream Menu — ត្រូវការ YOUR Help! 🙏☕\n\nFlavor ឬ Drink ណាដែលអ្នកចង់? Comment ហើយ Most-Voted Idea Real ខែក្រោយ!\n\nអ្នក Love {PRODUCT}? អ្នក ADD អ្វី?"
    ),
    (
        "Be honest — how many coffees a day is too many? 😂☕\n\nWe're asking because our {PRODUCT} is THAT good and people keep coming back.\n\nTag your coffee twin! 👇❤️",
        "Honest — Coffee ប៉ុន្មានថ្ងៃ Too Many? 😂☕\n\nយើងសួរ ព្រោះ {PRODUCT} ល្អ ហើយ People Keep Coming Back!\n\nTag Coffee Twin! 👇❤️"
    ),
    (
        "Staff picks! 🌟☕\n\nThis week, our baristas are obsessed with {PRODUCT}. Ask about the 'staff secret twist' when you order! 😏\n\nCome find out what the buzz is about at {LOCATION}.",
        "Staff Picks! 🌟☕\n\nSប្ដាហ៍នេះ Barista យើង Obsessed ជាមួយ {PRODUCT}! សួររឿង 'Staff Secret Twist'! 😏\n\nCome find out the buzz at {LOCATION}!"
    ),
],

# ─── BRAND STORY (300) ───────────────────────────────────────────────────────
"brand_story": [
    (
        "Beyond the cup. 🇰🇭❤️\n\nWe source our beans directly from farmers in {ORIGIN} to bring you the authentic taste of Cambodia. Quality you can trust.\n\nSupport local. Drink local. ✨",
        "លើសពីកែវ! 🇰🇭❤️\n\nយើងស Source Beans ដោយផ្ទាល់ ពីកសិករ {ORIGIN} ដើម្បីរសជាតិពិត Cambodia!\n\nគាំទ្រ Local! Drink Local! ✨"
    ),
    (
        "From the hills of {ORIGIN} to your cup. 🌿☕\n\nEvery sip you take supports local Cambodian farmers who pour their heart into every harvest.\n\nThank you for drinking local. We're proud to serve you. 🙏",
        "ពី Hills {ORIGIN} ដល់ Cup អ្នក! 🌿☕\n\nRip ណាក៏ដោយ គាំទ្រ Farmer Cambodian ក្នុងស្រុក ដែល Pour Heart!\n\nអរគុណ Drink Local! ❤️"
    ),
    (
        "Good coffee starts with good people. 👐☕\n\nOur beans are ethically sourced from small-scale farmers in Cambodia's highlands — ensuring fair pay and sustainable farming.\n\nEvery cup you enjoy makes a difference. ☕🌱",
        "Coffee ល្អ ចាប់ផ្ដើម People ល្អ! 👐☕\n\nBeans Ethically Sourced ពី Farmer Small-Scale ក្នុង Highlands Cambodia — Fair Pay Sustainable!\n\nCup ណាអ្នក Enjoy Makes a Difference! 🌱"
    ),
    (
        "We didn't start this to just serve coffee. ❤️\n\nWe started it to celebrate Cambodian flavors, support local farmers, and build a community over every cup.\n\nThank you for being part of our story. ☕🇰🇭",
        "យើងមិន Start ដើម្បីតែ Serve Coffee! ❤️\n\nយើង Start ដើម្បី Celebrate Khmer Flavors Support Farmer ក្នុងស្រុក Build Community!\n\nអរគុណ Part of Our Story! ☕🇰🇭"
    ),
    (
        "The secret ingredient? Passion. ☕🔥\n\nOur baristas spend years mastering the art of {BREWING} to bring you a cup that's more than just coffee — it's an experience.\n\nCome taste the difference at {LOCATION}.",
        "Ingredient 비밀? Passion! ☕🔥\n\nBarista យើង ចំណាយ Years Mastering Art {BREWING} ដើម្បី Cup ដែល More Than Just Coffee!\n\nCome Taste the Difference {LOCATION}!"
    ),
    (
        "Did you know? 🌱☕\n\nCambodia has been growing coffee since the French colonial era. Today, farmers in {ORIGIN} are reviving this heritage with single-origin beans.\n\nEvery cup you drink connects you to this story.",
        "តើអ្នកដឹងទេ? 🌱☕\n\nCambodia Growing Coffee ចាប់ពី French Colonial Era! ឥឡូវ Farmer {ORIGIN} Revive Heritage Single-Origin Beans!\n\nCup ណាអ្នក Drink Connect Story នេះ!"
    ),
    (
        "Sustainability isn't a trend for us — it's who we are. 🌿☕\n\nFrom compostable cups to partnering with eco-friendly farms in {ORIGIN}, every choice we make is for a greener tomorrow.\n\nDrink good. Do good.",
        "Sustainability មិនមែន Trend — គឺ WHO WE ARE! 🌿☕\n\nពី Compostable Cups ដល់ Eco-Friendly Farms {ORIGIN} ជំរើស ណាក៏ដោយ For Greener Tomorrow!\n\nDrink Good! Do Good!"
    ),
    (
        "Behind every great cup is a great team. 👩‍🍳☕\n\nOur baristas, farmers, and team members are the heart of everything we do. We're honored to serve you every day.\n\nMeet our team at {LOCATION} sometime — they'd love to say hi!",
        "Behind Every Great Cup គឺ Great Team! 👩‍🍳☕\n\nBarista Farmer Team Members គឺ Heart នៃអ្វីៗ! Honored Serve Every Day!\n\nMeet Team {LOCATION} — They'd Love to Say Hi!"
    ),
    (
        "Brewing excellence, one cup at a time. ☕✨\n\nOur {BREWING} process is designed to bring out the natural flavors of our {ORIGIN} beans — no shortcuts, no compromise.\n\nTaste the craft at {LOCATION}.",
        "Brewing Excellence ម្ដងមួយ Cup! ☕✨\n\n{BREWING} Process ផ្ដល់ Natural Flavors {ORIGIN} Beans — No Shortcuts No Compromise!\n\nTaste the Craft {LOCATION}!"
    ),
    (
        "We believe in transparent sourcing. 🤝☕\n\nYou deserve to know where your coffee comes from. Ours is from partner farms in {ORIGIN} — direct trade, fair price, great quality.\n\nAsk your barista about our beans anytime!",
        "យើង Believe Transparent Sourcing! 🤝☕\n\nអ្នក Deserve ដឹង Coffee ពីណា! Partner Farms {ORIGIN} — Direct Trade Fair Price Great Quality!\n\nAsk Barista ពី Beans ពេលណា!"
    ),
    (
        "Coffee with a conscience. 🌱🇰🇭\n\nFor every bag of {ORIGIN} beans we sell, a portion goes back to the farming families who grew them. Small cup, big impact.\n\nShop our beans at {LOCATION}.",
        "Coffee With a Conscience! 🌱🇰🇭\n\nBag {ORIGIN} Beans ណាក៏ដោយ Portion ត្រឡប់ Farming Families! Small Cup Big Impact!\n\nShop Beans {LOCATION}!"
    ),
],

}

# ──────────────────────────────────────────────────────────────────────────────
# Metadata builders per category
# ──────────────────────────────────────────────────────────────────────────────

MOOD_MAP = {
    "product_launch": [
        "exciting, fresh", "innovative, premium", "tropical, refreshing",
        "limited, exclusive", "bold, vibrant", "seasonal, festive",
        "cozy, warm", "exclusive, indulgent",
    ],
    "daily_moment": [
        "energizing, motivational", "comforting, cozy", "relaxing, calm",
        "productive, focused", "cheerful, uplifting", "nostalgic, warm",
        "refreshing, revitalizing", "cozy, slow",
    ],
    "promotion": [
        "urgent, exciting", "value-focused, cheerful", "limited-time, urgent",
        "festive, generous", "playful, energetic", "generous, warm",
    ],
    "engagement": [
        "playful, interactive", "fun, community-focused",
        "curious, conversational", "lighthearted, relatable",
    ],
    "brand_story": [
        "authentic, inspiring", "educational, heartfelt",
        "values-driven, sincere", "local, proud", "sustainable, hopeful",
    ],
}

OCCASION_MAP = {
    "product_launch": [
        "new menu launch", "seasonal launch", "limited edition drop",
        "summer launch", "Khmer New Year launch", "anniversary special",
        "weekend exclusive", "holiday edition", "premium range debut",
        "new branch opening", "collab launch",
    ],
    "daily_moment": [
        "Monday morning", "early morning fuel", "afternoon slump",
        "work from cafe", "study session", "weekend brunch",
        "rainy day comfort", "Friday feeling", "late night study",
        "morning ritual", "post-gym refuel", "Sunday slow morning",
        "afternoon break", "evening unwind",
    ],
    "promotion": [
        "happy hour", "flash sale", "student discount day",
        "birthday promo", "loyalty reward", "Khmer New Year deal",
        "Water Festival special", "weekday offer", "app-exclusive deal",
        "BOGO weekend", "early bird offer", "referral reward",
    ],
    "engagement": [
        "weekend poll", "taste test", "tag a friend challenge",
        "community question", "this or that", "giveaway",
        "feedback request", "monthly favorite vote", "caption contest",
    ],
    "brand_story": [
        "farm-to-cup story", "Cambodian coffee heritage", "ethical sourcing",
        "brewing spotlight", "local farmer partnership",
        "sustainability", "team story", "origin story", "roasting process",
    ],
}

PROMO_MAP = {
    "product_launch": ["new menu item", "limited edition", "seasonal special", None],
    "daily_moment":   [None, None, "loyalty points", None, None],
    "promotion": [
        "20% off", "Buy 1 Get 1 Free", "flash sale 30% off",
        "student discount 15%", "birthday free drink",
        "happy hour 2-for-1", "free size upgrade", "app discount 25%",
        "loyalty reward free drink", "referral discount",
    ],
    "engagement":   [None, None, "giveaway prize"],
    "brand_story":  [None],
}

# ──────────────────────────────────────────────────────────────────────────────
# Entry generator
# ──────────────────────────────────────────────────────────────────────────────

def make_entry(idx: int, category: str) -> dict:
    # Pick product
    if category == "brand_story":
        product = random.choice([
            "Mondulkiri Single-Origin", "Ratanakiri Arabica", "Kampot Robusta",
            "Local Blend", "Single-Origin Espresso", "Cold Brew",
            "Pour Over", "Signature Blend",
        ])
    else:
        product = random.choice(PRODUCTS)

    location   = random.choice(LOCATIONS)
    discount   = random.choice(DISCOUNTS)
    hours      = random.choice(HOURS)
    time_      = random.choice(TIMES)
    origin     = random.choice(BEAN_ORIGINS)
    brewing    = random.choice(BREWING_METHODS)
    occasion_v = random.choice(OCCASION_MAP[category])
    cultural   = random.choice(CULTURAL_OCCASIONS)

    # 15% chance to swap occasion for a cultural one
    if random.random() < 0.15:
        occasion_v = cultural

    # Pick a template pair
    tpl_en, tpl_km = random.choice(TEMPLATES[category])

    # Fill in placeholders
    def fill(t: str) -> str:
        return (
            t.replace("{PRODUCT}",   product)
             .replace("{LOCATION}",  location)
             .replace("{DISCOUNT}",  discount)
             .replace("{HOURS}",     hours)
             .replace("{TIME}",      time_)
             .replace("{ORIGIN}",    origin)
             .replace("{BREWING}",   brewing)
             .replace("{OCCASION}",  occasion_v)
        )

    caption_en = fill(tpl_en)
    caption_km = fill(tpl_km)

    # Hashtags
    en_tags = random.choice(EN_TAGS[category])
    km_tags = random.choice(KM_TAGS[category])

    # Build metadata
    promotion = random.choice(PROMO_MAP[category])

    return {
        "id": idx,
        "category": category,
        "metadata": {
            "product": product,
            "promotion": promotion,
            "mood": random.choice(MOOD_MAP[category]),
            "occasion": occasion_v,
            "target_audience": random.choice(AUDIENCES),
        },
        "caption": {
            "en": caption_en,
            "km": caption_km,
        },
        "hashtags": {
            "en": en_tags,
            "km": km_tags,
        },
    }


# ──────────────────────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────────────────────

def main():
    random.seed(42)   # reproducible shuffle, change to generate a different set
    all_entries = []
    idx = 1

    print("=" * 55)
    print("POSTNOW — Offline 2500 Caption Generator")
    print("=" * 55)

    for category, count in TARGET.items():
        print(f"  Generating {count:>4} × {category}…", end=" ", flush=True)
        for _ in range(count):
            all_entries.append(make_entry(idx, category))
            idx += 1
        print("done")

    # Shuffle so categories are mixed
    random.shuffle(all_entries)

    # Re-number IDs after shuffle
    for i, entry in enumerate(all_entries, 1):
        entry["id"] = i

    dataset = {
        "dataset_info": {
            "total_captions": len(all_entries),
            "language_pair": "en-km",
            "created_for": "POSTNOW mBART fine-tuning",
            "categories": {cat: count for cat, count in TARGET.items()},
        },
        "captions": all_entries,
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(dataset, f, ensure_ascii=False, indent=2)

    print()
    print(f"✅  Saved {len(all_entries)} captions → {OUTPUT_FILE}")
    print(f"    File size: {OUTPUT_FILE.stat().st_size / 1024:.1f} KB")


if __name__ == "__main__":
    main()

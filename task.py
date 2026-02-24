import json
import re
import mysql.connector
from datetime import datetime


# -------------------- DATABASE CONNECTION --------------------

def create_connection():
    try:
        return mysql.connector.connect(
            host="localhost",
            user="root",
            password="actowiz",
            database="zomato"
        )
    except mysql.connector.Error as err:
        print("Database Connection Error:", err)
        return None


# -------------------- CREATE TABLES --------------------

def create_table(cursor):

    cursor.execute("DROP TABLE IF EXISTS items")
    cursor.execute("DROP TABLE IF EXISTS restaurants")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS restaurants (
            restaurant_id BIGINT PRIMARY KEY,
            restaurant_name VARCHAR(150),
            restaurant_url TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS items (
            item_id VARCHAR(100) PRIMARY KEY,
            restaurant_id BIGINT,
            category_name VARCHAR(100) NULL,
            item_name VARCHAR(255),
            item_slugs TEXT,
            item_description TEXT,
            is_veg BOOLEAN,
            FOREIGN KEY (restaurant_id) REFERENCES restaurants(restaurant_id)
                ON DELETE CASCADE
        )
    """)


# -------------------- LOAD JSON --------------------

def input_file(json_file):
    try:
        with open(json_file, 'r', encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print("Error reading file:", e)
        return None


# -------------------- PARSER (YOUR LOGIC FIXED) --------------------

def parser(d):

    new = {}

    section_info = d["page_data"]["sections"]["SECTION_BASIC_INFO"]
    section_contact = d["page_data"]["sections"]["SECTION_RES_CONTACT"]
    section_header = d["page_data"]["sections"]["SECTION_RES_HEADER_DETAILS"]["LOCALITY"]

    new["restaurant_Id"] = section_info["res_id"]
    new["restaurant_name"] = section_info["name"]
    new["restaurant_url"] = section_header["url"]
    new["restaurant_contact"] = [section_contact["phoneDetails"]["phoneStr"]]

    # License number
    lic = d["page_data"]["order"]["menuList"]["fssaiInfo"]["text"]
    match = re.search(r"\d+", lic)
    new["fssai_licence_number"] = match.group() if match else None

    # Address
    new["address_info"] = {}
    new["address_info"]["full_address"] = section_contact["address"]
    new["address_info"]["city"] = section_contact["city_name"]
    new["address_info"]["pincode"] = section_contact["zipcode"]
    new["address_info"]["state"] = section_contact.get("state", None)

    # Cuisines
    new["cuisines"] = []
    cuisine = d["page_data"]["sections"]["SECTION_RES_HEADER_DETAILS"]["CUISINES"]

    for c in cuisine:
        new["cuisines"].append({
            "name": c["name"],
            "url": c["url"]
        })

    # Timings
    new["timings"] = {}
    timing = d["page_data"]["sections"]["SECTION_BASIC_INFO"]["timing"]["customised_timings"]["opening_hours"][0]["timing"]

    days = ["monday","tuesday","wednesday","thursday","friday","saturday","sunday"]

    parts = [t.strip() for t in timing.split()]
    open_time = parts[0]
    close_time = parts[2]

    if open_time.lower() in ["12noon", "noon"]:
        open_time = "12pm"

    for day in days:
        new["timings"][day] = {
            "open": open_time,
            "close": close_time
        }

    # -------------------- MENU PARSING --------------------

    new["items"] = []

    menus = d["page_data"]["order"]["menuList"]["menus"]

    for menu in menus:
        categories = menu["menu"]["categories"]

        for cat in categories:

            category_name = cat["category"]["name"]

            # If category empty → use menu name
            if not category_name:
                category_name = menu["menu"]["name"]

            # If still empty → NULL
            if not category_name:
                category_name = None

            items_d = cat["category"]["items"]

            for item_obj in items_d:
                item = item_obj["item"]

                dietary = item.get("dietary_slugs", [])
                is_veg = True if dietary and dietary[0] == "veg" else False

                item_entry = {
                    "restaurant_id": new["restaurant_Id"],
                    "category_name": category_name,
                    "item_id": item.get("id"),
                    "item_name": item.get("name"),
                    "item_slugs": item.get("tag_slugs"),
                    "item_description": item.get("desc"),
                    "is_veg": is_veg
                }

                new["items"].append(item_entry)

    return new

def write_jsondata(all_data):
    current_date = datetime.now().strftime("%d-%m-%Y")
    filename = f"ZOMATO_{current_date}.json"

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(all_data, f, indent=4, ensure_ascii=False)

    print("JSON file created:", filename)

def insert_into_db(connection, cursor, final_data):

    # Insert restaurant
    cursor.execute("""
        INSERT INTO restaurants (restaurant_id, restaurant_name, restaurant_url)
        VALUES (%s, %s, %s)
    """, (
        final_data["restaurant_Id"],
        final_data["restaurant_name"],
        final_data["restaurant_url"]
    ))

    # Insert items
    item_query = """
        INSERT INTO items
        (item_id, restaurant_id, category_name, item_name,
         item_slugs, item_description, is_veg)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """

    for item in final_data["items"]:
        cursor.execute(item_query, (
            item["item_id"],
            item["restaurant_id"],
            item["category_name"],  # NULL if None
            item["item_name"],
            ",".join(item.get("item_slugs", [])) if item.get("item_slugs") else None,
            item["item_description"],
            item["is_veg"]
        ))

    connection.commit()
    print("✅ Data inserted successfully!")


# -------------------- MAIN --------------------

def main():

    user_input = input("Enter JSON File Name: ")

    input_data = input_file(user_input)
    if not input_data:
        return

    final_data = parser(input_data)

    write_jsondata(final_data)

    connection = create_connection()
    if not connection:
        return

    cursor = connection.cursor()

    create_table(cursor)
    insert_into_db(connection, cursor, final_data)

    cursor.close()
    connection.close()


if __name__ == "__main__":
    main()
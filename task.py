import json
import calendar
from datetime import datetime

data_folder = dict()

# this function is load json data
def input_file(file_name):
    with open(file_name,"r") as f:
        data = json.load(f)
        return data
    
# this function process a data
def parser(data):
    # this variable are store path 
    temp_data1 =data['page_data']['sections']["SECTION_BASIC_INFO"]
    temp_data2 = data["page_data"]["sections"]["SECTION_RES_CONTACT"]
    temp_data3 = data["page_data"]["sections"]["SECTION_RES_HEADER_DETAILS"]["CUISINES"]


    data_folder["restaurant_Id"] = temp_data1["res_id"]
    data_folder["restaurant_name"] = temp_data1["name"]
    data_folder["restaurant_url"]= data["page_info"]["canonicalUrl"]
    data_folder["restaurant_contact"] = [temp_data2["phoneDetails"]["phoneStr"]]
    data_folder["fssai_licence_number"]= data["page_data"]["order"]["menuList"]["fssaiInfo"]["text"]

    data_folder["address_info"] = {
            'full_address' : temp_data2["address"],
            'region' : temp_data2["locality_verbose"].split(",")[0],
            "city" : temp_data2["city_name"],
            "pincode" : temp_data2["zipcode"],
            "state" : "Gujarat"
        }    
   
   # this loop is for cuisines
    data_folder["cuisines"]=[]
    for i in range(len(temp_data3)):
        data_folder["cuisines"].append({"name":temp_data3[i]["name"],"url":temp_data3[i]["url"]})


    time_structure = dict()
    timing_data = data['page_data']['sections']['SECTION_BASIC_INFO']['timing']['customised_timings']['opening_hours'][0]['timing']
    open_time = timing_data.split(" ")[0]
    close_time = timing_data.split(" ")[2]
    
    # find Weekday name using number calendar
    for i in range(0,7):
        day_name = calendar.day_name[i]
        time_structure[day_name] ={
            'open' : open_time,
            'close' : close_time
        }
    data_folder['timing'] = time_structure


    # this loop is for menulist
    for i in range(len(data["page_data"]["order"]["menuList"]["menus"])):
        menu = data["page_data"]["order"]["menuList"]["menus"][i]
        categories = menu["menu"]["categories"]
        
        for category in categories:
            category_data = {
                "category_name": category["category"]["name"],
                "items": []
            }

            items = category["category"]["items"]

            
            
            for item_obj in items:
                item = item_obj["item"]
                if item['dietary_slugs'][0] =='veg':
                    vegs =  True
                else:
                    vegs = False
                
                
                item_data = {
                    "item_id": item['id'],
                    "item_name": item["name"],
                    "item_slugs": item["tag_slugs"],
                    "item_description": item["desc"],
                    "is_veg": vegs
                }

                category_data["items"].append(item_data)

                if "menu_categories" not in data_folder:
                    data_folder["menu_categories"] = []
                data_folder["menu_categories"].append(category_data)
            return data_folder

# this Function works create file with json data
def write_jsondata(all_data):
    current_date = datetime.now().strftime('%d-%m-%Y')

    with open(f'ZOMATO_{current_date}.json', 'w') as f:
        json.dump(all_data, f, indent=4)


# user Input
user_input = input("Enter a File:")

# input_data is variable to store input_file function with parametre as user_input
input_data = input_file(user_input)

# final_data is variable to store parser function with parametre as input_data
final_data = parser(input_data)

# final function call with parameter final_data
write_jsondata(final_data)



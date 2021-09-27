import json
import pandas as pd
import numpy as np
import argparse

#=========================================================================================================
"""
- Uncomment section below in order to run the script via command line
- Example command to run via cmd:
     assignment.py -a "inventory.json" -b "products.json" -c "updated inventory.json" -d "Dining Chair" 
"""

# ap = argparse.ArgumentParser()
# ap.add_argument("-a", "--input_inv_file", required=True, help="input inventory json file name")
# ap.add_argument("-b", "--products_file", required=True, help="products json file name")
# ap.add_argument("-c", "--output_inv_file", required=True, help="output inventory json file name")
# ap.add_argument("-d", "--product", required=True, help="name of product")
# args = vars(ap.parse_args())
# args = ap.parse_args()

# inventory_file = args.input_inv_file
# products_file = args.products_file
# updated_inventory_file = args.output_inv_file
# product_name = args.product

#=========================================================================================================
"""
    Comment out section below in order to run the script via command line
"""

## Enter the input parameters here:

inventory_file = 'inventory.json'
products_file = 'products.json'
updated_inventory_file = 'updated inventory.json'
product_name = 'Dining Chair' # select one of 'Dining Chair' or 'Dinning Table'

#=========================================================================================================
## Inventory
# Reading the inventory JSON data to a dictionary file

with open(inventory_file) as inventory_file:
    dict_inventory = json.load(inventory_file)

## Products
# Reading the Products JSON data to a dictionary file

with open(products_file) as products_file:
    dict_products = json.load(products_file)

#=========================================================================================================
"""
    The code snippet below can be used to monitor the required articles for each product; 
"""

# for i in range(0, len(dict_inventory)):
#    for key, value in dict_inventory.items(): 
#        print(key + ':', value)

# for i in range(0, len(dict_products)):
#    for key, value in dict_products.items(): 
#        print(key + ':', value)

#=========================================================================================================
"""
    Create a DataFrame from inventory data
"""

## Create a DataFrame from inventory file by iterating over keys of inventory dictionary file
df_inventory = pd.DataFrame()
for key in dict_inventory.keys():
    inventory_value = dict_inventory.get(key)
    for item in inventory_value:
        df_single_item = pd.DataFrame([item])
        df_inventory = pd.concat([df_inventory, df_single_item])

# Set art_id column as index
df_inventory = df_inventory.set_index("art_id")
df_inventory["stock"] = df_inventory["stock"].astype(int)

print("Current inventory overview:")
print('====================================================')
print(df_inventory)
print('----------------------------------------------------')

#=========================================================================================================
# Create DataFrame from Products

## Create a DataFrame from products file by iterating over keys of products dictionary file
df_products = pd.DataFrame()
for key in dict_products.keys():
    prod_value = dict_products.get(key)
    for item in prod_value:
        df_single_item = pd.DataFrame([item])
        df_products = pd.concat([df_products, df_single_item])

# Create a list of names of all products
product_names = df_products.name.unique()

# set "name" column as index for each product DataFrame
new_df_products = df_products.set_index("name")

## Create a DataFrame for each product
def create_df_product(list_articles):
    """
    Creates a dataframe which represents the required articles for each product as a DataFrame
    """
    df_product = pd.DataFrame()
    for article in list_articles:
        df_single_article = pd.DataFrame([article])
        df_product = pd.concat([df_product, df_single_article])
    df_product["amount_of"] = df_product["amount_of"]
    return df_product.set_index("art_id")

#=========================================================================================================
# Create a function to get the list of available products in inventory with their quantity:

def get_quantity_of_available_product(product_names, latest_df_inventory):
    """
    This function get the list of product names and latest available articles in the inventory and returns the available quantity of
    each product in the inventory
    """
    dict_of_products_df = {}
    available_quantity_all_products = []

    for product in product_names:
        articles_list = new_df_products.loc[product, "contain_articles"]
        df_name = product + '_df'
        dict_of_products_df[df_name] = create_df_product(articles_list)

        # Outer join DataFrame of each product with inventory DataFrame to calculate the available quantity
        inventory_product_df =pd.concat([latest_df_inventory, dict_of_products_df[df_name]], axis=1)
        inventory_product_df["amount_of"] = inventory_product_df.amount_of.fillna(0).astype(int)

        # Calculate the possible quantity of each product to be sold by dividing available 'stock' of each article by the required "amount_of" it per product
        inventory_product_df["possible_quantity"] = inventory_product_df['stock'].div(inventory_product_df['amount_of'])
        possible_number_product = inventory_product_df.possible_quantity.min()

        if possible_number_product < 1:
            possible_number_product = 0

        available_quantity_all_products.append(possible_number_product) 

    return available_quantity_all_products    

#=========================================================================================================

def sell_a_product(
    product_name,
    latest_df_inventory, 
    quantity_of_available_product):

    """
    This function updates inventory dataframe after selling/removing a product from inventory.
    """

    articles_list = new_df_products.loc[product_name, "contain_articles"]
    df_name = product_name + '_df'
    df_name = create_df_product(articles_list)
    inventory_product_df =pd.concat([latest_df_inventory, df_name], axis=1)
    updated_inventory_df = latest_df_inventory.copy()

    # Calculate remaining quantity in the inventory
    if quantity_of_available_product >= 1 :
        inventory_product_df["amount_of"] = inventory_product_df.amount_of.fillna(0).astype(int)
        inventory_product_df["possible_quantity"] = inventory_product_df['stock'].div(inventory_product_df['amount_of']).replace(np.inf, 0).apply(np.floor)

        inventory_product_df["remaining_quantity"] = inventory_product_df["stock"] - inventory_product_df["amount_of"]
        updated_inventory_df["stock"] = inventory_product_df["remaining_quantity"]   

        quantity_of_available_product -= 1
        print(f"One {product_name} is sold")
        print(f"Latest quantity of {product_name} in stock is: {int(quantity_of_available_product)}")
        print("Overview of inventory after selling a product")
        print(updated_inventory_df)     
        
    elif quantity_of_available_product == 0 :
        updated_inventory_df["stock"] = inventory_product_df["stock"]
        print(f"{product_name} is out of stock!")
        quantity_of_available_product = 0

    return updated_inventory_df

# # Print available products in the inventory:
print("List of available products in inventory:")
print('====================================================')
for product, available_quantity in zip(product_names, get_quantity_of_available_product(product_names, df_inventory)):
    print (product, int(available_quantity))
print('----------------------------------------------------')

#=========================================================================================================
# Function to update inventory.json file

def update_inventory_json_file(dataframe, output_file_name):
    """
    This function update the inventory.json file according to latest status of inventory; Here new inventory data is saved as "updated inventory.json" file to keep the original 'inventory.json' file intact for furthur validation
    """
    dataframe = dataframe.reset_index()
    dataframe["stock"] = dataframe["stock"].astype(int).astype(str)
    result = dataframe.to_dict('records')
    data = {"inventory" : result}
    with open(output_file_name, 'w') as fp:
        json.dump(data, fp, indent = 2)

#=========================================================================================================
product_quantiy_dict = {product_names[0] : get_quantity_of_available_product(product_names, df_inventory)[0], product_names[1] : get_quantity_of_available_product(product_names, df_inventory)[1]}

"""
    - Add the name product to product_name variable below. Then by running the code, inventory.json is updated considering this product is sold/removed from inventory!
    - If the product name is not listed in product.json file, then a warning is shown to make sure product name is written correctly!
"""

if product_name in product_names:
    new_inventory_df = sell_a_product(product_name,  df_inventory, product_quantiy_dict[product_name])

    # Update and save inventory.json file
    df_inventory = new_inventory_df.copy()
    update_inventory_json_file(df_inventory, updated_inventory_file)

else:
    print(f"{product_name} is not a recognized product! Make sure you are entering the correct product name")
#=========================================================================================================


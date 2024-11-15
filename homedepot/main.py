# from serpapi import GoogleSearch
# import json
# params = {
#   "engine": "home_depot_product",
#   "product_id": "100232088",
#   "api_key": "77f58e0014e1cc571c9c598e6299408d86d56a4815835e8f75066a8568073599"
# }

# search = GoogleSearch(params)
# data = search.get_dict()

# with open("resultado.json", "w") as file:
#     json.dump(data, file, indent=4)

from serpapi import GoogleSearch
import pandas as pd



def main():
  lista = list()

  params = {
    "engine": "home_depot",
    "q": "fans",
    "hd_sort": 'top_sellers',
    "ps": 48,
    "page": 14, 
    "delivery_zip": "32809",
    "api_key": "77f58e0014e1cc571c9c598e6299408d86d56a4815835e8f75066a8568073599"
  }

  search = GoogleSearch(params)
  results = search.get_dict()
  total_products = results["search_information"]["total_results"]
  print(total_products)
  products = results["products"]

  for product in products:# Extraindo as informações desejadas
    model_number = product.get('model_number')
    brand = product.get('brand', None)  # Define como None se 'brand' não existir
    price = product.get('price', None)
    
    lista.append([model_number, price, brand, 'PartNumber'])
  
  print(model_number)
  df1 = pd.read_excel('fans.xlsx')
  df2 = pd.DataFrame(lista, columns=['Nome', 'Preço', 'Marca', 'TipoPlanilha'])
  df = pd.concat([df1, df2])
  df.to_excel('fans.xlsx', index=False)

if __name__ == "__main__":
  main()
  

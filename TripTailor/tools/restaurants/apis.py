import os
import pandas as pd
from geopy.distance import geodesic

class Restaurants:
    def __init__(self, relative_path="../../database_EN/restaurants.csv"):
         # Get the absolute path of the current file
        current_file_path = os.path.abspath(__file__)
        # Get the directory of the current file
        current_directory = os.path.dirname(current_file_path)
        # Construct the full path of the file
        self.path = os.path.join(current_directory, relative_path)
        
        # Attempt to read the CSV file
        try:
            self.data = pd.read_csv(self.path, low_memory=False)
        except FileNotFoundError:
            print(f"Error: The file {self.path} was not found.")
            self.data = None
        except Exception as e:
            print(f"An error occurred while reading the file: {e}")
            self.data = None

    def load_db(self):
        self.data = pd.read_csv(self.path, low_memory=False)
       
   
    def run(self, city, meal_cost_range, longitude, latitude, top_n=10):
         # 去除包含空值的行
        filtered_data = self.data.dropna().copy()

        # 过滤城市（忽略大小写）
        filtered_data = filtered_data[filtered_data['real_city'].str.lower() == city.lower()]

        # 过滤餐费范围
        filtered_data = filtered_data[
            (filtered_data['avg_price'] >= meal_cost_range[0]) &
            (filtered_data['avg_price'] <= meal_cost_range[1])
        ]

        # 计算距离
        filtered_data['distance'] = filtered_data.apply(
            lambda row: geodesic((latitude, longitude), (row['latitude'], row['longitude'])).kilometers,
            axis=1
        )

        # 根据距离排序并选取最近的top_n
        result = filtered_data.nsmallest(top_n, 'distance')
        return result


# 实例化并调用
# finder = Restaurants()
# result = finder.run('Harbin', [100, 200], 129.55464179978478, 46.32462172098222, top_n=10)
# print(result)
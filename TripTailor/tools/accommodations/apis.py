import os
import pandas as pd
from pandas import DataFrame
from typing import Optional


class Accommodations:
    def __init__(self, relative_path="../../database_EN/accommodations.csv"):
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

    def run(self, city, hotel_cost, sample_num=1):

        # 过滤城市和酒店成本类别（忽略大小写）
        filtered_data = self.data[(self.data['real_city'].str.lower() == city.lower()) & 
                                (self.data['small_cate'].str.lower() == hotel_cost.lower())]

        # 去除包含空值的行
        filtered_data = filtered_data.dropna()

        # 随机返回一行
        if not filtered_data.empty:
            if sample_num > 0 and sample_num <= len(filtered_data):
                return filtered_data.sample(n=sample_num)
            else:
                return filtered_data
        else:
            return None  # 或者返回其他表示没有找到匹配项的值
    
    def run_(self, city, sample_num=1):

        # 过滤城市和酒店成本类别（忽略大小写）
        filtered_data = self.data[self.data['real_city'].str.lower() == city.lower()]

        # 去除包含空值的行
        filtered_data = filtered_data.dropna()

        # 随机返回一行
        if not filtered_data.empty:
            if sample_num > 0 and sample_num <= len(filtered_data):
                return filtered_data.sample(n=sample_num)
            else:
                return filtered_data
        else:
            return None  # 或者返回其他表示没有找到匹配项的值


if __name__ == '__main__':
    accommodations = Accommodations()
    print(accommodations.run('Kaifeng', 'Luxury', sample_num=0))

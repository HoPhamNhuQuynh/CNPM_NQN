import pandas as pd
import numpy as np

# 1. Đọc file CSV
# Thay 'data.csv' bằng tên file của bạn
df = pd.read_csv('dataset_goc_guardian.csv')

# 2. Lọc bỏ các hàng có giá trị trong cột 'product_type' bằng 'Khác'
# Phương thức này tạo một DataFrame mới (df_filtered) chỉ chứa các hàng
# mà giá trị của cột 'product_type' KHÔNG PHẢI là 'Khác'
df_filtered = df[df['product_type'] != 'Khác']

# 3. (Tùy chọn) Lưu dữ liệu đã lọc vào một file CSV mới
df_filtered.to_csv('dataset_goc_guardian_clear.csv', index=False)

print("Đã lọc bỏ thành công các dòng có product_type là 'Khác'.")
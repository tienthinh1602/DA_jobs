import streamlit as st
import pandas as pd
import openai
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import matplotlib.pyplot as plt
from openai_utils import OpenAIAssistant
import json
import numpy as np

def display_data(data):
    if data is None or data.empty:
        st.write("Không có dữ liệu để hiển thị.")
        return
    if not data.empty:
        st.write("Dữ liệu mẫu:")
        rows_per_page = 20
        total_rows = len(data)
        num_pages = (total_rows // rows_per_page) + (1 if total_rows % rows_per_page > 0 else 0)
        page = st.number_input("Chọn trang: ", min_value=1, max_value=num_pages, step=1)
        start_idx = (page - 1) * rows_per_page
        end_idx = start_idx + rows_per_page
        st.write(data.iloc[start_idx:end_idx])

def execute_code(code, data):
    try:
        # Tạo một không gian riêng để thực thi mã
        local_scope = {'np': np, 'data': data, 'plt': plt}
        exec(code, {}, local_scope)
        if 'plt' in local_scope:
            st.pyplot(local_scope['plt'].gcf())  # Hiển thị biểu đồ đã vẽ
        else:
            st.error("Không tìm thấy đối tượng plt để hiển thị biểu đồ.")
    except Exception as e:
        st.error(f"Đã xảy ra lỗi khi thực thi mã: {e}")

def main():
    # Đọc dữ liệu từ file CSV
    file_path = "data/data_sample.xlsx"
    data = pd.read_excel(file_path)
    

    # Giao diện Streamlit
    st.title("Pyplot Chart Generator")

    with st.expander("Dữ liệu mẫu:"):
        st.dataframe(data)

    user_input = st.text_area("Enter your chart request:")

    columns = data.columns

    # Tạo một đối tượng OpenAIClient
    init_instruction = "You are an experience programmer, especially in data analysis and data visualize using Pyplot."
    assistant = OpenAIAssistant(model_name="gpt-4o-mini", init_instruction=init_instruction)
    assistant_msg = "Analyse user request, choose the best chart type and generate Python code to plot the chart."
    assistant.add_message('assistant', assistant_msg)

    if st.button("Generate Chart"):
        if user_input:
            # Tạo prompt cho API của OpenAI
            prompt = f'Create a Python code to plot a chart using Pyplot for the following request: "{user_input}". Given data columns: {columns}. Data is stored in a DataFrame named "data" so do not create sample data, just assume data is there.'
            try:
                # Gửi yêu cầu tới API và lấy mã nguồn, kiểu biểu đồ
                response = assistant.answer(prompt)
                print('Response:', response)
                code = response.split('```python')[1].split('```')[0].strip()
                print('Code:', code)
                # Thực thi mã
                execute_code(code, data)
            except Exception as e:
                st.error(f"Đã xảy ra lỗi khi thực thi mã: {e}")
        else:
            st.warning("Vui lòng nhập yêu cầu.")

if __name__ == "__main__":
    main()

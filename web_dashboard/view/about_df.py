import streamlit as st
import pandas as pd

def main():
    st.title("Tổng quan dữ liệu mẫu")    

    file_path = "data/data_sample.xlsx"
    data = pd.read_excel(file_path)

    st.write(
        """
        Dưới đây là bảng dữ liệu chứa thông tin về sinh viên và các yếu tố liên quan đến công việc và ngành học của họ.
        Bạn có thể tham khảo và tìm hiểu thêm về các cột dữ liệu trong bảng.
        """
    )

    with st.expander("Dữ liệu mẫu:"):
        st.dataframe(data)

    st.subheader("Mô tả các cột trong dữ liệu:")
    st.write(
        """
        - **Chương trình**: Chuyên ngành học của sinh viên.
        - **Đợt tốt nghiệp**: Đợt tốt nghiệp của sinh viên.
        - **Việc đang làm có liên quan tới ngành học không?**: Thông tin về việc làm có liên quan đến ngành học hay không.
        - **Khoảng lương hiện tại**: Mức lương hiện tại của sinh viên (theo các khoảng giá trị).
        - **Vị trí công việc**: Vị trí công việc hiện tại của sinh viên.
        - **Anh chị đã chuyển việc mấy lần?**: Số lần chuyển công việc của sinh viên.
        - **Trong lúc còn đang học, anh chị có việc làm thêm không?**: Câu trả lời có hay không về việc làm thêm trong khi còn học.
        - **Công việc đó có liên quan tới ngành học không?**: Liên quan giữa công việc làm thêm và ngành học của sinh viên.
        """
    )

    # Hiển thị các giá trị duy nhất của các cột trong DataFrame
    # st.subheader("Các giá trị của các cột:")
    
    # unique_values = {}
    # for column in data.columns:
    #     unique_values[column] = list(data[column].unique())

    # # Trình bày dưới dạng bảng đẹp mắt với markdown
    # for column, values in unique_values.items():
    #     st.markdown(f"### {column}:")        
    #     st.markdown(f"<ul>{''.join([f'<li>{value}</li>' for value in values])}</ul>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()

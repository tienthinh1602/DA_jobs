import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from openai import OpenAI  

def get_key():
        with open('view\key.txt') as f:
            return f.read().strip()
        
client = OpenAI(api_key=get_key())

def get_analysis_from_ai(text_prompt):
    chart_descriptions = """
        Hãy phân tích:
        1. Các đánh giá chung từ biểu đồ thông qua dữ liệu.
        2. Các điểm đáng lưu ý từ số liệu đặc biệt.       
        3. Các để xuất giải pháp để giúp cải thiện tốt hơn trong tương lai.

        Lưu ý: 
        - Sử dụng các con số chính xác từ dữ liệu để cho vào phân tích
        - Diễn giải số liệu một cách rõ ràng, dễ hiểu
        - Tập trung vào các xu hướng và mối tương quan"""
    
    full_prompt = chart_descriptions + "\n\n" + text_prompt    
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo-0125",
            messages=[
                {"role": "system", "content": "You are an experienced visualized chart analyst."},
                {"role": "user", "content": full_prompt}
            ],
            max_tokens=1000
        )
        analysis = response.choices[0].message.content
        return analysis
    except Exception as e:
        st.error(f"Error in AI analysis: {str(e)}")
        return None

def convert_salary_range_to_midpoint(salary_range):
        if salary_range == "0-5":
            return 2.5
        elif salary_range == "5-10":
            return 7.5
        elif salary_range == "10-20":
            return 15
        elif salary_range == "20-30":
            return 25
        elif salary_range == "30-40":
            return 35
        elif salary_range == "40-100":
            return 45
        else:
            return None

def add_column(df):
    df['Đi làm khi còn đi học'] = df.apply(
        lambda row: 'Có liên quan' if row['Trong lúc còn đang học, anh chị có việc làm thêm không?'] == 'Có' and row['Công việc đó có liên quan tới ngành học không?'] == 'Có'
        else 'Không liên quan' if row['Trong lúc còn đang học, anh chị có việc làm thêm không?'] == 'Có' and row['Công việc đó có liên quan tới ngành học không?'] == 'Không'
        else 'Không đi làm thêm' if row['Trong lúc còn đang học, anh chị có việc làm thêm không?'] == 'Không'
        else 'Thông tin không rõ', axis=1
    )
    df['Lương hiện tại (midpoint)'] = df['Khoảng lương hiện tại'].apply(convert_salary_range_to_midpoint)
    df['Lương đầu tiên (midpoint)'] = df['Khoảng lương của công việc đầu tiên'].apply(convert_salary_range_to_midpoint)
    df['Lương có cải thiện không?'] = df['Lương hiện tại (midpoint)'] > df['Lương đầu tiên (midpoint)']
    df['Lương có cải thiện không?'] = df['Lương có cải thiện không?'].replace({True: 'Có', False: 'Không'})

def plot_job_change_average(department_name, df):
        department_df = df[df['Chương trình'] == department_name]       
        average_job_changes = department_df['Anh chị đã chuyển việc mấy lần?'].mean()
        st.metric(
            label=f"Chuyên ngành {department_name}",
            value=f"{average_job_changes:.1f} lần" if not pd.isna(average_job_changes) else "N/A",
        )    

def plot_gauge(department_name, df):
    total_students = len(df[df['Chương trình'] == department_name])
    related_students = len(df[(df['Chương trình'] == department_name) & 
                            (df['Lương có cải thiện không?'] == 'Có')])
    percentage = (related_students / total_students) * 100 if total_students > 0 else 0        
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=percentage,
        number={'suffix': "%"},  
        gauge={
            'axis': {'range': [0, 100], 'showticklabels': False},  
            'bar': {'color': "#66b3ff"},  
            'bgcolor': "#f2f2f2",  
            'shape': "angular",
            'steps': [
                {'range': [0, percentage], 'color': "#66b3ff"},
                {'range': [percentage, 100], 'color': "#f2f2f2"}
            ],
            'threshold': {'thickness': 1, 'value': percentage},
        },            
    ))
    fig.update_layout(            
        margin={'t': 0, 'b': 0, 'l': 0, 'r': 0},
        height=80,
        width=100,
    )        
    fig.update_traces(gauge_shape="angular")  
    st.plotly_chart(fig)

def filter_data(df):
    fil_1, fil_2 = st.columns(2)
    with fil_1:
        selected_programs = st.sidebar.multiselect("Ngành học", options=df['Chương trình'].unique(),
                                                   default=df['Chương trình'].unique())
    with fil_2:
        selected_graduation_period = st.sidebar.multiselect("Đợt tốt nghiệp", options=df['Đợt tốt nghiệp'].unique(),
                                                            default=df['Đợt tốt nghiệp'].unique())
    return df[(df['Chương trình'].isin(selected_programs)) & (df['Đợt tốt nghiệp'].isin(selected_graduation_period))]


def improve_salary_bar(df):
    # df = df[~df['Anh chị đã chuyển việc mấy lần?'].isin([0, 5, 6, 8])]    
    df = df[~df['Anh chị đã chuyển việc mấy lần?'].isin([0])]    
    grouped = df.groupby(['Anh chị đã chuyển việc mấy lần?', 'Lương có cải thiện không?']).size().reset_index(name='Số lượng')
    total_counts = grouped.groupby('Anh chị đã chuyển việc mấy lần?')['Số lượng'].transform('sum')
    grouped['Tỉ lệ (%)'] = grouped['Số lượng'] / total_counts * 100

    st.session_state.salary_improvement_data = grouped.to_dict('records')

    fig = px.bar(
        grouped,
        x='Tỉ lệ (%)',
        color='Lương có cải thiện không?',
        y='Anh chị đã chuyển việc mấy lần?',
        orientation='h',
        title="Tỉ lệ cải thiện lương theo số lần chuyển việc",
        labels={'Tỉ lệ (%)': 'Tỉ lệ (%)', 'Lương có cải thiện không?': 'Lương có cải thiện'},
        color_discrete_sequence=['#66b3ff', '#ff9999'],  
        text='Tỉ lệ (%)',  
        category_orders={"Lương có cải thiện không?": ['Có', 'Không']}
    )
    fig.update_layout(
        barmode='stack',
        xaxis={'tickformat': '.1f'},              
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1,
            xanchor="center",
            x=0.5
        )
    )        
    fig.update_traces(
        texttemplate='%{text:.1f}%', 
        textposition='inside'
    )
    st.plotly_chart(fig)  

def improve_salary_pie(df): 
    salary_improvement_counts = df['Lương có cải thiện không?'].value_counts().reset_index()
    salary_improvement_counts.columns = ['Lương có cải thiện không?', 'Số lượng']
    fig2 = px.pie(
        salary_improvement_counts,
        names='Lương có cải thiện không?',
        values='Số lượng',
        title="Tỉ lệ cải thiện lương tất cả các ngành",
        color_discrete_sequence=['#66b3ff', '#ff9999'],
        hole=0.5
    )
    fig2.update_layout(height=400)
    st.plotly_chart(fig2)

def part_time_job(df):  
    # df = df[~df['Anh chị đã chuyển việc mấy lần?'].isin([5, 6, 8])]
    df = df[(df['Đi làm khi còn đi học'] != 'Thông tin không rõ') & (df['Đi làm khi còn đi học'] != 'Không đi làm thêm')] 
    grouped = df.groupby(['Anh chị đã chuyển việc mấy lần?', 'Đi làm khi còn đi học']).size().reset_index(name='Số lượng')
    total_counts = grouped.groupby('Anh chị đã chuyển việc mấy lần?')['Số lượng'].transform('sum')
    grouped['Tỉ lệ (%)'] = grouped['Số lượng'] / total_counts * 100    

    data_for_analysis = grouped.to_dict('records')
    st.session_state.part_time_job_data = data_for_analysis

    fig = px.bar(
    grouped,
    x='Tỉ lệ (%)',
    y='Anh chị đã chuyển việc mấy lần?',
    color='Đi làm khi còn đi học',
    orientation='h',
    title="Tỉ lệ đi làm khi còn đi học theo số lần chuyển việc",
    labels={'Tỉ lệ (%)': 'Tỉ lệ (%)', 'Anh chị đã chuyển việc mấy lần?': 'Số lần chuyển việc'},
    color_discrete_sequence=['#66b3ff', '#ff9999'],  
    text='Tỉ lệ (%)', 
    category_orders={"Đi làm khi còn đi học": ['Có liên quan', 'Không liên quan']}
)

    fig.update_layout(
        barmode='stack',
        xaxis={'tickformat': '.1f'},         
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1,
            xanchor="center",
            x=0.5
        )
    )
    fig.update_traces(
        texttemplate='%{text:.1f}%',  
        textposition='inside'
    )

    st.plotly_chart(fig)

def average_salary(df):
    # df = df[~df['Khoảng lương hiện tại'].isin(['0-5'])]   
    job_changes_avg = df.groupby('Khoảng lương hiện tại')['Anh chị đã chuyển việc mấy lần?'].mean().reset_index()

    data_for_analysis = job_changes_avg.to_dict('records')
    st.session_state.average_salary_data = data_for_analysis
    
    fig = px.bar(    
        job_changes_avg,
        x='Khoảng lương hiện tại',
        y='Anh chị đã chuyển việc mấy lần?',
        title="Trung bình số lần chuyển việc theo khoảng lương",
        labels={'Anh chị đã chuyển việc mấy lần?': 'Trung bình số lần chuyển việc'},
        color='Khoảng lương hiện tại', 
        text='Anh chị đã chuyển việc mấy lần?',  
        # category_orders={"Khoảng lương hiện tại": ['0-5', '5-10', '10-20', '20-30', '30-40', '40-100']}
        )
    fig.update_layout(            
        showlegend=False,
        xaxis_title="Khoảng lương hiện tại",
        yaxis_title="Trung bình số lần chuyển việc",
        xaxis={'tickangle': 45}  
    )
    fig.update_traces(
        texttemplate='%{text:.1f}',textposition='inside'
    )
    st.plotly_chart(fig)

def show_analysis(text):
    if text == "Tỉ lệ đi làm khi còn đi học theo số lần chuyển việc":
        data = st.session_state.get('part_time_job_data', [])
    elif text == "Tỉ lệ cải thiện lương theo số lần chuyển việc":
        data = st.session_state.get('salary_improvement_data', [])
    elif text == "Trung bình số lần chuyển việc theo khoảng lương":
        data = st.session_state.get('average_salary_data', [])
    elif text == "Trung bình khoảng lương sau tốt nghiệp":
        data = st.session_state.get('salary_change_by_graduation', [])
    else:
        data = []

    data_str = "\nDữ liệu chi tiết: " + "\n".join([f"- {str(item)}" for item in data])
    
    analysis_prompt = f"Phân tích chi tiết biểu đồ về {text}. {data_str}"
    
    analysis = get_analysis_from_ai(analysis_prompt)
    if analysis:
        st.write("Phân tích từ AI cho biểu đồ")
        st.write(analysis)
    else:
        st.write("Không thể lấy phân tích từ AI.")

def salary_change_by_graduation(df): 
    if df.empty:
        st.warning("Không có dữ liệu để hiển thị. Vui lòng điều chỉnh bộ lọc.")
        return
    df = df[~df['Lương đầu tiên (midpoint)'].isin([25, 45])]   
    df['Graduation Date'] = pd.to_datetime(df['Đợt tốt nghiệp'], format='%Y-%m')    
    current_date = pd.to_datetime('2025-01-01')
    df['Years After Graduation'] = ((current_date - df['Graduation Date']) / pd.Timedelta(days=365)).apply(lambda x: f'{int(x)} năm')
    salary_by_years = df.groupby('Years After Graduation').agg({
        'Lương hiện tại (midpoint)': 'mean',
        'Lương đầu tiên (midpoint)': 'mean'
    }).reset_index()
    
    salary_by_years['Sort Order'] = salary_by_years['Years After Graduation'].str.extract('(\d+)').astype(float)
    salary_by_years = salary_by_years.sort_values('Sort Order')

    st.session_state.salary_graduation_data = salary_by_years.to_dict('records')
    
    fig = go.Figure()   
    fig.add_trace(go.Scatter(
        x=salary_by_years['Years After Graduation'],
        y=salary_by_years['Lương hiện tại (midpoint)'],
        mode='lines',
        name='Lương hiện tại',
        line=dict(color='#66b3ff', width=3),
        marker=dict(size=10)
    ))

    fig.add_trace(go.Scatter(
        x=salary_by_years['Years After Graduation'],
        y=salary_by_years['Lương đầu tiên (midpoint)'],
        mode='lines',
        name='Lương đầu tiên',
        line=dict(color='#ff9999', width=3),
        marker=dict(size=10)
    ))

    fig.update_layout(
        title='Trung bình lương theo số năm sau tốt nghiệp',
        xaxis_title='Số năm sau tốt nghiệp',
        yaxis_title='Trung bình lương (triệu VNĐ)',
        yaxis=dict(rangemode='tozero'),
        legend=dict(
            orientation="h", 
            yanchor="bottom",  
            y=1.02,  
            xanchor="center",  
            x=0.5
        )
    )
    st.plotly_chart(fig)


def main():
    data_path = 'data/data_sample.xlsx'
    df = pd.read_excel(data_path)   
    add_column(df)
    df_copy = df.copy()
    df_filter = filter_data(df)
        
    top_left_column, top_right_column = st.columns((2, 1))
    center_left_column, center_right_column = st.columns(2)
    bottom_left_column, bottom_right_column = st.columns(2)

    with top_left_column:
        st.title("Trung bình số lần chuyển việc theo ngành học")   
        departments = ["IT", "Business", "Design"]
        cols = st.columns(3)
        for i, department in enumerate(departments):
            with cols[i]:
                plot_job_change_average(department, df_copy)  
                plot_gauge(department, df_copy)
                st.write('Tỉ lệ lương được cải thiện')
                
    with top_right_column:
        improve_salary_pie(df_copy)   

    with center_left_column:
        part_time_job(df_filter)
        if st.button("Xem phân tích từ việc đi làm khi còn đi học"):
            show_analysis("Tỉ lệ đi làm khi còn đi học theo số lần chuyển việc")
    with center_right_column:
        improve_salary_bar(df_filter)
        if st.button("Xem phân tích mức độ cải thiện lương qua chuyển việc"):
            show_analysis("Tỉ lệ cải thiện lương theo số lần chuyển việc")
    with bottom_left_column:
        average_salary(df_filter)
        if st.button("Xem phân tích khoảng lương qua số lần chuyển việc"):
            show_analysis("Trung bình số lần chuyển việc theo khoảng lương")
    with bottom_right_column:
        salary_change_by_graduation(df_filter)
        if st.button("Xem phân tích khoảng lương sau tốt nghiệp"):
            show_analysis("Trung bình khoảng lương sau tốt nghiệp")

if __name__ == "__main__":
    main()
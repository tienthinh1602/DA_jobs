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

def filter_data(df):
    fil_1, fil_2, fil_3 = st.columns(3)
    with fil_1:
        selected_related = st.sidebar.multiselect(
            "Công việc đúng ngành học",
            options=df['Việc đang làm có liên quan tới ngành học không?'].dropna().unique(),
            default=df['Việc đang làm có liên quan tới ngành học không?'].dropna().unique()
        )
    with fil_2:
        selected_programs = st.sidebar.multiselect(
            "Ngành học",
            options=df['Chương trình'].unique(),
            default=df['Chương trình'].unique()
        )
    with fil_3:
        selected_graduation_period = st.sidebar.multiselect(
            "Đợt tốt nghiệp",
            options=df['Đợt tốt nghiệp'].unique(),
            default=df['Đợt tốt nghiệp'].unique()
        )

    return df[
        (df['Việc đang làm có liên quan tới ngành học không?'].isin(selected_related)) &
        (df['Chương trình'].isin(selected_programs)) &
        (df['Đợt tốt nghiệp'].isin(selected_graduation_period))
    ]

def add_column(df):
    df['Đi làm khi còn đi học'] = df.apply(
        lambda row: 'Có liên quan' if row['Trong lúc còn đang học, anh chị có việc làm thêm không?'] == 'Có' and row['Công việc đó có liên quan tới ngành học không?'] == 'Có'
        else 'Không liên quan' if row['Trong lúc còn đang học, anh chị có việc làm thêm không?'] == 'Có' and row['Công việc đó có liên quan tới ngành học không?'] == 'Không'
        else 'Không đi làm thêm' if row['Trong lúc còn đang học, anh chị có việc làm thêm không?'] == 'Không'
        else 'Thông tin không rõ', axis=1
    )

def plot_metric(department_name, df):

    total_students = len(df[df['Chương trình'] == department_name])
    related_students = len(df[(df['Chương trình'] == department_name) & 
                            (df['Việc đang làm có liên quan tới ngành học không?'] == 'Có')])
    st.metric(
        label=f"Chuyên ngành {department_name}",
        value=f"{related_students}/{total_students}",
        # delta=f"{(related_students / total_students) * 100:.1f}%" if total_students > 0 else "N/A"
    )

def plot_gauge(department_name, df):
    total_students = len(df[df['Chương trình'] == department_name])
    related_students = len(df[(df['Chương trình'] == department_name) & 
                            (df['Việc đang làm có liên quan tới ngành học không?'] == 'Có')])
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

def right_major_pie(df):
    related_counts = df['Việc đang làm có liên quan tới ngành học không?'].value_counts()
    fig1 = px.pie(
        names=related_counts.index,
        values=related_counts,
        title="Tỉ lệ việc làm liên quan tới ngành học",
        color_discrete_sequence=['#66b3ff', '#ff9999'],
        hole= 0.5
    )
    fig1.update_layout(height=350)
    st.plotly_chart(fig1)

def first_salary(df):
        # df = df[~df['Khoảng lương của công việc đầu tiên'].isin(['20-30', '40-100'])]
        grouped = df.groupby([
        'Khoảng lương của công việc đầu tiên', 
        'Việc đang làm có liên quan tới ngành học không?'
        ]).size().reset_index(name='Số lượng')
  
        st.session_state.first_salary_data = grouped.to_dict('records')

        fig = px.bar(
            df,
            x='Khoảng lương của công việc đầu tiên',
            color='Việc đang làm có liên quan tới ngành học không?',
            title='Khoảng lương công việc đầu tiên',
            color_discrete_sequence=['#66b3ff', '#ff9999'],
            barmode='group',
            category_orders={
                #  "Khoảng lương của công việc đầu tiên": ['0-5', '5-10', '10-20'],
                 "Việc đang làm có liên quan tới ngành học không?": ['Có', 'Không']}
        )
        fig.update_layout( 
            yaxis_title="Số lượng sinh viên",
            legend=dict(
            orientation="h", 
            yanchor="bottom",  
            y=1,  
            xanchor="center",  
            x=0.5))
        st.plotly_chart(fig)

def part_time_job(df):
        df= df[df['Đi làm khi còn đi học'] != 'Thông tin không rõ']
        grouped = df.groupby(['Việc đang làm có liên quan tới ngành học không?', 'Đi làm khi còn đi học']).size().reset_index(name='Số lượng')
        total_counts = grouped.groupby('Việc đang làm có liên quan tới ngành học không?')['Số lượng'].transform('sum')
        grouped['Tỉ lệ (%)'] = (grouped['Số lượng'] / total_counts) * 100

        data_for_analysis = grouped.to_dict('records')
        st.session_state.part_time_job = data_for_analysis

        fig = px.bar(
            grouped,
            x='Tỉ lệ (%)',
            y='Việc đang làm có liên quan tới ngành học không?',            
            color='Đi làm khi còn đi học',
            title="Tỉ lệ đi làm khi còn đi học và làm việc đúng ngành",
            labels={'Tỉ lệ (%)': 'Tỉ lệ (%)', 'Việc đang làm có liên quan tới ngành học không?': 'Làm việc đúng ngành'},
            color_discrete_sequence=['#66b3ff', '#ff9999', '#ffcc99'],  
            text='Tỉ lệ (%)',  
            category_orders={"Việc đang làm có liên quan tới ngành học không?": ['Có', 'Không']})
            

        fig.update_layout(
            barmode='stack', 
            xaxis={'tickformat': '.0f'}, 
            height=300,
            title_y=0.87,
            margin={'t': 200, 'b': 0, 'l': 0, 'r': 0},            
            legend=dict(
            orientation="h",  
            yanchor="bottom", 
            y=1.3,      
        )           
        )
        fig.update_traces(
        texttemplate='%{text:.0f}%', 
        textposition='inside', 
    )
        st.plotly_chart(fig)

def job_position(df):
        position_counts = df['Vị trí công việc'].value_counts().reset_index()
        position_counts.columns = ['Vị trí công việc', 'Số lượng']
        st.session_state.job_position = position_counts.to_dict('records')
        fig = px.treemap(
            position_counts, 
            path=['Vị trí công việc'],  
            values='Số lượng',  
            title="Phân bố các vị trí công việc",
            color='Số lượng',  
            color_continuous_scale='Blues' 
        )             
        st.plotly_chart(fig)

def current_salary(df):    
        # df = df[~df['Khoảng lương của công việc đầu tiên'].isin(['0-5'])]
        salary_data = df.groupby(['Khoảng lương hiện tại', 'Việc đang làm có liên quan tới ngành học không?']).size().reset_index(name='Số lượng')
        st.session_state.current_salary = salary_data.to_dict('records')
        fig = px.bar(
            df,
            x='Khoảng lương hiện tại',
            color='Việc đang làm có liên quan tới ngành học không?',
            title='Khoảng lương hiện tại',
            color_discrete_sequence=['#66b3ff', '#ff9999'],
            barmode='group',
            # category_orders={"Khoảng lương hiện tại": ['0-5', '5-10', '10-20', '20-30', '30-40', '40-100']}
        )
        fig.update_layout( 
            yaxis_title="Số lượng sinh viên",
            legend=dict(
            orientation="h", 
            yanchor="bottom",  
            y=1,  
            xanchor="center",  
            x=0.5))
        st.plotly_chart(fig)

def graduation_time(df):
    pivot_table = pd.crosstab(
        df['Đợt tốt nghiệp'],
        df['Việc đang làm có liên quan tới ngành học không?'],
        normalize='index'
    ).reindex(columns=['Có', 'Không'], fill_value=0)  

    pivot_table_percent = pivot_table * 100

    st.session_state.graduation_time = {
        'pivot_table': pivot_table_percent.to_dict(),
        'details': [
            {
                'Đợt tốt nghiệp': index, 
                'Có (%)': f"{pivot_table_percent.loc[index, 'Có']:.1f}", 
                'Không (%)': f"{pivot_table_percent.loc[index, 'Không']:.1f}"
            } 
            for index in pivot_table_percent.index
        ]
    }

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=pivot_table.index, y=pivot_table['Có'], mode='lines', name='Có',
        stackgroup='one', fill='tonexty', line=dict(color='#66b3ff')
    ))
    fig.add_trace(go.Scatter(
        x=pivot_table.index, y=pivot_table['Không'], mode='lines', name='Không',
        stackgroup='one', fill='tonexty', line=dict(color='#ff9999')
    ))
    
    fig.update_layout(
        title='Tỉ lệ làm việc đúng ngành theo đợt tốt nghiệp',
        legend=dict(
            orientation="h", 
            yanchor="bottom",  
            y=1,  
            xanchor="center",  
            x=0.5
        )
    )
    st.plotly_chart(fig)

def show_analysis(text):
    if text == "khoảng lương đầu tiên":
        data = st.session_state.get('first_salary', [])
    elif text == "khoảng lương hiện tại":
        data = st.session_state.get('current_salary', [])
    elif text == "làm việc khi còn đi học":
        data = st.session_state.get('part_time_job', [])
    elif text == "tỉ lệ làm đúng ngành theo thời gian":
        data = st.session_state.get('graduation_time', {}).get('details', [])
    elif text == "phân bố vị trí công việc":
        data = st.session_state.get('job_position', [])
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



def main():    
    data_path = 'data/data_sample.xlsx'
    df = pd.read_excel(data_path)
    add_column(df)
    df_copy = df.copy()
    df_filter = filter_data(df)    

    top_left_column, top_right_column = st.columns((2, 1))    
    center_left_column, center_right_column, center_mid_column = st.columns(3)
    bottom_left_column, bottom_right_column = st.columns(2)

    with top_left_column:
        st.title("Sinh viên làm việc đúng ngành học")
        departments = ["IT", "Business", "Design"]
        cols = st.columns(3)        
        for i, department in enumerate(departments):
            with cols[i]:
                plot_metric(department, df_copy)
                plot_gauge(department, df_copy)
                st.write('Tỉ lệ làm việc đúng ngành')

    with top_right_column:
        right_major_pie(df_copy)

    with center_left_column:
        first_salary(df_filter)
        if st.button("Xem phân tích khoảng lương đầu tiên"):
            show_analysis("khoảng lương đầu tiên")

    with center_right_column:
        current_salary(df_filter)
        if st.button("Xem phân tích khảng lương hiện tại"):
            show_analysis("khoảng lương hiện tại")

    with center_mid_column:
        part_time_job(df_filter)
        st.markdown('<div class="padding-top"></div>', unsafe_allow_html=True)
        if st.button("Xem phân tích làm việc khi còn đi học"):
            show_analysis("làm việc khi còn đi học")

    with bottom_left_column:
        graduation_time(df_filter)
        if st.button("Xem phân tích tỉ lệ làm đúng ngành theo thời gian"):
            show_analysis("tỉ lệ làm đúng ngành theo thời gian")

    with bottom_right_column:
        job_position(df_filter)
        if st.button("Xem phân tích cho phân bố vị trí công việc"):
            show_analysis("phân bố vị trí công việc")

    
if __name__ == "__main__":
    main()

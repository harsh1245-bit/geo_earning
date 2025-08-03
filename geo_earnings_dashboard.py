# Flask-based Local Web Dashboard (No Streamlit)
from flask import Flask, render_template, request, send_file
import pandas as pd
import random
import plotly.express as px
import plotly.io as pio
import os

app = Flask(__name__)

# Generate Dummy Data
random.seed(42)
geo_codes = ['G1', 'G2', 'G3', 'G4', 'G5']
parent_geo_codes = {'G1': 'P1', 'G2': 'P1', 'G3': 'P2', 'G4': 'P2', 'G5': 'P3'}
parent_of_parent_geo_codes = {'P1': 'PP1', 'P2': 'PP1', 'P3': 'PP2'}
align_codes = ['ASR2', 'ASC1', 'SSL2']

data = []
for i in range(30):
    geo = random.choice(geo_codes)
    parent_geo = parent_geo_codes[geo]
    parent_of_parent_geo = parent_of_parent_geo_codes[parent_geo]
    align_code = random.choice(align_codes)
    employee_name = f"Employee_{i}"
    how_earning = random.randint(10, 100)
    what_earning = random.randint(5, 50)
    total_earning = how_earning + what_earning
    data.append([align_code, geo, parent_geo, parent_of_parent_geo,
                 employee_name, how_earning, what_earning, total_earning])

columns = ['Align code', 'geo code', 'parent geo code', 'parent of parent geo code',
           'employee name', 'how earning', 'what earning', 'total earning']
df = pd.DataFrame(data, columns=columns)

@app.route('/')
def dashboard():
    align_filter = request.args.getlist('align') or df['Align code'].unique().tolist()
    geo_filter = request.args.getlist('geo') or df['geo code'].unique().tolist()
    emp_filter = request.args.getlist('employee') or df['employee name'].unique().tolist()

    filtered_df = df[df['Align code'].isin(align_filter) &
                     df['geo code'].isin(geo_filter) &
                     df['employee name'].isin(emp_filter)]

    # KPIs
    total_earnings = int(filtered_df['total earning'].sum())
    avg_earnings = round(filtered_df.groupby('employee name')['total earning'].sum().mean(), 2)
    unique_employees = filtered_df['employee name'].nunique()

    # Charts
    geo_summary = filtered_df.groupby(['parent of parent geo code', 'parent geo code', 'geo code'])['total earning'].sum().reset_index()
    fig_geo = px.sunburst(geo_summary, path=['parent of parent geo code', 'parent geo code', 'geo code'], values='total earning')
    geo_chart = pio.to_html(fig_geo, full_html=False)

    align_summary = filtered_df.groupby('Align code')['total earning'].sum().reset_index()
    fig_align = px.bar(align_summary, x='Align code', y='total earning')
    align_chart = pio.to_html(fig_align, full_html=False)

    top_employees = filtered_df.groupby('employee name')['total earning'].sum().reset_index().sort_values(by='total earning', ascending=False).head(10)
    fig_top = px.bar(top_employees, x='employee name', y='total earning')
    top_chart = pio.to_html(fig_top, full_html=False)

    return render_template('dashboard.html',
                           total_earnings=total_earnings,
                           avg_earnings=avg_earnings,
                           unique_employees=unique_employees,
                           align_codes=df['Align code'].unique(),
                           geo_codes=df['geo code'].unique(),
                           employee_names=df['employee name'].unique(),
                           selected_align=align_filter,
                           selected_geo=geo_filter,
                           selected_emp=emp_filter,
                           geo_chart=geo_chart,
                           align_chart=align_chart,
                           top_chart=top_chart)

@app.route('/download')
def download():
    filtered = df.copy()
    path = "filtered_earnings.csv"
    filtered.to_csv(path, index=False)
    return send_file(path, as_attachment=True)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))  # use Render's port if available
    app.run(host='0.0.0.0', port=port)

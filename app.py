from flask import Flask, render_template, url_for, request, Response
import pandas as pd
from datetime import timezone, datetime, timedelta
import json
import plotly
import numpy as np
import plotly.express as px
import os

app = Flask(__name__)
dir_path = os.path.dirname(__file__)

# datetime setting
local_tz = timezone(timedelta(hours=+8))


def get_data():
    target = ['石門水庫', '新山水庫', '翡翠水庫', '寶山第二水庫', '永和山水庫', '明德水庫',
              '鯉魚潭水庫', '湖山水庫', '仁義潭水庫', '白河水庫', '烏山頭水庫', '曾文水庫',
              '南化水庫', '阿公店水庫', '牡丹水庫', '德基水庫', '霧社水庫', '日月潭水庫',
              '石岡壩', '高屏溪攔河堰']
    data = []

    for y in range(2019, 2022):
        year_data = pd.read_csv(dir_path + '/data/reservoir_{}.csv'.format(y))
        year_data = year_data[year_data['ReservoirName'].isin(target)]
        data.append(year_data)

    df = pd.concat(data)
    df = df[~df['EffectiveWaterStorageCapacity'].isnull()]
    df = df.reset_index().drop('index', axis=1)
    df = df.sort_values('RecordTime')
    df['RecordTime'] = pd.to_datetime(df['RecordTime'], format='%Y-%m-%d')
    df['Year'] = df['RecordTime'].apply(lambda x: str(x.date().strftime('%Y')))
    return df


def data_cleaning(dataframe):
    # reduce the noise on the data
    df_clean = dataframe
    df_clean.loc[(~np.isfinite(df_clean['WaterStorageRate']))] = np.nan
    df_clean.loc[df_clean['WaterStorageRate'] > 1, 'WaterStorageRate'] = 1
    df_clean.loc[df_clean['WaterStorageRate'] > 1.5, 'WaterStorageRate'] = np.nan
    df_clean = df_clean[~df_clean['WaterStorageRate'].isnull()]
    df_clean['date'] = df_clean['RecordTime'].apply(lambda x: x.date().strftime('%m-%d'))
    df_clean['date'] = pd.to_datetime(df_clean['date'], format='%m-%d', errors='coerce')

    return df_clean


def reservoir_by_name(raw_data, reservoir_name):
    # filtering and formatting the data
    df_name = raw_data[raw_data['ReservoirName'] == reservoir_name]
    df_name['WaterStorageRate'] = df_name['WaterStorageRate'] / 100
    df_name['WaterStorageRate'] = df_name['WaterStorageRate'].where(df_name['WaterStorageRate'].isnull(),
                                                                    df_name['EffectiveWaterStorageCapacity'] /
                                                                    df_name['EffectiveCapacity'])
    df_name = data_cleaning(df_name)

    return df_name


def get_plotly_json(graph_data, x_axis='date', y_axis='WaterStorageRate'):
    # last date
    last_date = graph_data['RecordTime'].to_list()[-1].date().strftime('%Y')

    # make plot
    fig = px.line(graph_data, x=x_axis, y=y_axis,
                  color='Year', template='simple_white',
                  color_discrete_sequence=px.colors.qualitative.Pastel)

    # formatting x, y ticks
    fig.update_traces(hovertemplate='日期: %{x|%m-%d}<br>蓄水率: %{y}', )

    # highlight latest data
    fig.update_traces(patch={'line': {'width': 3}},
                      selector={'legendgroup': '2021'},
                      secondary_y=False)

    # add text annotation
    fig.add_scatter(x=[fig.data[-1].x[-1]], y=[fig.data[-1].y[-1]],
                    mode='markers + text',
                    marker={'color': 'rgba(250, 250, 250, 0)', 'size': 2},
                    showlegend=False,
                    text=last_date,
                    textposition='top center',
                    hovertemplate='',
                    hoverinfo='skip')

    # background setting
    fig.update_layout(
        title='',
        plot_bgcolor='rgb(250, 250, 250)',
        paper_bgcolor='rgb(250, 250, 250)',
        yaxis_tickformat='%',
        yaxis_range=[0, 1.02],
        xaxis_tickformat='%m',
        yaxis_title='蓄水率',
        xaxis_title='月份',
        margin=dict(t=10, l=10, b=10, r=10),
        legend=dict(
            orientation='h',
            y=1.1,
        )
    )

    graph_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    return graph_json


@app.route('/')
def hello_world():
    return 'Hello World!'


@app.route('/sample_data')
def sample_data():
    # return a simple list of dictionaries
    sample_dict = [{'user': 'A', 'id': '1'},
                   {'user': 'B', 'id': '2'}]

    response = Response(json.dumps(sample_dict), mimetype='application/json')

    return response


@app.route('/sample_reservoir_data')
def sample_reservoir_data():
    # converting dataframe to json
    reservoir_data_latest = pd.read_csv(dir_path + '/data/history_data/reservoir_20211209.csv')
    response_data = reservoir_data_latest.to_json(orient='records')

    # return JSON format data
    response = Response(response_data, mimetype='application/json')

    return response


@app.route('/sample_reservoir_plot')
def sample_reservoir_plot():
    reservoir_data = get_data()
    reservoirs = reservoir_data['ReservoirName'].unique()

    # prepare data for plotting
    if not reservoir_data.empty:
        reservoir_each = reservoir_by_name(reservoir_data, reservoirs[0])
        reservoir_graph_json = get_plotly_json(reservoir_each)

        latest_value = reservoir_each.iloc[-1:, :]
        meta_info = (reservoirs[0],
                     '{:.2f}'.format(latest_value['WaterStorageRate'].item() * 100),
                     latest_value['RecordTime'].item().date().strftime('%Y-%m-%d'))

        # pass data to HTML page
        return render_template('sample_graphic.html',
                               meta_title='DSSI Demo',
                               reservoir_graph_json=reservoir_graph_json,
                               meta_info=meta_info)

    else:
        return 'None'


if __name__ == '__main__':
    app.run()


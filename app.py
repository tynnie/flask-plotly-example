from flask import Flask, render_template, url_for, Response
from model import get_data, reservoir_by_name
import pandas as pd
from datetime import timezone, datetime, timedelta
import json
import plotly
import plotly.express as px
import os

app = Flask(__name__)
dir_path = os.path.dirname(__file__)

# datetime setting
local_tz = timezone(timedelta(hours=+8))


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


@app.route('/sample_template')
def sample_template():
    time_now = datetime.now().strftime('%H%M')
    name = 'Ting Ni'

    return render_template('index.html',
                    time_now=time_now,
                    name=name)


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
    # for development use debug=True
    app.run(debug=True)

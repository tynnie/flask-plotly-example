import pandas as pd
from datetime import timezone, datetime, timedelta
import numpy as np
import os

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


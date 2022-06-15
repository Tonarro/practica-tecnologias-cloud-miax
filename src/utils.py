import requests
from bs4 import BeautifulSoup
import pandas as pd
import locale
from datetime import datetime
import mibian
import boto3
from boto3.dynamodb.conditions import Key

locale.setlocale(locale.LC_ALL, 'es_ES.UTF-8')


def get_data():
    response = requests.get('https://www.meff.es/esp/Derivados-Financieros/Ficha/FIEM_MiniIbex_35')

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        if soup is not None:
            future = soup.find('table', {'id': 'Contenido_Contenido_tblFuturos'})
            df_future = pd.read_html(str(future), decimal=',', thousands='.')[0]
            df_future.columns = df_future.columns.get_level_values(0)
            df_future = df_future.iloc[:-1, [0, -1]]
            df_future.index = [i.replace('.', '') for i in df_future.iloc[:, 0].values.tolist()]
            df_future = df_future.iloc[:, 1]
            df_future.index = pd.to_datetime(df_future.index, format='%d %b %Y')
            df_future.name = 'price'


            option = soup.find('table', {'id': 'tblOpciones'})
            indexes = option.find_all('tbody')[0].find_all('tr')[:-2]
            indexes = [i.attrs['data-tipo'] for i in indexes]

            df_option = pd.read_html(str(option), decimal=',', thousands='.')[0]
            df_option.columns = df_option.columns.get_level_values(0)
            list_option = df_option.iloc[:-2, [0, -1]].values[:].tolist()

            df_option = pd.DataFrame([[ind[1:2], ind[2:3], datetime.strptime(ind[3:], '%Y%m%d'), float(opt[0]), float(opt[1])] for ind, opt in zip(indexes, list_option) if opt[1] != '-'], columns=['call_put', 'type', 'date', 'strike', 'price'])
            df_option.index = df_option.iloc[:, 2].values
            df_option = df_option.iloc[:, [0, 1, 3, 4]]
            df_option = df_option[df_option.type == 'E']

            return df_future, df_option


def implied_volatility(df_option, future_price):
    """
    Calculate implied volatility for a given future price, strike, expiry and price.
    """
    if df_option.call_put == 'C':
        c = mibian.BS([future_price, df_option.strike, 0, (df_option.name-datetime.today()).days], callPrice=df_option.price)
        return c.impliedVolatility
    elif df_option.call_put == 'P':
        p = mibian.BS([future_price, df_option.strike, 0, (df_option.name-datetime.today()).days], putPrice=df_option.price)
        return p.impliedVolatility


def scan_dynamodb(table_name):
    dynamodb = boto3.resource('dynamodb', aws_access_key_id="AKIAY6FUYBZMK6AQQSER", aws_secret_access_key="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", region_name="eu-west-3",)
    table = dynamodb.Table(table_name)
    response = table.scan()
    if response['ResponseMetadata']['HTTPStatusCode'] == 200:
        return response['Count'], response['Items']
    else:
        return 0, []


def read_data_dynamodb(table_name, key_name, key_value):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(table_name)
    response = table.query(
        KeyConditionExpression=Key(key_name).eq(key_value)
    )
    print(response['Items'])
    df = pd.DataFrame(response['Items'])
    return df


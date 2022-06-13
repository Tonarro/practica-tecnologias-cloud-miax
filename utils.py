import requests
from bs4 import BeautifulSoup
import pandas as pd
import locale
from datetime import datetime

locale.setlocale(locale.LC_ALL, 'esp_esp')


def get_data():
    response = requests.get('https://www.meff.es/esp/Derivados-Financieros/Ficha/FIEM_MiniIbex_35')

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        if soup is not None:
            future = soup.find('table', {'id': 'Contenido_Contenido_tblFuturos'})
            df_future = pd.read_html(str(future), decimal=',', thousands='.')[0]
            df_future.columns = df_future.columns.get_level_values(0)
            df_future = df_future.iloc[:-1, [0, -1]]
            df_future.index = df_future.iloc[:, 0].values
            df_future = df_future.iloc[:, 1]
            df_future.index = pd.to_datetime(df_future.index, format='%d %b %Y')
            df_future.name = 'price'


            option = soup.find('table', {'id': 'tblOpciones'})
            indexes = option.find_all('tbody')[0].find_all('tr')[:-2]
            indexes = [i.attrs['data-tipo'] for i in indexes]

            df_option = pd.read_html(str(option), decimal=',', thousands='.')[0]
            df_option.columns = df_option.columns.get_level_values(0)
            list_option = df_option.iloc[:-2, [0, -1]].values[:].tolist()

            df_option = pd.DataFrame([[ind[1:2], ind[2:3], datetime.strptime(ind[3:], '%Y%m%d'), opt[0], opt[1]] for ind, opt in zip(indexes, list_option)], columns=['call_put', 'type', 'date', 'strike', 'price'])
            df_option.index = df_option.iloc[:, 2].values
            df_option = df_option.iloc[:, [0, 1, 3, 4]]
            df_option = df_option[df_option.type == 'E']

            return df_future, df_option

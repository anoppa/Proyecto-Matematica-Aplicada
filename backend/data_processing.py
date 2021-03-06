from typing import Dict
import pandas as pd
from pandas.core.frame import DataFrame
from sklearn.preprocessing import StandardScaler
import numpy as np
from random import random
from re import search

def to_dataFrame(file_path: str, other_reader = None) -> DataFrame:
        """
        Dada la dirección del archivo retorna un dataFrame con los datos.
        
        file_path -> dirección del archivo de datos
        other_reader -> función : (str) a DataFrame

        Extensiones soportadas: csv,xls,xlsx,xlsm,xlsb,odf,json
        
        Si no es ninguna de las extensiones contempladas y se recibe el parámetro
        other_reader, se aplica other_reader(file_path) 
        
        Excepción en caso de extensión inválida
        """
        df = None
        if file_path.endswith(".csv"):
            df = pd.read_csv(file_path)
        elif file_path.endswith((".xls", ".xlsx", ".xlsm", ".xlsb", ".odf")):
            df = pd.read_excel(file_path)
        elif file_path.endswith(".json"):
            df = pd.read_json(file_path, typ="frame")
        elif not other_reader == None:
            try:
                df = other_reader(file_path)
            except:
                raise Exception("other_reader function  failed")
        else:
            raise Exception("The extension is not allowed.")
        return df

class DataProcessor:

    def __replace_bad_character__(self, data: DataFrame) -> DataFrame:
        """
        data -> DataFrame completo incial
        Devuelve un dataframe donde se sustituyen por NaN todas las expresiones que indiquen
            ausencia de datos
            Ej: ---- se remplaza por NaN para ser procesado
        """
        pattern = "[A-Za-z0-9]+"  # patrón con el que se van a comparar todas las cadenas
        new_data_set = {}  # diccionario -> par {etiqueta:[valores]} del dataframe
        for col in data[:]:
            new_list_col = []
            for row in data[col]:
                if isinstance(row, str):
                    x = search(pattern, row)
                    if not x:
                        new_list_col.append(None)
                    else:
                        new_list_col.append(row)

                else:
                    new_list_col.append(row)
            new_data_set[col] = new_list_col

        return DataFrame(new_data_set)


    def __fill_na__(self, data: DataFrame) -> DataFrame:
        """
        Asigna a los valores nan de un feature determinado un valor de los que este feature puede tomar utilizando
        la probabilidad de ocurrencia de cada uno de esos valores a partir de una función de probabilidad
        """
        dict_values_to_freq = {}
        for feature in data.columns:
            dict_values_to_freq[feature] = {}
            for i, row in data.iterrows():
                if pd.isna(row[feature]):
                    continue
                else:
                    if row[feature] not in dict_values_to_freq[feature]:
                        dict_values_to_freq[feature][row[feature]] = 0
                    dict_values_to_freq[feature][row[feature]] += 1
            for value in dict_values_to_freq[feature]:
                dict_values_to_freq[feature][value] = dict_values_to_freq[feature][
                    value
                ] / (len(data) - data[feature].isna().sum())
            for i, row in data.iterrows():
                if pd.isna(row[feature]):
                    u = random()
                    acc_prob = 0
                    for value in dict_values_to_freq[feature]:
                        acc_prob += dict_values_to_freq[feature][value]
                        if u <= acc_prob:
                            data.loc[i, feature] = value
                            break
        return data


    def __values_fill_na__(self, data: DataFrame) -> DataFrame:
        """
        Rellena los valores nan de los atributos numéricos en el dataFrame original
        data-> dataFrame(data de entrada completa antes de dummy)
        """
        types = data.dtypes
        for i in range(len(types)):
            if types[i] == np.int64 or types[i] == np.float64:
                data.loc[:, data.columns.values[i]] = data.loc[
                    :, data.columns.values[i]
                ].fillna(data.loc[:, data.columns.values[i]].mean())
        return data


    def __precomputing_nominal_fill_na__(self, data: DataFrame):
        """
        Precomputa los diccionarios para la sustitución de los valores nan nominales
        """
        dict_values_to_prob = {}
        dict_atribute_rowsnan = {}
        for feature in data.columns:
            dict_values_to_prob[feature] = {}
            dict_atribute_rowsnan[feature] = []
            for i, row in data.iterrows():
                if pd.isna(row[feature]):
                    dict_atribute_rowsnan[feature].append(i)
                    continue
                else:
                    if row[feature] not in dict_values_to_prob[feature]:
                        dict_values_to_prob[feature][row[feature]] = 0
                    dict_values_to_prob[feature][row[feature]] += 1
            for value in dict_values_to_prob[feature]:
                dict_values_to_prob[feature][value] = dict_values_to_prob[feature][
                    value
                ] / (len(data) - data[feature].isna().sum())
        return dict_values_to_prob, dict_atribute_rowsnan


    def __nominal_fill_na__(self,
        data: DataFrame, dict_values_to_prob: Dict, dict_atribute_rowsnan: Dict
    ) -> DataFrame:
        """
        Rellena los valores nan de los atributos nominales en el data frame original
        data-> data frame (data de entrada completa luego de dummy)
        dict_values_to_prob -> diccionario atributo : (dict valor: probabilidad)
        dict_atribute_rowsnan -> diccionario atributo : lista de filas que tenían nan
        """
        for feature in dict_atribute_rowsnan:
            rows = dict_atribute_rowsnan[feature]
            if len(rows) == 0:
                continue
            for row in rows:
                for value in dict_values_to_prob[feature]:
                    prob = dict_values_to_prob[feature][value]
                    column_name = feature + "_" + value
                    data.loc[row, column_name] = prob
        return data


    def municipality_raw_parser(municipality_column) -> list:
        """
        Otorga un nombre standard a los municipios
        A los municipios fuera de La Habana les otorga el valor: habana del este
        """
        dict_munic = {
            "plaza de la revolucion": "plaza de la revoución",
            "plaza de la revoución": "plaza de la revoución",
            "plaza": "plaza de la revolucion",
            "centro habana": "centro habana",
            "habana vieja": "habana vieja",
            "playa": "playa",
            "cerro": "cerro",
            "marianao": "marianao",
            "diez de octubre": "diez de octubre",
            "10 de octubre": "diez de octubre",
            "la lisa": "la lisa",
            "boyero": "boyeros",
            "boyeros": "boyeros",
            "arroyo naranjo": "arroyo naranjo",
            "san miguel": "san miguel del padrón",
            "san miguel del padron": "san miguel del padrón",
            "san miguel del padrón": "san miguel del padrón",
            "cotorro": "cotorro",
            "guanabacoa": "guanabacoa",
            "habana del este": "habana del este",
        }
        result = []
        for munc in municipality_column:
            if pd.isna(munc) or munc.lower() not in dict_munic:
                munc = "habana del este"
            result.append(dict_munic[munc.lower()])
        return result


    def municipality_parser_universityDistance(self,municipality_column) -> list:
        """
        Realiza un primer municipality_parser_raw, y luego
        Otorga un valor standard a los municipios segun su cercanía con la universidad
        """
        dict_munic = {
            "plaza de la revoución": 0,
            "centro habana": 1,
            "habana vieja": 2,
            "playa": 2,
            "cerro": 2,
            "marianao": 3,
            "diez de octubre": 3,
            "la lisa": 4,
            "boyeros": 4,
            "arroyo naranjo": 4,
            "san miguel del padrón": 5,
            "cotoro": 5,
            "guanabacoa": 5,
            "habana del este": 5,
        }
        result = []
        for munc in self.municipality_raw_parser(municipality_column):
            if munc.lower() not in dict_munic:
                munc = "habana del este"
            result.append(dict_munic[munc.lower()] / 6)
        return result


    dict_parsers_global = {
        "municipality_raw_parser": municipality_raw_parser,
        "municipality_parser_universityDistance": municipality_parser_universityDistance,
    }


    def data_performing(self, df: DataFrame) -> DataFrame:
        """
        df-> data frame(data de entrada completa)
        Procesa y normaliza los datos para ser utilizados en el algoritmo de agrupamiento
        """
        relevant_data = df
        relevant_data = self.__replace_bad_character__(relevant_data)
        relevant_data = self.__values_fill_na__(relevant_data)
        dict_values_to_prob, dict_atribute_rowsnan = self.__precomputing_nominal_fill_na__(
            relevant_data
        )
        relevant_data = pd.get_dummies(relevant_data)
        relevant_data = self.__nominal_fill_na__(
            relevant_data, dict_values_to_prob, dict_atribute_rowsnan
        )
        sc = StandardScaler()
        relevant_data.loc[:, :] = sc.fit_transform(relevant_data)
        return relevant_data


    def data_weighted(self, df: DataFrame, attr: list([str, float])) -> DataFrame:
        """
        Asigna los pesos especificados a los atributos dentro del DataFrame
        Retorna un nuevo DataFrame con los valores actualizados
        """
        relevant_data = df
        for i in range(len(attr)):
            for column in relevant_data.columns.values:
                if column.startswith(attr[i][0]):
                    relevant_data.loc[:, column] *= attr[i][1]
        return relevant_data
'''
Python package for analyzing data of the following types:
    1. Seismic catalogue
        - Activity
        - b-value
    2. Radon measurements: activity and concentration
        - Indicator functions
    3. Inclination measurements
        - Indicator functions

(c) by Gleb Indakov
    MSU, IPE RAS
'''
# Загрузка даных
import pandas as pd
import numpy as np

class GetData:
    typelist = ['catalogues', 'catalogues_declastered',
                 'inclinometers', 'radon']
    
    def __init__(self, filetype, filename):
        self.filetype = filetype
        self.filename = filename
        print('Для данных типа ' + filetype,
              'Получаем DataFrame из ' + filename, sep='\n')
    
    def gd_seis(self):
        data = pd.read_table(self.filename, 
                             sep=';', 
                             skiprows=0) 
        data.Date = pd.to_datetime(data.Date, format = '%Y-%m-%dT%H:%M:%S.%f')
        data = data.drop(columns=['Event', 'Agency', 'Software', 
                                  'Volcano', 'Unnamed: 17']) # !download BaseNew-catalogue
        title = 'Данные сейсмического каталога Камчатки'
        return data, title    
    
    def gd_inc(self):
        data = pd.read_csv(self.filename, encoding = 'utf-8')
        data['DATE'] = pd.to_datetime(data['DATE'], format = '%Y-%m-%d %H:%M:%S')
        title = 'Исходные данные'
        return data, title
    
    def gd_radon(self):
        data = pd.read_excel(self.filename)
        data = data.rename(columns={'Unnamed: 0': 't', 
                             'Объемная активность радона, Бк/м^3': 'зона аэрации',
                             'Unnamed: 2': 'поверхность',
                             'Unnamed: 3': 'воздух',
                             'Unnamed: 4': 'ствол скважины',
                             'Давление': 'атм. давление'
                             })
        data = data.drop(index=0)
        data['t'] = pd.to_datetime(data['t'], format = '%Y-%m-%d %H:%M:%S.%f')
        title = 'Исходные данные'
        return data, title    
        print('Обрабатываем DataFrame')
    
    def get_data(self): # more convenient
        idx = GetData.typelist.index(self.filetype)
        if   idx == 0: # 'catalogues'
            return self.gd_seis()
        elif idx == 2: # 'inclinometers'
            return self.gd_inc()
        elif idx == 3: # 'radon'
            return self.gd_radon()
        
class DFtansform(GetData):
    
    def data_full(self, data, w=[]): # логарифм максимального значения в скользящем окне
        time = list(data.columns)[0]
        data_full = data.copy()
        if w == []:
            w = [10, 100, 1000]
        for name in list(data.columns)[1:]:
            val_diff = data[name].diff(periods=2).shift(periods=-1)
            t_diff = data[time].diff(periods=2).shift(periods=-1).dt.total_seconds()
            data_der_mod = ((val_diff / t_diff)**2)**(1/2)
            for win in w:
                col_name = name + '_' + str(win)
                data_full[col_name] = data_der_mod.rolling(win, min_periods=1).max().shift(-win//2)
                data_full[col_name] = np.log10(data_full[col_name].replace(to_replace = 0, value = 10**(-6)))
        title = 'Полный анализ данных'
        return data_full, title
    
    def activity(self):
        pass
    
    def b_value(self):
        pass

class DFtansform_steps(GetData):
        
    def der_cols(self, data):
        time = list(data.columns)[0]
        data_der = data[[time]].copy()
        for name in list(data.columns)[1:]:
            col_name = name + '_der'
            val_diff = data[name].diff(periods=2).shift(periods=-1)
            t_diff = data[time].diff(periods=2).shift(periods=-1).dt.total_seconds()
            data_der[col_name] = val_diff / t_diff
        title = 'Численная производная исходных данных (2T=120с)'
        return data_der, title
    
    def der_cols_2(self, data): # Применять к производной
        time = list(data.columns)[0]
        data_der_2 = data[[time]].copy()
        for name in list(data.columns)[1:]:
            col_name = name + '_2'
            data_der_2[col_name] = (data[name]**2)**(1/2)
        title = 'Модуль производной'
        return data_der_2, title
    
    def der_w(self, data, w=[]): # Расчет среднего в окнах с привязкой к центральной дате
        time = list(data.columns)[0]
        data_w = data[[time]].copy()
        if w == []:
            w = [10, 100, 1000]
        for name in list(data.columns)[1:]:
            for win in w:
                col_name = name.split('_')[0] + '_w_' + str(win)
                data_w[col_name] = data[name].rolling(win, min_periods=1).mean().shift(-win//2)
        title = 'Усреднение в окнах'
        return data_w, title
    
    def der_lg(self, data):
        time = list(data.columns)[0]
        data_lg = data[[time]].copy()
        for name in list(data.columns)[1:]:
            col_name = name.split('_')[0] + '_lg_' + name.split('_')[2]
            data_lg[col_name] = np.log10(data[name].replace(to_replace = 0, value = 10**(-6)))
        title = 'Индикаторная функция (логарифм модуля производной)'
        return data_lg, title
    
    def data_sep(self, name, d_list):
        data_sep = d_list[0][[list(d_list[0].columns)[0]]].copy()
        for data in d_list:
            col_name = [i for i in list(data.columns) if i.startswith(name)]
            data_sep[col_name] = data[col_name]
        title = 'Компонента ' + name
        return data_sep, title
#Графики
import matplotlib.pyplot as plt

class Graph:
    dpi = 300
    
    def __init__(self, data, time_start, time_end):
        print('Строим график:', *list(data.columns)[1:], sep=' ')
        name = list(data.columns)[0] # Первой колонкой обязательно должно стоять время DATE
        self.data = data[(data[name] >= time_start) & 
                         (data[name] <= time_end)] 
        # Сразу определим шрифты
        plt.rcParams['font.family'] = 'Times New Roman'
        plt.rcParams['font.size'] = 10
        
    def graph(self, 
              title='Заголовок',         # Название графика
              labels=[],                 # Легенда
              par_loc='upper left',      # Положение легенды
              xlabel='',                 # Подпись оси времени (X) - общая
              ylabel=[],                 # Названия осей y
              colors=[],                 # Цвета графиков
              figsize=(8,6),             # Размер графика
              save_fig=True):            # Сохранить график в папку     
        data = self.data
        data_col = list(data.columns)[1:]
        time = list(data.columns)[0]
        num = len(data_col)
        
        if ylabel == []:
            ylabel = data_col        
        if labels == []:
            labels = data_col
        if colors == []:
            color = plt.rcParams['axes.prop_cycle']()
            for i in range(num):
                c = next(color)['color']
                colors.append(c)
        
        fig, ax = plt.subplots(num, sharex=True, dpi=Graph.dpi, figsize=figsize)
        fig.suptitle(title)
        for ax, data_col, labels, colors, ylabel in zip(ax.flat, data_col, labels, colors, ylabel):
            ax.plot(data[time], data[data_col], color=colors, label=labels)
            ax.legend(loc=par_loc)
            ax.grid()
            ax.tick_params(axis='x', rotation=20)
            ax.set_xlim([data[time].min(), data[time].max()])
            
            ax.set_ylabel(ylabel)
        
        fig.subplots_adjust(hspace=1.0)
        fig.tight_layout(pad=1.2)
        fig.supxlabel(xlabel)
        
        plt.show()
        if save_fig:
            fig.savefig('B:\Рабочий стол\Геошкола\радон\pics\\' + title + '.png')

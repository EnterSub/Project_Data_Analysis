import os
import requests
import pandas as pd
import json
import numpy as np
import re
import bs4
from datetime import date

from kivymd.app import MDApp
from kivymd.uix.screen import Screen
from kivy.lang import Builder
from kivymd.uix.button import MDRectangleFlatButton
from kivy.uix.screenmanager import ScreenManager

from kivymd.uix.filemanager import MDFileManager
from kivy.core.window import Window

from kivymd.uix.datatables import MDDataTable
from kivy.metrics import dp
import numpy as np

from google.cloud import bigquery

API_KEY = os.environ['API_KEY']
model_id = os.environ['ID']
url = os.environ['URL_TO_FILE'] + model_id + os.environ['URL_TYPE']

list_path = []

def load_page(link):
    data = {'file': open(link, 'rb')}
    response = requests.post(url, auth=requests.auth.HTTPBasicAuth(API_KEY, ''), files=data)

    col_max, row_max = 0, 0
    table = []
    data = json.loads(response.text)

    for i in data['result']:
        for j in i['prediction']:
            for k in j['cells']:
                table.append(k['text'])
                # table.append(k['score'])
                if k['col'] > 0:
                    col_max = k['col']
                if k['row'] > 0:
                    row_max = k['row']

    k = np.array(table).reshape(row_max, col_max * len(table) // (col_max * row_max))
    return k

def subjects_schedule(group_name):
    schedule_url = os.environ['SITE_NAME'] + group_name + os.environ['SITE_TYPE']
    TITLE = os.environ['SITE_TITLE']
    ITEM = os.environ['SITE_ITEM']
    BODY = os.environ['SITE_BODY']
    ROW = os.environ['SITE_ROW']
    TIME = os.environ['SITE_TIME']
    LABEL = os.environ['SITE_LABEL']
    DAY = os.environ['SITE_DAY']

    table_list, list_all_table, list_all_table_2, list_all_table_data, d, d2 = [], [], [], [], [], []

    req = requests.get(schedule_url)
    parser = bs4.BeautifulSoup(req.text, 'lxml')
    week_n = parser.find(class_=TITLE).text
    week_n = re.findall(r'\d+', week_n)
    week_n = int(str(week_n[0]))

    table = parser.findAll(class_=BODY)
    rows_ = [r for r in table[0].findAll(class_=ROW) if r.findAll(class_=DAY)]
    for r in rows_:
        day = r.findAll(class_=DAY)[0].text
        time_rows = [dr for dr in r.findAll(class_=ROW) if dr.findAll(class_=TIME)]
        for tr in time_rows:
            time = tr.findAll(class_=TIME)[0].text
            lessons = [lesson for lesson in tr.findAll(class_=ROW) if lesson.findAll(class_=ITEM)]
            lessons_list = []
            for lesson in lessons:
                week_type = lesson.findAll(class_=LABEL)[0].findChild('span').text if lesson.findAll(
                    class_=LABEL) else ''
                item = lesson.findAll(class_=ITEM)[0] if lesson.findAll(class_=LABEL) else lesson.findAll(class_=ITEM)[
                    0]
                item_lable_reg = re.search(r'\t[\w\s,.]+', item.text if item else None)
                item_lable = re.sub(r'(\s+·)|[\n\t]|\s{2}', '', item_lable_reg.group(0)) if item_lable_reg else None
                lessons_list.append({'w': week_type, 'n': item_lable})
            if lessons_list:
                table_list.append({'d': day, 't': time, 'i': lessons_list})

    for i in table_list:
        list_all_table.append([i['d'], i['t'], i['i']])

    for t, i, j in list_all_table:
        list_all_table_2.append([t, i, j])

    for i in list_all_table_2:
        for j in i[2]:
            list_all_table_data.append([i[0], i[1], j['w'], j['n']])

    for t, i, j, k in list_all_table_data:
        d.append(
            {
                'week_n': t,
                'class_t': i,
                'week_t': j,
                'subject': "".join([k[0].upper() for k in k.split()])
            }
        )
    df = pd.DataFrame(d)

    list_values_subjects = []
    for count, i in enumerate(df['week_t'], 0):
        if "недели" in i:
            list_values_subjects.append(count)

    for i in list_values_subjects:
        k = df.loc[i, 'week_t']
        k = re.findall(r'\d.*', k)
        l = k[0].split(' ')
        df.loc[i, 'week_t'] = list(map(int, l))

    for count, i in enumerate(df['week_t'], 0):
        if i == "по чётным":
            df.loc[count, 'week_t'] = [i for i in range(1, 19) if i % 2 == 0]
        elif i == "по нечётным":
            df.loc[count, 'week_t'] = [i for i in range(1, 19) if i % 2 == 1]
        elif not i:
            df.loc[count, 'week_t'] = [i for i in range(1, 19)]

    ###
    for count, i in enumerate(df['week_n'], 0):
        if df.loc[count, 'week_n'] == 'пн':
            df.loc[count, 'week_n'] = 1
        elif df.loc[count, 'week_n'] == 'вт':
            df.loc[count, 'week_n'] = 2
        elif df.loc[count, 'week_n'] == 'ср':
            df.loc[count, 'week_n'] = 3
        elif df.loc[count, 'week_n'] == 'чт':
            df.loc[count, 'week_n'] = 4
        elif df.loc[count, 'week_n'] == 'пт':
            df.loc[count, 'week_n'] = 5
        elif df.loc[count, 'week_n'] == 'сб':
            df.loc[count, 'week_n'] = 6

    for count, i in enumerate(df['class_t'], 0):
        if df.loc[count, 'class_t'] == '08:30-10:00':
            df.loc[count, 'class_t'] = 1
        elif df.loc[count, 'class_t'] == '10:15-11:45':
            df.loc[count, 'class_t'] = 2
        elif df.loc[count, 'class_t'] == '12:00-13:30':
            df.loc[count, 'class_t'] = 3
        elif df.loc[count, 'class_t'] == '14:00-15:30':
            df.loc[count, 'class_t'] = 4
        elif df.loc[count, 'class_t'] == '15:45-17:15':
            df.loc[count, 'class_t'] = 5
        elif df.loc[count, 'class_t'] == '17:30-19:00':
            df.loc[count, 'class_t'] = 6
        elif df.loc[count, 'class_t'] == '19:15-20:45':
            df.loc[count, 'class_t'] = 7
        elif df.loc[count, 'class_t'] == '21:00-22:30':
            df.loc[count, 'class_t'] = 8
    ###

    for count, i in enumerate(df['week_t'], 0):
        if week_n in i and len(df['subject'][count]) and df['subject'][count] != 'ФКИС':
            d2.append(
                {
                    'week_n': df.loc[count][0],
                    'class_t': df.loc[count][1],
                    'subject': df.loc[count][3]
                }
            )

    df_current = pd.DataFrame(d2)
    if df_current.empty:
        l = ''
    else:
        l = df_current
    return group_name, df_current, l, week_n

def page_left():
    k = load_page(link=list_path[0])
    df_columns, list_values_week, list_signature_value_lecturer, list_signature_lecturer, list_signature_value, list_signature, list_value_sum, values_subject_1, values_subject_index = [], [], [], [], [], [], [], [], []
    df_1 = pd.DataFrame(k)
    df_1.is_copy = False
    df_columns = ["number", "student"]
    list_index_with_subjects = []

    for i in df_1.columns[:len(df_1.columns) - len(df_columns)]:
        df_columns.append(f"column{i + 1}")

    df_1 = pd.DataFrame(k, columns=df_columns)

    if df_1.loc[1, 'student'] != "Предмет":
        value = "Предмет"
        df_1.loc[1, 'student'] = value
    if df_1.loc[2, 'student'] != "Тип занятия":
        value = "Тип занятия"
        df_1.loc[2, 'student'] = value

    for count, i in enumerate(df_1.loc[0][2:], 0):
        if i:
            list_values_week.append(i)

    # Cells that contain subjects
    for count, i in enumerate(df_1.loc[1][2:], 0):
        if i:
            list_index_with_subjects.append(count + 2)

    for i in list_index_with_subjects:
        if 1 <= i <= 4:
            df_1.loc[0][i] = list_values_week[0]
        elif 5 <= i <= 8:
            df_1.loc[0][i] = list_values_week[1]
        elif 9 <= i <= 12:
            df_1.loc[0][i] = list_values_week[2]

    for i in range(2, len(df_1.loc[1][:])):
        if i not in list_index_with_subjects:
            df_1.loc[0][i] = ''

    for count, i in enumerate(df_1.loc[38], 0):
        if i:
            if count >= 2:
                list_signature_value_lecturer.append(i)
                list_signature_lecturer.append(count)
    df_1.loc[38][list_signature_lecturer] = "Yes"

    for count, i in enumerate(df_1.loc[39], 0):
        if i:
            if count >= 2:
                list_signature_value.append(i)
                list_signature.append(count)
    df_1.loc[39][list_signature] = "Yes"

    df_1.loc[37, 'student'] = "Всего отсутствовало"
    df_1.loc[38, 'student'] = "Подпись преподавателя"
    df_1.loc[39, 'student'] = "Подпись старосты"

    for count, i in enumerate(df_1.loc[2], 0):
        if len(i) > 1 and count > 1:
            value = "Практические занятия"
            df_1.iloc[2, count] = value
        elif len(i) == 1 and count > 1:
            value = "Лекция"
            df_1.iloc[2, count] = value
        elif len(i) == 0 and count > 1:
            pass
    df_1 = df_1.where(df_1.notnull(), '')

    n = df_1.iloc[3:37, 2:14].replace(r'^\s*$', np.nan, regex=True).isna().all()

    for count, i in enumerate(n, 0):
        if not i:
            values_subject_1.append(count + 2)

    for i in values_subject_1:  # Fill only columns with some subject
        df_1.iloc[3:37, i:i + 1] = df_1.iloc[3:37, i:i + 1].apply(
            lambda x: x.str.extract(r'([а-яА-Яa-zA-Z0-9])', expand=False)).replace('None', np.nan).notnull().astype(int)
        list_value_sum.append(sum(df_1.iloc[3:37, i]))

    for count, i in enumerate(df_1.loc[1], 0):
        if i and count >= 2:
            values_subject_index.append(count)

    for i in values_subject_index:
        value = sum(df_1.iloc[3:37, i])
        df_1.iloc[37, i] = value

    for count, i in enumerate(df_1['number'][1:df_1.shape[0] - 5], 1):
        df_1.loc[count + 2, 'number'] = count

    for count, i in enumerate(df_1['student'][3:df_1.shape[0]-3], 3):
        if i:
            df_1.loc[count, 'student'] = f"Student{df_1.loc[count, 'number']}"

    return df_1, k

def page_right():
    k = load_page(link=list_path[1])
    df_columns, list_values_week, list_signature_value_lecturer, list_signature_lecturer, list_signature_value, list_signature, list_value_sum, values_subject_2, values_subject_index = [], [], [], [], [], [], [], [], []
    df_2 = pd.DataFrame(k)
    df_2.is_copy = False
    list_index_with_subjects = []

    for i in df_2.columns:
        df_columns.append(f"column{i + 13}")

    df_2 = pd.DataFrame(k, columns=df_columns)

    # Insert row just with numbers (or student names) from previous df
    df_2 = df_2.rename({'column25': 'lectures_all', 'column26': 'lectures', 'column27': 'message'}, axis=1)

    for count, i in enumerate(df_2.loc[0][:12], 0):
        if i:
            list_values_week.append(i)

    # Cells that contain subjects
    for count, i in enumerate(df_2.loc[1][:12], 0):
        if i:
            list_index_with_subjects.append(count)

    for i in list_index_with_subjects:
        if 0 <= i <= 4:
            df_2.loc[0][i] = list_values_week[0]
        elif 5 <= i <= 8:
            df_2.loc[0][i] = list_values_week[1]
        elif 9 <= i <= 12:
            df_2.loc[0][i] = list_values_week[2]

    for i in range(2, len(df_2.loc[1][:])):
        if i not in list_index_with_subjects:
            df_2.loc[0][i] = ''

    for count, i in enumerate(df_2.loc[38], 0):
        if i:
            if count >= 0:
                list_signature_value_lecturer.append(i)
                list_signature_lecturer.append(count)
    df_2.loc[38][list_signature_lecturer] = "Yes"

    for count, i in enumerate(df_2.loc[39], 0):
        if i:
            if count >= 0:
                list_signature_value.append(i)
                list_signature.append(count)
    df_2.loc[39][list_signature] = "Yes"

    df_2.loc[0, 'lectures_all':'lectures'] = 'Пропущено часов занят.'
    df_2.loc[1:2, 'lectures_all'] = 'всего'
    df_2.loc[1:2, 'lectures'] = 'по уважит. прич.'
    df_2.loc[0:2, 'message'] = 'Замечания деканата и преподавателей'

    for count, i in enumerate(df_2.loc[2], 0):
        if len(i) > 1 and count < 12:
            value = "Практические занятия"
            df_2.iloc[2, count] = value
        elif len(i) == 1 and count < 12:
            value = "Лекция"
            df_2.iloc[2, count] = value
        elif len(i) == 0 and count < 12:
            pass
    df_2 = df_2.where(df_2.notnull(), '')

    j = df_2.iloc[3:37, :12].replace(r'^\s*$', np.nan, regex=True).isna().all()

    for count, i in enumerate(j, 0):
        if not i:
            values_subject_2.append(count)

    for i in values_subject_2:  # Fill only columns with some subject
        df_2.iloc[3:37, i:i + 1] = df_2.iloc[3:37, i:i + 1].apply(
            lambda x: x.str.extract(r'([а-яА-Яa-zA-Z0-9])', expand=False)).replace('None', np.nan).notnull().astype(int)
        list_value_sum.append(sum(df_2.iloc[3:37, i]))

    for count, i in enumerate(df_2.loc[1], 0):
        if i and 0 <= count < 12:
            values_subject_index.append(count)

    for i in values_subject_index:
        value = sum(df_2.iloc[3:37, i])
        df_2.iloc[37, i] = value
    return df_2, k

class ProjectApp(MDApp):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Window.bind(on_keyboard=self.events)
        self.manager_open = False
        self.file_manager = MDFileManager(
            exit_manager=self.exit_manager,
            select_path=self.select_path,
            preview=False,
        )
        self.data_tables = None

    #Screen 1
    def start(self):
        if self.root.ids.user.text == "" and self.root.ids.password.text == "":
            self.root.current = 'menu'
        # else:
        #     self.root.ids.user.text = ""
        #     self.root.ids.password.text = ""

    def close(self):
        pass

    #Screen 2
    def show_data(self):
        text = subjects_schedule(self.root.ids.textbox.text)[2]  # l
        if len(text) > 0:  # Если название не пустое, то
            self.root.current = 'processing'  # Переключиться на Screen2
        else:  # Иначе
            self.root.ids.textbox.text = ""
        textbox = self.root.ids.textbox.text
        return textbox, text

    def collect(self):
        func = subjects_schedule(self.root.ids.textbox.text)
        df_current = func[1]
        week_n = func[3]
        df_1, k = page_left()
        #df_1_shape = k
        df_2, k = page_right()
        #df_2_shape = k
        df_1.loc[0, 'number'] = self.root.ids.textbox.text
        df_1.loc[1, 'number'] = week_n
        df = df_1.join(df_2)

        for i in range(df.shape[0])[3:37]:
            k = 0
            for count, j in enumerate(df.iloc[i, 2:26]):
                if j:
                    k += j
            df.loc[i, 'lectures_all'] = k

        n = 0
        for i in df.loc[37][2:df.shape[1] - 3]:
            if i:
                n += i
        df.loc[37, 'lectures_all'] = n

        list_subjects_indexes = []
        j = 0
        for count, i in enumerate(df.loc[1][2:df.shape[1] - 3], 0):
            if count % 4 == 0:
                j += 1
            if i:
                list_subjects_indexes.append([j, (count % 4) + 1, count + 2, i])

        list1 = list(df_current['week_n'])
        list2 = []

        n = 1
        for count, i in enumerate(list1):
            list2.append(n)
            if count + 1 < len(list1):
                if list1[count + 1] == list1[count]:
                    n += 1
                else:
                    n = 1

        list1 = pd.Series(list1)
        list2 = pd.Series(list2)

        list_subjects_indexes_week_n = []

        for i, j, z in zip(list1, list2, df_current['subject']):
            list_subjects_indexes_week_n.append([i, j, z])

        for i in list_subjects_indexes:
            for j in list_subjects_indexes_week_n:
                if i[0] == j[0] and i[1] == j[1]:
                    df.loc[1][i[2]] = j[2]

        for count, i in enumerate(df['student'][3:df.shape[0] - 3], 1):
            if not i:
                df.loc[count + 2, 'number'] = ''

        list_values_number = []
        for count, i in enumerate(df['number'][3:37], 1):
            if not i:
                list_values_number.append(count + 2)

        k = 0
        for i in df.loc[0][2:df.shape[1] - 3]:
            if i:
                k += 1
        k = [i for i in range(k + 1)]

        for j in k:
            for i in list_values_number:
                df.iloc[i][2:27] = df.iloc[i][2:27].replace(j, '')

        ### Selecting part from df for DB processing
        df_students = df.iloc[1:37, :27]
        df_students.loc[1, 'student'] = "Студент"
        df_students = df_students[df_students["number"] != '']

        list_values_df = []

        for count, i in enumerate(df.iloc[0, 2:df.shape[1] - 3], 2):
            if i:
                list_values_df.append(df.columns[count])

        l = 0
        for i in list_values_df:
            df_students.loc[24, i] = sum(df_students.loc[2:df_students.shape[0], i])
            l += df_students.loc[24, i]
        df_students.loc[24, 'lectures_all'] = l
        df_students.loc[24, 'number'] = 'total'
        df_students.loc[24, 'student'] = 'all'

        df_students = df_students[1:df_students.shape[0] - 1]
        df_students = df_students[["number", "student", "lectures_all"]]
        df_students['group'] = df.loc[0, 'number']
        df_students['week_n'] = df.loc[1, 'number']
        df_students['date'] = date.today()
        df_students = df_students.fillna('')


        df_subjects = df.drop(0)
        df_subjects = df_subjects.drop(columns=['number', 'student', 'lectures_all', 'lectures', 'message'])
        df_subjects = df_subjects[0:df_students.shape[0] + 2]
        df_subjects = df_subjects[df_subjects[list_values_df] != '']
        df_subjects = df_subjects[list_values_df]
        df_subjects_sum = pd.DataFrame(columns=['subject', 'total', 'group', 'week_n', 'date'])
        df_subjects_sum.loc[:, 'subject'] = df_subjects.loc[1][:df_subjects.shape[1]]
        df_subjects_sum = df_subjects_sum.reset_index(drop=True)

        df_subjects = df_subjects.drop(1)
        df_subjects = df_subjects.drop(2)
        df_subjects = df_subjects.reset_index(drop=True)

        for count, i in enumerate(df_subjects, 0):
            df_subjects_sum.loc[count, 'total'] = sum(df_subjects.loc[:, i])

        df_subjects_sum['group'] = df.loc[0, 'number']
        df_subjects_sum['week_n'] = df.loc[1, 'number']
        df_subjects_sum['date'] = date.today()
        df_subjects_sum = df_subjects_sum.groupby(['subject', 'group', 'week_n', 'date'])['total'].sum().reset_index()
        return df, df_students, df_subjects_sum

    #Screen 3
    def file_manager_open(self):
        self.file_manager.show('/')  # Output manager to the screen
        self.manager_open = True

    def select_path(self, path):
        list_path.append(path)  # Upgrade with checking by len of items
        self.exit_manager()
        return list_path

    def exit_manager(self, *args):
        self.manager_open = False
        self.file_manager.close()

    def events(self, instance, keyboard, keycode, text, modifiers):
        if keyboard in (1001, 27):
            if self.manager_open:
                self.file_manager.back()
        return True

    def show_table(self):
        global df_students  #Define global variable to optimize calling function count (can be change)
        global df_subjects_sum  #Define global variable to optimize calling function count (can be change)
        df, df_students, df_subjects_sum = self.collect()
        table = df_subjects_sum
        if table.shape[0] > 0 and table.shape[1] > 0:  # Указать размеры таблицы, иначе не та таблица (40 rows × 29 columns)
            #Screen 5
            self.root.current = 'db'
            #Screen 4
            table_kivymd = table
            column_data = list(table_kivymd.columns)
            row_data = table_kivymd.to_records(index=False)
            column_data = [(x, dp(60)) for x in column_data]
            self.data_tables = MDDataTable(
                use_pagination=True,
                column_data=column_data,
                row_data=row_data,
                #rows_num=len(row_data)  #To show all rows in 1 page (with disabled use_pagination property)
            )

            # self.button_next = MDRectangleFlatButton(
            #         text="Next",
            #         icon="language-python",
            #         pos_hint={"center_x": .5, "center_y": .2}
            #     )

            self.root.ids.data_scr.add_widget(self.data_tables)
            #self.root.ids.data_scr.add_widget(self.button_next)
        else:  # Иначе
            self.root.current = 'processing'  # Переключиться на Screen1
        return table, table_kivymd

    # def button_checking(self):
    #     if self.root.ids.button_next.state == 'down':
    #         print("Button pressed")
    #         self.root.current = 'db'

    def db_processing(self):
        if self.root.ids.collect.state == 'down':
            key = 'bigquery_key.json'
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = key

            client = bigquery.Client()
            table_id_1 = os.environ['TABLE_ID_1']
            table_id_2 = os.environ['TABLE_ID_2']

            job_1 = client.load_table_from_dataframe(
                df_students, table_id_1)
            job_1.result()

            job_2 = client.load_table_from_dataframe(
                df_subjects_sum, table_id_2)
            job_2.result()
        else:
            pass

    def build(self):
        self.theme_cls.theme_style = "Light"
        self.theme_cls.primary_palette = "Green"
        return Builder.load_file('settings.kv')

ProjectApp().run()
#Copyright (c) Dmitry Moskalev
import os  # Currently, os module is only for PC version (CHANGE_EXCLUDE)
from kivy.core.window import Window
import requests
import pandas as pd
import json
import numpy as np
import re
import bs4
import pandas_gbq
from google.oauth2 import service_account
from datetime import date
from kivymd.app import MDApp
from kivy.lang import Builder
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFillRoundFlatButton
from kivymd.uix.filemanager import MDFileManager
from kivy.metrics import dp
from kivymd.uix.datatables import MDDataTable
# from android.storage import primary_external_storage_path
#SD_CARD = primary_external_storage_path()

Window.size = (360, 640)

class Student_Digitizer(MDApp):

    project_id = os.environ['PROJECT_ID']
    table_id_authorization = os.environ['TABLE_ID_AUTHORIZATION']
    credentials = service_account.Credentials.from_service_account_file('bigquery_key.json')

    sql = f"""SELECT * FROM `{table_id_authorization}`"""
    df_authorization = pd.read_gbq(query=sql,
                                   project_id=project_id,
                                   dialect='standard',
                                   credentials=credentials)

    logins = list(df_authorization['login'])
    passwords = list(df_authorization['password'])
    model_id = list(df_authorization['id_model'])
    model_key = list(df_authorization['key_model'])
    access = list(df_authorization['access_type'])

    table_id_1 = os.environ['TABLE_ID_1']
    table_id_2 = os.environ['TABLE_ID_2']

    header_label = os.environ['SITE_HEADER_LABEL']
    SITE_TITLE = os.environ['SITE_TITLE']
    ITEM = os.environ['SITE_ITEM']
    BODY = os.environ['SITE_BODY']
    ROW = os.environ['SITE_ROW']
    TIME = os.environ['SITE_TIME']
    LABEL = os.environ['SITE_LABEL']
    DAY = os.environ['SITE_DAY']
    CLASS_N = os.environ['CLASS_N']
    GROUP_NAME = os.environ['GROUP_NAME']

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Window.bind(on_keyboard=self.events)
        self.just_file = ''
        self.list_file_path = []
        self.list_path = []
        self.dialog = None
        self.manager_open = False
        self.file_manager = MDFileManager(
            exit_manager=self.exit_manager,
            select_path=self.select_path,
            preview=False,
        )
        self.data_tables = None
        self.subjects_table = None

    def authorization(self):
        for i, j, n, m, l in zip(self.logins, self.passwords, self.model_id, self.model_key, self.access):
            if self.root.ids.user.text == i and self.root.ids.password.text == j:
                self.root.ids.id_model.text = n
                self.root.ids.key_model.text = m
                self.root.current = 'model_login'
        else:
            self.root.ids.user.text = ''
            self.root.ids.password.text = ''

    def week_schedule(self):
        schedule_url = os.environ['SITE_NAME']  # (CHANGE)
        try:
            req = requests.get(schedule_url)
            parser = bs4.BeautifulSoup(req.text, 'lxml')
        except Exception:
            value_schedule = "No connection"
        else:
            try:
                value_schedule = parser.find(class_=self.header_label).text
                value_schedule = re.findall(r'\d+', value_schedule)
                value_schedule = value_schedule[0]
            except Exception:
                value_schedule = "No subjects in university schedule"
        return value_schedule

    def load_page(self, link):
        url = os.environ['URL_TO_FILE'] + self.root.ids.id_model.text + os.environ['URL_TYPE']
        data = {'file': open(link, 'rb')}
        response = requests.post(url, auth=requests.auth.HTTPBasicAuth(self.root.ids.key_model.text, ''), files=data)

        # If response.status_code == 200 continue processing

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

    def page_left(self):
        k_1 = self.load_page(link=self.list_path[0])
        df_1 = pd.DataFrame(k_1)
        df_1.is_copy = False
        df_columns = ["number", "student"]

        for i in df_1.columns[:len(df_1.columns) - len(df_columns)]:
            df_columns.append(f"column{i + 1}")

        df_1 = pd.DataFrame(k_1, columns=df_columns)

        if df_1.loc[1, 'student'] != "Предмет":
            value = "Предмет"
            df_1.loc[1, 'student'] = value
        if df_1.loc[2, 'student'] != "Тип занятия":
            value = "Тип занятия"
            df_1.loc[2, 'student'] = value

        df_1.loc[37, 'student'] = "Всего отсутствовало"
        df_1.loc[38, 'student'] = "Подпись преподавателя"
        df_1.loc[39, 'student'] = "Подпись старосты"

        for count, i in enumerate(df_1['number'][1:df_1.shape[0] - 5], 1):
            df_1.loc[count + 2, 'number'] = count

        for count, i in enumerate(df_1['student'][3:df_1.shape[0] - 3], 3):
            if i:
                df_1.loc[count, 'student'] = f"Student{df_1.loc[count, 'number']}"
        return df_1, k_1

    def page_right(self):
        k_2 = self.load_page(link=self.list_path[1])
        df_columns = []
        df_2 = pd.DataFrame(k_2)
        df_2.is_copy = False

        for i in df_2.columns:
            df_columns.append(f"column{i + 13}")

        df_2 = pd.DataFrame(k_2, columns=df_columns)

        # Insert row just with numbers (or students names) from previous df
        df_2 = df_2.rename({'column25': 'lectures_all', 'column26': 'lectures', 'column27': 'message'}, axis=1)

        df_2.loc[0, 'lectures_all':'lectures'] = 'Пропущено часов занят.'
        df_2.loc[1:2, 'lectures_all'] = 'всего'
        df_2.loc[1:2, 'lectures'] = 'по уважит. прич.'
        df_2.loc[0:2, 'message'] = 'Замечания деканата и преподавателей'
        return df_2, k_2

    def show_alert_dialog(self):
        self.dialog = ""
        if not self.dialog:
            self.dialog = MDDialog(
                text=f"Ошибка:\n{self.root.ids.textbox_week_number.text}" if self.root.ids.lang.active
                else f"Error:\n{self.root.ids.textbox_week_number.text}",
                buttons=[
                    MDFillRoundFlatButton(
                        font_style="Button",
                        md_bg_color=(138.0 / 255.0, 161.0 / 255.0, 107.0 / 255.0, .5),
                        text="Загрузка из файла" if self.root.ids.lang.active else "Manual load",
                        on_release=lambda _: screen_update()),

                    MDFillRoundFlatButton(
                    font_style="Button",
                    md_bg_color=(138.0 / 255.0, 161.0 / 255.0, 107.0 / 255.0, .5),
                    text="Закрыть" if self.root.ids.lang.active else "Cancel",
                    on_release=lambda _: self.dialog.dismiss())
                ])
        self.dialog.open()

        def screen_update():
            self.dialog.dismiss()
            screen = self.root.current = 'manual_load'
            return screen

    def show_information(self):
        self.dialog = ""
        if not self.dialog:
            self.dialog = MDDialog(
                text=f"Для более подробной информации напишите по контактам" \
                    if self.root.ids.lang.active else f"For more information write to contact list",
                buttons=[MDFillRoundFlatButton(
                    font_style="Button",
                    md_bg_color=(138.0 / 255.0, 161.0 / 255.0, 107.0 / 255.0, .5),
                    text="Cancel",
                    on_release=lambda _: self.dialog.dismiss())])
        self.dialog.open()

    def subjects_schedule(self, group_name):
        schedule_url_full = os.environ['SITE_NAME'] + group_name + os.environ['SITE_TYPE']  # (CHANGE)
        table_list, list_all_table, list_all_table_2, list_all_table_data, d, d2 = [], [], [], [], [], []

        if self.root.ids.textbox_week_number.text != "No connection" \
                and self.root.ids.textbox_week_number.text != "No subjects in university schedule":
            req = requests.get(schedule_url_full)
            parser = bs4.BeautifulSoup(req.text, 'lxml')
        else:
            self.just_file = self.list_file_path[0]
            with open(self.just_file, encoding='utf-8') as file:
                src = file.read()
                parser = bs4.BeautifulSoup(src, "lxml")
        try:
            self.value_schedule = ''
            value_schedule = int(self.week_schedule())
            value_schedule = int(self.root.ids.textbox_week_number.text)
        except Exception:
            value_schedule = parser.find(class_=self.SITE_TITLE).text
            value_schedule = re.findall(r'\d+', value_schedule)
            value_schedule = int(str(value_schedule[0]))
            group_name = parser.find(class_=self.GROUP_NAME).text.split('&middot')[1].replace(" ", "")

        table = parser.findAll(class_=self.BODY)
        rows_ = [r for r in table[0].findAll(class_=self.ROW) if r.findAll(class_=self.DAY)]
        for r in rows_:
            day = r.findAll(class_=self.DAY)[0].text
            time_rows = [dr for dr in r.findAll(class_=self.ROW) if dr.findAll(class_=self.TIME)]
            for tr in time_rows:
                time = tr.findAll(class_=self.TIME)[0].text
                lessons = [lesson for lesson in tr.findAll(class_=self.ROW) if lesson.findAll(class_=self.ITEM)]
                lessons_list = []
                for lesson in lessons:
                    week_type = lesson.findAll(class_=self.LABEL)[0].findChild('span').text \
                        if lesson.findAll(class_=self.LABEL) else ''
                    item = lesson.findAll(class_=self.ITEM)[0] \
                        if lesson.findAll(class_=self.LABEL) else lesson.findAll(class_=self.ITEM)[0]
                    class_number = item.findAll(class_=self.CLASS_N)[0].text.replace('&nbsp', '')
                    item_label_reg = re.search(r'\t[\w\s,-.]+', item.text if item else None)
                    item_label = re.sub(r'(\s+·)|[\n\t]|\s{2}', '', item_label_reg.group(0)) if item_label_reg \
                        else None
                    item_label = item_label.replace(class_number, '').strip()
                    lessons_list.append({'w': week_type, 'n': item_label, 'c': class_number})
                if lessons_list:
                    table_list.append({'d': day, 't': time, 'i': lessons_list})

        for i in table_list:
            list_all_table.append([i['d'], i['t'], i['i']])

        for t, i, j in list_all_table:
            list_all_table_2.append([t, i, j])

        for i in list_all_table_2:
            for j in i[2]:
                list_all_table_data.append([i[0], i[1], j['w'], j['n']])

        all_subjects_full = []

        for t, i, j, k in list_all_table_data:
            k_split = "".join([k[0].upper() for k in k.split()])
            if k and k_split != "ФКИС":
                all_subjects_full.append(k)
                d.append(
                    {
                        'week_n': t,
                        'class_t': i,
                        'week_t': j,
                        'subject': k_split
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

        for count, i in enumerate(df['week_t'], 0):
            if value_schedule in i and len(df['subject'][count]) and df['subject'][count] != 'ФКИС':
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

        try:
            if self.subjects_df:
                self.subjects_df = self.subjects_df[0:0]
        except Exception:
            all_subjects_full = set(all_subjects_full)
            subject_values_sorted = []

            for j in all_subjects_full:
                k_split = "".join([j[0].upper() for j in j.split()])
                subject_values_sorted.append(k_split)

            list_subjects = []

            for i, j in zip(subject_values_sorted, all_subjects_full):
                list_subjects.append(
                    {
                        'abbreviate': i,
                        'subject': j
                    }
                )
            subjects_df = pd.DataFrame(list_subjects)
            column_subjects = list(subjects_df.columns)
            row_data_subjects = subjects_df.to_records(index=False)
            column_subjects = [(x, dp(25)) if _ % 2 == 0 else (x, dp(250)) for _, x in enumerate(column_subjects, 0)]

            if not self.subjects_table:
                self.subjects_table = MDDataTable(
                    background_color_header=(0, 1, 0, .1),
                    pos_hint={"top": 1, "center_y": 0.5},
                    size_hint_x=1,
                    size_hint_y=None,
                    height=Window.height * 0.9,
                    use_pagination=True,
                    column_data=column_subjects,
                    row_data=row_data_subjects,
                )
                self.root.ids.subjects_box.add_widget(self.subjects_table)
            else:
                self.subjects_table.update_row_data(self.subjects_table, row_data_subjects)
        return group_name, df_current, l, value_schedule

    # Screen 1
    def start(self):
        if self.root.ids.id_model.text != "" and self.root.ids.key_model.text != "":
            try:
                self.root.ids.textbox_week_number.text = self.week_schedule()
            except Exception:
                pass
            if self.root.ids.textbox_week_number.text == "No connection" \
                    or self.root.ids.textbox_week_number.text == "No subjects in university schedule":
                self.show_alert_dialog()
            else:
                self.root.current = 'menu'
        else:
            self.root.ids.id_model.text = ""
            self.root.ids.key_model.text = ""

    # Screen 2
    def show_data(self):
        func = self.subjects_schedule(self.root.ids.textbox.text)
        text = func[2]  # l
        value_schedule = func[3]

        if len(text) > 0:  # If name is not empty do:
            try:
                if self.df:
                    self.df = self.df[0:0]
            except Exception:
                pass
            self.root.current = 'subjects'  # Move to the Screen3
        else:
            self.root.ids.textbox.text = ''
        textbox = self.root.ids.textbox.text
        return textbox, text

    def collect(self):
        func = self.subjects_schedule(self.root.ids.textbox.text)
        df_current = func[1]
        value_schedule = func[3]
        df_1, k_1 = self.page_left()
        # df_1_shape = k_1
        df_2, k_2 = self.page_right()
        # df_2_shape = k_2

        if len(self.root.ids.textbox.text) > 0:
            df_1.loc[0, 'number'] = self.root.ids.textbox.text
        else:
            group_name = self.subjects_schedule(self.root.ids.textbox.text)[0]
            df_1.loc[0, 'number'] = group_name

        df_1.loc[1, 'number'] = value_schedule
        df = df_1.join(df_2)

        list_signature_lecturer = []
        list_signature = []
        subject_index_list = []
        subject_index_schedule = []
        list2 = []
        subject_indexes_schedule_to_df = []
        values_subject = []
        values_not_subject = []
        list_values_number = []
        list_value_sum = []
        values_rows = []
        items_subjects = []

        for count, i in enumerate(df.loc[2][2:26], 2):
            if len(i) > 1:
                value = "Практические занятия"
                df.iloc[2, count] = value
            elif len(i) == 1:
                value = "Лекция"
                df.iloc[2, count] = value
            elif len(i) == 0:
                pass

        for count, i in enumerate(df.loc[38], 0):
            if i:
                if count >= 2:
                    list_signature_lecturer.append(count)
        df.loc[38][list_signature_lecturer] = "Yes"

        for count, i in enumerate(df.loc[39], 0):
            if i:
                if count >= 2:
                    list_signature.append(count)
        df.loc[39][list_signature] = "Yes"

        i = 0
        for j, _ in enumerate(df.loc[1][2:26], 2):
            if j % 4 == 2:
                i += 1
            subject_index_list.append([i, j])

        df.iloc[1:2, 2:26] = ''

        # Index of subjects from schedule to import to df
        for i in df_current['week_n']:
            subject_index_schedule.append(i)

        list1 = list(df_current['week_n'])

        n = 1
        for count, i in enumerate(list1):
            list2.append(n)
            if count + 1 < len(list1):
                if list1[count + 1] == list1[count]:
                    n += 1
                else:
                    n = 1

        items = subject_index_schedule + list2
        items_week_n = items[:len(items) // 2]
        items_number_column = items[len(items) // 2:]

        for i, j in zip(items_week_n, items_number_column):
            if i == 2:
                j += 4
            elif i == 3:
                j += 8
            elif i == 4:
                j += 12
            elif i == 5:
                j += 16
            elif i == 6:
                j += 20
            j += 1  # Because we compare with slice of df from 2 column
            subject_indexes_schedule_to_df.append([i, j])

        for count, (i, j) in enumerate(subject_indexes_schedule_to_df, 0):
            df.loc[1][j] = df_current['subject'][count]

        for count, i in enumerate(df.loc[1][2:26], 2):
            if i:
                values_subject.append(count)
            elif not i:
                values_not_subject.append(count)

        for i in values_not_subject:  # Clear values in all row where is no subject
            df.iloc[:, i] = ''

        # Remove values where is no student
        for count, i in enumerate(df['student'][3:df.shape[0] - 3], 1):
            if not i:
                df.loc[count + 2, 'number'] = ''

        for count, i in enumerate(df['number'][3:37], 1):
            if not i:
                list_values_number.append(count + 2)

        for i in list_values_number:
            df.iloc[i][2:27] = ''

        # Sum values
        for i in values_subject:  # Fill only columns with some subject
            df.iloc[3:37, i:i + 1] = df.iloc[3:37, i:i + 1].apply(
                lambda x: x.str.extract(r'([а-яА-Яa-zA-Z0-9])', expand=False)).replace('None', np.nan).notnull().astype(
                int)
            list_value_sum.append(sum(df.iloc[3:37, i]))

        # Remove values where is no student
        for i in list_values_number:
            df.iloc[i][2:27] = ''

        # Summary by student
        for count, i in enumerate(df['student'][3:37], 3):
            if i:
                values_rows.append(count)

        for i in values_rows:
            k = 0
            for j in df.loc[i][2:26]:
                if j:
                    k += j
            df.loc[i, 'lectures_all'] = k

        summary = 0
        for i in df['lectures_all'][3:df.shape[0] - 3]:
            if i:
                summary += i

        df.loc[37, 'lectures_all'] = summary

        for i in values_subject:
            k = 0
            for j in df.iloc[3:37, i]:
                if j:
                    k += j
                df.loc[37][i] = k

        # Df only: number; student; lectures_all; group_name; week_number
        df_students = df.iloc[1:37, :27]
        df_students.loc[1, 'student'] = "Студент"
        df_students = df_students[df_students["number"] != '']
        df_students = df_students.reset_index(drop=True)

        # Insert 2 values in 2 columns
        df_students.loc[df_students.shape[0], 'number'] = 'total'
        df_students.loc[df_students.shape[0] - 1, 'student'] = 'all'
        df_students = df_students[1:df_students.shape[0] - 1]
        df_students = df_students[["number", "student", "lectures_all"]]
        df_students['group'] = df.loc[0, 'number']
        df_students['week_n'] = df.loc[1, 'number']
        df_students['date'] = date.today()
        df_students = df_students.fillna('')
        df_students = df_students.reset_index(drop=True)

        # Df only: column{i}; group_name; week_number
        for count, i in enumerate(values_subject, 0):
            items_subjects.append(
                {
                    'subject': df.loc[1][i],
                    'total': df.loc[37][i],
                    'group': df.loc[0, 'number'],
                    'week_n': df.loc[1, 'number'],
                    'date': date.today()
                }
            )

        df_subjects = pd.DataFrame(items_subjects)
        df_subjects = df_subjects.groupby(['subject', 'group', 'date', 'week_n'])['total'].sum().reset_index()
        return df, df_students, df_subjects

    # Screen 3
    def file_manager_open(self):
        self.file_manager.show('/')  # Output manager to the screen
        # self.file_manager.show(SD_CARD)  # (CHANGE)
        self.manager_open = True

    def select_path(self, path):
        if self.root.ids.lang.active:
            self.root.ids.file.text = "Html файл: "
            self.root.ids.file1.text = "1 файл: "
            self.root.ids.file2.text = "2 файл: "
        else:
            self.root.ids.file.text = "Html file: "
            self.root.ids.file1.text = "1 file: "
            self.root.ids.file2.text = "2 file: "

        if self.root.current == 'manual_load':
            if not self.list_file_path:
                self.list_file_path.append(path)
            else:
                self.list_file_path.clear()
                self.list_file_path.append(path)

        if self.root.current == 'processing':
            if len(self.list_path) < 2:
                self.list_path.append(path)
            else:
                self.list_path.clear()
                self.list_path.append(path)
        self.exit_manager()

        try:
            self.root.ids.file.text = f"{self.root.ids.file.text}\n{self.list_file_path[0]}"
        except Exception:
            pass

        try:
            self.root.ids.file1.text = f"{self.root.ids.file1.text}\n{self.list_path[0]}"
            self.root.ids.file2.text = f"{self.root.ids.file2.text}\n{self.list_path[1]}"
        except Exception:
            pass
        return self.list_file_path, self.list_path

    def exit_manager(self, *args):
        self.manager_open = False
        self.file_manager.close()

    def events(self, instance, keyboard, keycode, text, modifiers):
        if keyboard in (1001, 27):
            if self.manager_open:
                self.file_manager.back()
        return True

    def callback_button_collect(self):
        # Screen 5
        self.df_students['date'] = pd.to_datetime(self.df_students['date'])
        self.df_subjects['date'] = pd.to_datetime(self.df_subjects['date'])
        pandas_gbq.to_gbq(self.df_students, project_id=self.project_id,
                          destination_table=self.table_id_1, if_exists='append', credentials=self.credentials)
        pandas_gbq.to_gbq(self.df_subjects, project_id=self.project_id,
                          destination_table=self.table_id_2, if_exists='append', credentials=self.credentials)
        self.root.current = 'check'


    def show_table(self):
        self.df, self.df_students, self.df_subjects = self.collect()
        self.list_path.clear()
        if self.df.shape[0] == 40 and self.df.shape[1] == 29:  # Input table (40 rows × 29 columns)
            # Screen 4
            column_data = list(self.df.columns)
            row_data = self.df.to_records(index=False)
            column_data = [(x, dp(75)) if (_ >= 1 and (_ % 26 == 0 or _ % 27 == 0 or _ % 28 == 0)) \
                               else (x, dp(25)) for _, x in enumerate(column_data, 0)]
            if not self.data_tables:
                self.data_tables = MDDataTable(
                    background_color_header=(0, 1, 0, .1),
                    pos_hint={"top": 1, "center_y": 0.5},
                    size_hint_x=1,
                    size_hint_y=None,
                    height=Window.height * 0.9,
                    use_pagination=True,
                    column_data=column_data,
                    row_data=row_data,
                )
                self.root.ids.table_box.add_widget(self.data_tables)
            else:
                self.data_tables.update_row_data(self.data_tables, row_data)
        else:
            self.root.current = 'processing'  # Move to the Screen3

    def uploading(self):
        if self.root.ids.textbox.text == '':
            self.root.current = 'manual_load'
        else:
            self.root.current = 'menu'

    def build(self):
        self.theme_cls.theme_style = "Light"
        self.theme_cls.primary_palette = "Green"
        return Builder.load_file('main.kv')


Student_Digitizer().run()
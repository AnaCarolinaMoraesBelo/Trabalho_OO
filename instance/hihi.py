import pandas as pd
import sqlite3

con = sqlite3.connect("./instance/minhabase.sqlite3")
print (con)
lista_campeons = pd.read_csv('./instance/campeoes_lista_v3.csv', sep=';', encoding='utf8')
print (lista_campeons)
lista_campeons.to_sql('campeoes', con=con, if_exists='append', index=False)
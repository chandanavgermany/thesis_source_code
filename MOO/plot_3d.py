# -*- coding: utf-8 -*-
"""
Created on Sun May 23 10:02:12 2021

@author: Q514347
"""

import matplotlib.pyplot as plt
import pandas as pd


df = pd.read_excel('a_23.xlsx')
df = df[['makespan', 'stock_cost', 'tardiness_cost', 'rank']]
df['color'] = 'x'
df.loc[(df['rank'] == 0), 'color'] = '#800000'
df.loc[~(df['rank'] == 0), 'color'] = '#D3D3D3'

# =============================================================================
# fig = plt.figure()
# ax = fig.add_subplot(111, projection='3d')
# 
# x = df['makespan']
# y = df['stock_cost']
# z = df['tardiness_cost']
# 
# 
# ax.scatter(x, y, z, c='r', marker='o')
# 
# 
# 
# plt.setp(ax.get_xticklabels(), rotation=30)
# plt.setp(ax.get_yticklabels(), rotation=-30)
# plt.setp(ax.get_zticklabels(), rotation=0)
# 
# plt.show()
# =============================================================================

import plotly.express as px

fig = px.scatter(df, x='makespan', y='stock_cost', color='color')
fig.show()
fig.write_image('C:\\Users\\q514347\\Documents\\Thesis Project\\a.png')
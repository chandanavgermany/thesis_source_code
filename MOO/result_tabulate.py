# -*- coding: utf-8 -*-
"""
Created on Mon Mar 29 11:46:07 2021

@author: Q514347
"""

import pandas as pd

def plot_graph(df, param, size, x_label, disruption):
    algorithms = list(df['Algorithm'].unique())
    labels = list(df['Rescheduling Strategy'].unique())
    #labels.pop()
    labels += ['Robust (breakdown outside buffer)']
    hybrid = df.loc[df['Algorithm'] == algorithms[0]]
    nsga = df.loc[df['Algorithm'] == algorithms[1]]
    hybrid_values = [float(i) for i in list(hybrid[param])]
    nsga_values = [float(i) for i in list(nsga[param])]
    result = pd.DataFrame({'Hybrid': hybrid_values, 'NSGA': nsga_values}, index=labels)
    ax = result.plot.barh(title='JSSP - Production performance for ' + size + ' size ' + disruption + ' disruption problem w.r.t '+ x_label, figsize=(25, 10))
    ax.set_xlabel(x_label)
    ax.set_ylabel('Rescheduling Strategies')
    ax.get_figure().savefig('Data/Result_JSSP/_JSSP_'+ size + '_size_' + disruption + '_disruption_' + x_label + '.png')

if __name__ == '__main__':
    df = pd.read_excel('Data/JSSP_result.xlsx')
    df = df.iloc[1:]
    df = df.drop(df.index[[1]])
    df.columns = df.iloc[0]
    df = df[1:]
    
    small_size_df = df.loc[(df['Problem Size'] == 'L') & (df['Time of disruption'] != 'Late') 
                        & (df['Time of disruption'] != 'Late(breakdown outside buffer)')]
    
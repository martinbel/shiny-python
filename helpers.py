import re
from shiny import *
from shinywidgets import output_widget, register_widget, render_widget
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objs as go
import plotly.figure_factory as ff
from datetime import date


def performance(returns):
    """Create a table that summarizes stock performance"""
    monthly_ret = returns.copy()

    # Define Risk Free Rate
    risk_free_rate = 0.04

    # Comulative Returns
    ret_cumulative = (1 + monthly_ret).cumprod()

    # CAGR - Annualied Returns
    annualized_returns = (1 + monthly_ret.mean()) ** 12 - 1

    # Volatility
    annualied_std_deviation = monthly_ret.std() * np.sqrt(12)

    # Drawdown
    previous_peaks = ret_cumulative.cummax()
    drawdown = (ret_cumulative - previous_peaks) / previous_peaks

    # Create Summary Table
    df_risk_return = pd.DataFrame({
        "Annualized Returns": annualized_returns,
        "Annualized Risk": annualied_std_deviation,
        "Max Drawdown": drawdown.min() * -1
    })

    # Compute Sharpe Ratio
    df_risk_return['Sharpe Ratio'] = (
        df_risk_return['Annualized Returns'] - risk_free_rate) / \
        df_risk_return['Annualized Risk']

    # Sort results by sharpe ratio
    df_risk_return.sort_values("Sharpe Ratio", ascending=False)

    return df_risk_return



def plotnine_qqplot(ret):
    x = pd.DataFrame(ret)

    p = (ggplot(aes(sample = x)) +
        stat_qq() +
        stat_qq_line() +
        xlab("Theoretical Quantiles") +
        ggtitle("Q-Q Plot")

    )
    return p


def plotly_qqplot(qqplot_data):
    df_qq = pd.DataFrame({
        'x': qqplot_data[0].get_xdata(),
        'y': qqplot_data[0].get_ydata(),
        'data': "points"
    })

    fig = px.scatter(df_qq, x='x', y='y',
                     trendline='ols')
    fig

    return fig

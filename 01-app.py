from shiny import *
from shinywidgets import output_widget, register_widget, render_widget
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objs as go


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


### Global data
# Read Stock prices data
close_adj = pd.read_parquet("spy_close_adjusted.parquet")


app_ui = ui.page_fluid(
    ui.row(
        ui.column(4,
                  ui.input_select("stocks", "Select Stocks:",
                        choices=list(close_adj.columns),
                        selected=["AAPL", "MSFT", "AMZN"],
                        multiple=True,
                        selectize=True
                        ),
        ),
    ),
    ui.row(
        ui.column(6,
                  ui.h4("Performance Report"),
                  ui.output_table("performance_report")),
        ui.column(6,
                  ui.h4("Risk & Return"),
                  output_widget("scatter_plot"))
    )
)


def server(input, output, session):

    @reactive.Calc
    def compute_returns():
        #stocks = ['AAPL', 'AMZN', 'GOOGL', 'MA', 'MSFT', 'NFLX', 'NVDA']
        stocks = list(input.stocks())

        # 1. Select Stocks
        # 2. Compute Daily Returns
        df_selection = (
            close_adj[stocks]
            .dropna()
            .pct_change()    # Compute daily returns
        ).copy()             # copy resulting DF

        # 3. Resample returns to be monthly
        df_selection = (
            df_selection
            .resample('M')
            .agg(lambda x: (1 + x).prod() - 1)
        )
        df_selection.head()
        # filter dates
        start_date = "2007-01-01"
        end_date = '2020-10-01'

        # Filter start and end dates
        df_selection = df_selection[start_date:end_date]

        perf_summary = performance(df_selection)
        perf_equal_weight = (
            df_selection
            .mean(axis=1)
            .to_frame()
            .pipe(performance)
        )
        perf_equal_weight.index = ['Portfolio']
        perf_long = pd.concat([perf_summary, perf_equal_weight])

        return perf_long


    @output
    @render.table
    def performance_report():
        perf_long = compute_returns()

        perf_report = (perf_long
                       .T.reset_index()
                       .rename(columns={"index": "Metric"})).copy()

        return perf_report


    @output
    @render_widget
    def scatter_plot():
        perf_long = compute_returns()
        perf_long = (perf_long.reset_index()
                     .rename(columns={"index":"ticker"}))

        fig = px.scatter(perf_long,
                        x="Annualized Returns",
                        y="Annualized Risk",
                        text="ticker")

        fig.update_traces(textposition='top center')

        fig.update_layout(
            xaxis=dict(title='Annualized Returns', tickformat=".0%"),
            yaxis=dict(title='Risk', tickformat=".0%"),
            title_text='Annualized Returns & Risk'
        )

        return go.FigureWidget(fig)



app = App(app_ui, server, debug=False)

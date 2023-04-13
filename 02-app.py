# import everything in helpers.py
from helpers import *

### Global data
# We read this file once, when the app starts

# Read Stock prices data
close_adj = pd.read_parquet("spy_close_adjusted.parquet")

### Front-End Code
app_ui = ui.page_navbar(
    ui.nav("Performance", 
        ui.row(
            ui.column(4, 
                    ui.input_date_range(
                        "daterange", "Date Range",
                        start="2006-01-01", 
                        end="2010-01-01")
                    ),
            ui.column(4,
                ui.input_select("stocks", "Select Stocks", 
                                choices=list(close_adj.columns), 
                                selected=["AAPL", "MSFT", "AMZN", 
                                          "ACN", "ADBE"], 
                                multiple=True, 
                                selectize=True
                                )
            ),
        ),
        ui.row(
            ui.column(6, 
                      ui.h4("Risk & Return"),
                      output_widget("scatter_plot")),
            ui.column(6, 
                      ui.h4("Cumulative Return"),
                      output_widget("cumulative_return"))
        ),
        ui.row(
            ui.column(12, 
                      ui.h4("Performance Metrics"),
                      output_widget("performance_report"))
        )
    ),
    ui.nav("Single Stock Analysis",
        ui.row(
            ui.input_select("stock_1d", "Select Stock", 
                        choices=list(close_adj.columns), 
                        selected=["MSFT"], 
                        multiple=False, 
                        selectize=True
                        ),
            ui.input_select("benchmarks", "Select Benchmarks", 
                        choices=["QQQ", "SPY", "TLT", "LQD"], 
                        selected=["SPY", "TLT", "QQQ"], 
                        multiple=True, 
                        selectize=True
                        ),            
        ),
        ui.row(
            ui.column(6, 
                      ui.h4("Monthly Return Distributions"),
                      output_widget("boxplot_benchmarks")),
            ui.column(6, 
                      ui.h4("Cumulative Return"),
                      output_widget("cumulative_returns_benchmarks"))
        )
    ),
    title='Portfolio Analytics',
    bg="#0062cc",
    inverse=True,
    id="navbar_id",
    footer=ui.div(
        {"style": "width:80%;margin: 0 auto"},
        ui.tags.style(
            """
            h4 {
                margin-top: 3em;
            }
            """
    ))
    
)
    

### Server: Back-End Code
def server(input, output, session):
    
    @reactive.Calc
    def filter_prices():
        
        # Date Range input dates
        start_date = input.daterange()[0]
        end_date = input.daterange()[1]

        # Filter start and end dates
        df_selection = close_adj[start_date:end_date]
        
        return df_selection

    
    @reactive.Calc
    def daily_returns():
        # get stocks list
        stocks = list(input.stocks())
        
        # Filtered close prices
        df = filter_prices()
        
        # Compute Daily Returns
        df = (
            df[stocks]  # filter stocks
            .dropna()      
            .pct_change()         # Compute daily returns
        )          
        
        return df
    
    @reactive.Calc
    def monthly_returns():
        # Call reactive function
        df = daily_returns()
        
        # 3. Resample returns to be monthly
        df = (
            df
            .resample('M')
            .agg(lambda x: (1 + x).prod() - 1)
        )
        
        return df

    @reactive.Calc
    def performance_long():
        
        df = monthly_returns()

        perf_summary = performance(df)
        perf_equal_weight = (
            df
            .mean(axis=1)
            .to_frame()
            .pipe(performance)
        )
        perf_equal_weight.index = ['Portfolio']
        perf_long = pd.concat([perf_summary, perf_equal_weight])
        
        return perf_long
    
    @reactive.Calc
    def returns_benchmark():
        # Date Range input dates
        start_date = input.daterange()[0]
        end_date = input.daterange()[1]

        # Filter start and end dates
        df = close_adj[start_date:end_date]
        
        select_tickers = [input.stock_1d()] + list(input.benchmarks())
        
        df = (
            df[select_tickers]    # filter stocks
            .dropna()      
            .pct_change()         # Compute daily returns
            .resample('M')
            .agg(lambda x: (1 + x).prod() - 1)
        )
                
        return df



    ############### Portfolio Performance ##############
    
    @output
    @render_widget
    def performance_report():
        perf_long = performance_long()
        
        perf_long = perf_long.round(4)
        
        df = (perf_long
              .T.reset_index()
              .rename(columns={"index": "Metric"})
              )
        df['Metric'] = ['Return', 'Risk', "Max DD", "Sharpe"]
        
        cols = list(df.columns[1:])
        for col in cols:
            df[col] = (df[col] * 100).round(2).astype(str) + "%"
        
        fig = ff.create_table(df)
       
        return go.FigureWidget(fig)


    @output
    @render_widget
    def scatter_plot():
        perf_long = performance_long()
        perf_long = (perf_long
                     .reset_index()
                     .rename(columns={"index":"ticker"}))
        
        fig = px.scatter(perf_long, 
                        x="Annualized Returns",
                        y="Annualized Risk", 
                        text="ticker")

        fig.update_traces(textposition='top center')

        fig.update_layout(
            xaxis=dict(title='Annualized Returns', 
                       tickformat=".0%"),
            yaxis=dict(title='Risk', tickformat=".0%"),
            title_text=''
        )
        
        return go.FigureWidget(fig)
    
    
    @output
    @render_widget
    def cumulative_return():
        monthly_ret = monthly_returns()
        
        monthly_ret['Portfolio'] = monthly_ret.mean(axis=1)
        
        ret_cumulative = (1 + monthly_ret).cumprod() - 1
        ret_cumulative = (ret_cumulative * 100).round(2)
        
        fig = px.line(ret_cumulative)
        fig.update_traces(hovertemplate=None)
        fig.update_layout(hovermode="x", yaxis_ticksuffix = "%")
        
        return go.FigureWidget(fig)
    
    ############### Benchmarks ##############
    
    @output
    @render_widget
    def boxplot_benchmarks():
        monthly_ret = returns_benchmark()
        
        mdf = (monthly_ret
               .reset_index()
               .melt(id_vars='Date'))
        mdf.columns = ['Date', 'Ticker', "Return"]

        fig = px.box(mdf, x='Ticker', y='Return', color='Ticker')
        
        return go.FigureWidget(fig)
    
    
    @output
    @render_widget
    def cumulative_returns_benchmarks():

        monthly_ret = returns_benchmark()
        
        ret_cumulative = (1 + monthly_ret).cumprod() - 1
        ret_cumulative = (ret_cumulative * 100).round(2)
        
        fig = px.line(ret_cumulative)
        fig.update_traces(hovertemplate=None)
        fig.update_layout(hovermode="x", yaxis_ticksuffix = "%")
        
        return go.FigureWidget(fig)

        


app = App(app_ui, server, debug=False)


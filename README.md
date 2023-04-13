# Shiny for Python - Portfolio Analytics App

## 1. Data Collection

Follow the `Get stocks data.ipynb` notebook to extract close adjusted
price data using the yahoo finance API.

After running the notebook, a file will be saved locally called `spy_close_adjusted.parquet`.
This file has price data of all the S&P 500 components.

## Environment set-up

If you are using anaconda, first activate your environment

```
conda activate envname
pip install -r requirements.txt
```

## 1. First App

This first app explains how to create a first version of the app.
It's covered in this [video tutorial](https://www.youtube.com/watch?v=pCnetgDRRs0).

You can run it using this command from the terminal.
```
conda activate envname
shiny run --reload 01-app.py
```

## 2. Second app
This app is a more complex version that shows how you can build multiple
reactive calculations and easily output results to the user.
It's covered in this [video tutorial](https://www.youtube.com/watch?v=Zil-UQOegdA).

You can run it using this command from the terminal.
```
conda activate envname
shiny run --reload 02-app.py
```

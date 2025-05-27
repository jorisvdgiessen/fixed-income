# imports
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.optimize import fsolve
import pandas_market_calendars as mcal
from datetime import datetime as dt
from datetime import timedelta 
import math

VALUATION_DATE = dt(year=2025, month=5, day=7)
DAY_CONVENTION = 'ACT/ACT' 

# MARKETS CALENDAR
target = mcal.get_calendar("EUREX")
target_days = target.schedule(start_date=VALUATION_DATE, end_date='2100-01-01')
target_days = target_days.index
target_days = list(target_days.to_pydatetime())

def tau(start_date: dt, end_date: dt, day_count_convention: str='ACT/ACT') -> float:
    """ Function to compute time as yearly fraction based on specific day count convention """
    # general check if end date greater or equal than start date
    if start_date > end_date:
        print("start date and end date are switched")

    year1 = int(start_date.year)
    year2 = int(end_date.year)

    # same year calculations 
    if year1==year2: 
        days_in_year = 366 if is_leap_year(year1) else 365
        return( (end_date - start_date).days / days_in_year )

    # multiple year calculations
    else: 
        # first fraction year 
        end_of_year1 = dt((year1 + 1), 1, 1)
        days_in_year1 = 366 if is_leap_year(year1) else 365
        frac1 = (end_of_year1 - start_date).days / days_in_year1
    
        # last fraction year
        start_of_year2 = dt(year2, 1, 1)
        days_in_year2 = 366 if is_leap_year(year2) else 365
        frac2 = (end_date - start_of_year2).days / days_in_year2

        # full years in between
        full_years = year2 - year1 - 1

        return( frac1 + full_years + frac2 )
    


def is_leap_year(year: int) -> bool:
    "function to determine if a year is a leap year"
    leap_year = year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)
    return leap_year


def next_business_day(figure_date: dt, business_days: list) -> dt:
    """ Checks if date is a business day, if not, retrieves first business day after (based on business days list) """
    # if already a business day
    if figure_date in business_days:
        return figure_date

    # if not a business day
    else:
        for current_control_date in business_days:
            if current_control_date > figure_date:
                return current_control_date
            
        # if figure date after last day in business days list
        return None
    

def plus_one_business_day(figure_date: dt, business_days: list) -> dt:
    """ Retrieves t+1 business day """
    # if figure date not a business day
    if figure_date not in business_days:
        current_date = next_business_day(figure_date=figure_date, business_days=business_days)
    else:
        current_date = figure_date

    figure_date_plus_one_day = current_date + timedelta(days=1)
    figure_date_plus_one_business_day = next_business_day(figure_date=figure_date_plus_one_day, business_days=business_days)

    return figure_date_plus_one_business_day


# DEPENDENCIES: 
"""
from datetime import datetime as dt
import pandas as pd
import pandas_market_calendars as mcal

"""
class Bond:
    def __init__(self, description: str, ticker: str, issue_date: dt, maturity_date: dt, 
                 price: float, coupon_rate: float, coupon_frequency: int = 1, 
                 day_count_convention: str = 'ACT/ACT', face_value: float = 100.0, currency: str = "EUR",
                 business_days: list = None):
        
        self._description = description
        self._ticker = ticker
        self._issue_date = issue_date
        self._maturity_date = maturity_date
        self._coupon_rate = coupon_rate
        self._coupon_frequency = coupon_frequency
        self._price = price
        self._day_count_convention = day_count_convention
        self._face_value = face_value
        self._currency = currency

        if business_days is None:
            target = mcal.get_calendar("EUREX")
            target_days = target.schedule(start_date=VALUATION_DATE, end_date='2100-01-01')
            target_days = target_days.index
            target_days = list(target_days.to_pydatetime())
            self._business_days = target_days
        else: 
            self._business_days = business_days

    # Getter methods
    def get_description(self) -> str:
        return self._description

    def get_ticker(self) -> str:
        return self._ticker

    def get_issue_date(self) -> dt:
        return self._issue_date

    def get_maturity_date(self) -> dt:
        return self._maturity_date

    def get_coupon_rate(self) -> float:
        return self._coupon_rate

    def get_coupon_frequency(self) -> int:
        return self._coupon_frequency

    def get_price(self) -> float:
        return self._price

    def get_day_count_convention(self) -> str:
        return self._day_count_convention

    def get_face_value(self) -> float:
        return self._face_value

    def get_currency(self) -> str:
        return self._currency

    def __str__(self):
        return f"{self._description} ({self._ticker}) - Matures on {self._maturity_date.date()}, Coupon: {self._coupon_rate*100:.2f}%"
    

    def get_summary(self) -> str:
        return (
            f"Bond Summary:\n"
            f"-----------------------------------------------------\n"
            f"Description:          {self.get_description()}\n"
            f"Ticker:               {self.get_ticker()}\n"
            f"Issue Date:           {self.get_issue_date()}\n"
            f"Maturity Date:        {self.get_maturity_date().date()}\n"
            f"Coupon Rate:          {self.get_coupon_rate()*100:.2f}%\n"
            f"Frequency:            {self.get_coupon_frequency()} times/year\n"
            f"Price:                {self.get_price()} {self.get_currency()}\n"
            f"Face Value:           {self.get_face_value()} {self.get_currency()}\n"
            f"Day Count:            {self.get_day_count_convention()}"
        )

    # Payment dates of bond
    def get_payment_dates(self, figure_date: dt) -> list:
        """ Retrieves coupon payment dates (business days) for coupon paying bond """
        payment_month = self._maturity_date.month 
        payment_day = self._maturity_date.day
        first_year = figure_date.year

        # next coupon date
        if (figure_date > dt(first_year, payment_month, payment_day)):
            first_year += 1
            next_coupon_date = dt((first_year), payment_month, payment_day)

        else:
            next_coupon_date = dt(first_year, payment_month, payment_day)

        first_payment_date = next_business_day(figure_date=next_coupon_date, business_days=self._business_days)
        payment_dates = []
        payment_dates.append(first_payment_date)

        n = self._maturity_date.year  - first_year
        current_year = first_year

        for _ in range(n):
            current_year += 1 
            current_coupon_date = dt(current_year, payment_month, payment_day)
            current_payment_date = next_business_day(figure_date=current_coupon_date, business_days=self._business_days)
            payment_dates.append(current_payment_date)

        return( payment_dates )


    # Bond Cashflows
    def get_cashflows(self, figure_date: dt) -> list:
        """ Retrieves cashflows of an annual coupon paying bond """
        payment_dates = self.get_payment_dates(figure_date=figure_date)
        coupon_payment = self._coupon_rate * self._face_value
        cashflows = []

        for current_date in payment_dates:
            maturity_business_day = next_business_day(figure_date=self._maturity_date, business_days=self._business_days)
            if current_date==maturity_business_day:
                cashflows.append(coupon_payment + self._face_value)
            else:
                cashflows.append(coupon_payment)

        return( cashflows )


    def get_cashflow_df(self, figure_date: dt) -> pd.DataFrame:
        """ Retrieves cashflows, timing, and payment dates for annual coupon paying bond """
        payment_dates = self.get_payment_dates(figure_date=figure_date)
        cashflows = self.get_cashflows(figure_date=figure_date)
        cashflow_table = pd.DataFrame()
        cashflow_table['payment_date'] = payment_dates
        cashflow_table['cashflow'] = cashflows
        cashflow_table['time_to_figure_date'] = cashflow_table['payment_date'].apply(lambda x: tau(start_date=figure_date, end_date=x, day_count_convention=self._day_count_convention)) 
        cashflow_table['time_between_cashflows'] = cashflow_table['time_to_figure_date'] - cashflow_table['time_to_figure_date'].shift(1)
        cashflow_table.loc[0, 'time_between_cashflows'] = cashflow_table.loc[0, 'time_to_figure_date']
        
        return( cashflow_table )
    

    # Function to retrieve the bond yield implied by market price
    def get_yield(self, figure_date: dt) -> float:
        """ retrieve the bond yield implied by market price for annual coupon paying bond """
        cashflow_table = self.get_cashflow_df(figure_date=figure_date)

        def func_to_solve(_yield):
            npv = 0

            for idx in cashflow_table.index:
                cashflow = cashflow_table.loc[idx, 'cashflow']
                time = cashflow_table.loc[idx, 'time_to_figure_date']

                npv +=  cashflow * ( 1 / (1 + _yield)**time )

            return( self._price - npv )
        
        res = fsolve(func=func_to_solve, x0=0.03)
        return res[0]



    def get_present_value(self, figure_date: dt) -> float:

        cashflow_table = self.get_cashflow_df(figure_date=figure_date)

        # TEMPORARY UNTIL GOOD METHOD FOR DISCOUNT FACTORS
        cashflow_table['discount_factor'] = 1 
        
        npv = 0
        for idx in cashflow_table.index:
            npv += cashflow_table.loc[idx, 'cashflow'] * cashflow_table.loc[idx, 'discount_factor']

        return npv


# Create our bond universe
file_path = "C:/Users/joris/OneDrive/Documenten/GitHub/fixed-income/static_dsl_curve_snippet.xlsx"

dsl_df = pd.read_excel(file_path, index_col=0, header=0)
dsl_df['Maturity'] = pd.to_datetime(dsl_df['Maturity'])
dsl_df = dsl_df.sort_values(by='Maturity')

bond_dict = {}

for bond_id in dsl_df.index:
    bond_dict[bond_id] = Bond(description=dsl_df.loc[bond_id, 'Bond'],
                              ticker=dsl_df.loc[bond_id, 'Ticker'],
                              coupon_rate=dsl_df.loc[bond_id, 'Coupon']/100,
                              issue_date=dsl_df.loc[bond_id, 'Issue Date'],
                              maturity_date=dsl_df.loc[bond_id, 'Maturity'],
                              price=dsl_df.loc[bond_id, 'Mid (price)'],
                              business_days=target_days)
    

    print(bond_dict[bond_id].get_summary())
    

    


# Import Libraries

from bs4 import BeautifulSoup
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.common.by import By
import time
import pandas as pd

from code.chromedriver import chrome_driver


class PyScraper:
    # Global attributes: website link, driver object, path to data.csv, and dataframe
    global link
    global driver
    global data_path
    global df

    def __init__(self, url, path):

        print('Initializing the scraper.')

        # Initiate the driver

        link = url
        self.driver = chrome_driver(link)
        self.data_path = path

        # Load web elements into BeautifulSoup

        html = self.driver.page_source
        soup = BeautifulSoup(html, 'html.parser')

        # Get dataframe from csv in data_path
        self.df = pd.read_csv(self.data_path)

    def get_df(self):
        return self.df

    def extract_column(self, col_name):
        """A function to extract the items in a specified column in the data.

        Parameters
        ----------
        col_name : str
            The name of the column from which to extract the items

        :returns list
        """

        col_elems = self.df[col_name].values.tolist()
        return col_elems

    @staticmethod
    def parse_cities(entries):
        """A function to parse the city name from the longer entry in the corresponding column.
        For example, in the dataset Boston is listed as 'Boston, MASSACHUSETTS, US'; In the ICAO drop-down,
        Boston is listed as 'BOSTON, UNST (BOS )'. In both cases, this function returns just 'Boston'.

        Parameters
        ----------
        entries : list
            The list of entries from which to extract only each city name

        :returns list
        """

        cities = []

        for location in entries:              # For each location in the entire list of entries,
            location = str(location)          # ensure it's a string,

            if '/' in location:
                index = location.find('/')    # bug with 'Minneapolis/St Paul', so need the index of / instead of ,
            else:
                index = location.find(',')    # find the index of the first comma,

            cities.append(location[0:index])  # and append the substring containing the city name to the list

        return cities

    @staticmethod
    def parse_airports(entries):
        """A function to parse the airport code from the longer entry in each ICAO drop-down menu item. For example, in
        the ICAO drop-down, BOSTON is listed as 'BOSTON, UNST (BOS )'. In this case, this function returns just 'BOS'

        Parameters
        ----------
        entries : list
            The list of entries from which to extract each airport code

        :returns list
        """

        codes = []

        for option in entries:
            option = str(option)
            start = option.find('(') + 1
            end = option.find(')') - 1

            codes.append(option[start:end])

        return codes

    def set_trip_type(self, xpath, type):
        """A function to set and click the correct trip type in the calculator.

        Parameters
        ----------
        xpath : str
            The XPATH of the trip type drop-down menu
        type : str
            The desired trip type

        :returns None
        """

        select = Select(self.driver.find_element_by_xpath(xpath))
        select.select_by_visible_text(type)
        time.sleep(2)  # Selenium runs very quickly, website can't always load elements in time

    def set_cabin_class(self, xpath, cat):
        """A function to set and click the correct cabin class in the calculator.

        Parameters
        ----------
        xpath : str
            The XPATH of the cabin class drop-down menu
        cat : str
            The desired cabin class category, ie. Economy or Premium

        :returns None
        """

        select = Select(self.driver.find_element_by_xpath(xpath))
        select.select_by_visible_text(cat)
        time.sleep(2)

    def match(self, city, airport, items):
        """A function to match the given city to the correct option in the drop-down menu.

        Parameters
        ----------
        city : str
            The full name of the city, eg. Boston
        airport : str
            The airport code
        items : list
            The options in the drop-down menu; index starts from 1

        :returns int
        """

        items_str = []
        for item in items:
            items_str.append(item.text)

        if len(items_str) == 1:
            return 1
        else:
            city_to_match = self.parse_cities(items_str)       # extract just the cities from each row in the menu
            airport_to_match = self.parse_airports(items_str)  # extract just the airport codes ""

            for i in range(len(city_to_match)):
                if city_to_match[i] == city.upper() or airport_to_match[i] == airport:
                    return i + 1  # web menu lists start from index 1

    def send(self, name, airport, city, xpath, tag_name):
        """A function to send airport info to the online ICAO calculator.

        Parameters
        ----------
        name : str
            The input to the driver, eg. 'frm1' for departure
        airport : str
            The airport code, eg. BOS
        city : str
            The city corresponding to the airport code
        xpath : str
            The XPATH of the drop-down menu
        tag_name : str

        :returns None
        """

        input_to_send = self.driver.find_element_by_name(name)
        input_to_send.send_keys(airport)
        time.sleep(5)

        click_wait = WebDriverWait(self.driver, 15).until(ec.visibility_of_element_located((By.XPATH, xpath)))
        menu_items = click_wait.find_elements_by_tag_name(tag_name)  # list of drop-down menu options

        # Click the correct option, using the match() helper function

        index = self.match(city, airport, menu_items)
        element = WebDriverWait(self.driver, 15).until(
            ec.element_to_be_clickable((By.XPATH, xpath + "/" + tag_name + "[" + str(index) + "]")))
        element.click()

    def compute(self):
        """A function to have the ICAO calculator compute the emissions.

        :returns None
        """

        compute_id = "computeByInput"
        button = self.driver.find_element_by_id(compute_id)
        button.click()

    def extract_from_table(self, xpath, tag_name):
        """A function to extract the emissions figures from the ICAO calculator table.

        Parameters
        ----------
        xpath : str
            The XPATH of the table
        tag_name : str

        :returns list
        """

        time.sleep(5)

        table = self.driver.find_elements_by_xpath(xpath)

        for row in table:
            tds = row.find_elements_by_tag_name(tag_name)
            table_results = [td.text for td in tds]

        return table_results

    def append_to_csv(self, new_val, row, col, dest_file):
        """A function to add a value to a csv file in the specified row and column.

        Parameters
        ----------
        new_val : int
            The new value to append in the correct column and row
        row, col : int
            The row and column in which to insert the new value
        dest_file : str
            The path to the file to which to write the results

        :returns str
        """

        self.df.at[row, col] = new_val
        self.df.to_csv(dest_file, index=False)

    def clear_inputs(self, name):
        """A function to clear the inputs on the page, so that the next iteration can be entered.

        Parameters
        ----------
        name : str
            The name of the input to clear

        :returns None
        """

        input_to_clear = self.driver.find_element_by_name(name)
        input_to_clear.clear()

    def quit(self):
        """A function to shut down the chrome driver and close Chrome.

        :returns None
        """

        print('Shutting down the driver and closing the Chrome window.')
        self.driver.quit()






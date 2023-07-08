""" 
 Program testing the peace-disarray trading strategy. 
 """ 
  
 from __future__ import annotations 
  
  
 from typing import Callable, Any, Final, final, NoReturn 
  
 import plotly.graph_objects as go 
 import numpy as np 
  
 import binance.client 
 import binance.exceptions 
 import binance.enums 
 import requests 
 import datetime 
 import numbers 
 import concurrent.futures 
 import json 
 import functools 
 import time 
 import random 
  
  
 class ExceptionHandling: 
  
     """ 
     A helper class for handling exceptions related to the Binance API. 
  
     This class includes a static method to wait until the next minute and a class method for general exception handling. 
     It also defines a custom exception `IncorrectIPError` for IP-related issues during API access. 
  
     Attributes: 
             WEIGHT_EXCEEDED_CODE (int): Error code: the weight limit is exceeded 
             NO_PERMISSIONS_CODE (int): Error code: no permissions for getting the data from a specific method 
             INVALID_SYMBOL_CODE (int): Error Code: symbol does not exist on this market for the chosen time 
  
     Methods: 
         general_exception(api_related_callable, *args, **kwargs) -> Any 
         wait_till_the_next_minute() -> None 
  
     Exception Classes: 
         IncorrectIPError: Raised when there is a problem with the IP-related permissions for API access. 
     """ 
  
     # Error codes: 
  
     WEIGHT_EXCEEDED_CODE: Final[int] = -1003 
     NO_PERMISSIONS_CODE: Final[int] = -2015 
     INVALID_SYMBOL_CODE: Final[int] = -1121 
  
     class IncorrectIPError(Exception): 
  
         """ 
         Custom exception for issues related to IP permissions during API access. 
  
         This class extends the built-in `Exception` class and defines a default message and a method to get the current 
         public IP address using the IPIFY API. 
  
         Attributes: 
             DEFAULT_MESSAGE (str): Default error message. 
             IPIFY_API (str): URL for the IPIFY API. 
             __message (str): Message for the exception. 
  
         Methods: 
             message(self) -> str: Getter for the self.__message attribute. 
         """ 
  
         DEFAULT_MESSAGE: Final[str] = ( 
             "Please change your connection IP due to no permissions to get data using the current public IP address." 
         ) 
  
         IPIFY_API: Final[str] = "https://api.ipify.org" 
  
         def __init__(self, message=DEFAULT_MESSAGE): 
  
             if message == self.DEFAULT_MESSAGE: 
                 self.__message: str = message + f" Your current public IP address: {requests.get(self.IPIFY_API).text}" 
             else: 
                 self.__message: str = message 
  
             super().__init__(self.message) 
  
         @property 
         def message(self) -> str: 
  
             """ 
             Getter for the self.__message attribute 
  
             Returns: 
                 str: self.__message attribute value 
             """ 
  
             return self.__message 
  
     class InvalidSymbolError(Exception): 
  
         """ 
         Custom exception for issues related to symbol existence during API access. 
  
         This class extends the built-in `Exception` class and defines a default message with the information about the 
         chosen invalid symbol. 
  
         Attributes: 
             DEFAULT_MESSAGE (str): Default error message. 
             __message (str): Message for the exception. 
  
         Methods: 
             message(self) -> str: Getter for the self.__message attribute. 
         """ 
  
         DEFAULT_MESSAGE: Final[str] = ( 
             "The information about the chosen symbol could not be obtained. Please check the name of the symbol." 
         ) 
  
         def __init__(self, message: str = DEFAULT_MESSAGE, symbol: str | None = None) -> None: 
  
             if symbol is not None: 
                 self.__message: str = message + f" Tried to use the following symbol: {symbol}." 
             else: 
                 self.__message: str = message 
  
             super().__init__(self.message) 
  
         @property 
         def message(self) -> str: 
  
             """ 
             Getter for the self.__message attribute 
  
             Returns: 
                 str: self.__message attribute value 
             """ 
  
             return self.__message 
  
     @classmethod 
     def general_exception(cls, api_related_callable: Callable[..., Any], *args, **kwargs) -> Any: 
  
         """ 
         Handles exceptions related to the Binance API. 
  
         When exceptions related to the Binance API occur, the method waits until the next minute if necessary. 
         If the API weight limit is exceeded, it waits until the next minute to avoid IP banning. 
  
         Args: 
             api_related_callable (Callable[..., Any]): Callable that might throw an exception. 
             *args: Variable length argument list for the callable. 
             **kwargs: Arbitrary keyword arguments for the callable. 
  
         Returns: 
             Any: The same object that the api_related_callable would return. 
  
         Raises: 
             TypeError: If api_related_callable is not a callable object. 
         """ 
  
         if isinstance(api_related_callable, Callable): 
             while True: 
                 try: 
                     return api_related_callable(*args, **kwargs) 
                 except binance.exceptions.BinanceAPIException as binance_api_exception: 
                     match json.loads(binance_api_exception.args[2])["code"]: 
                         case cls.WEIGHT_EXCEEDED_CODE: 
                             cls.wait_till_the_next_minute() 
                         case cls.NO_PERMISSIONS_CODE: 
                             raise cls.IncorrectIPError() 
                         case cls.INVALID_SYMBOL_CODE: 
                             raise cls.InvalidSymbolError( 
                                 symbol=kwargs['symbol'] 
                             ) 
                         case _: 
                             raise Exception(f"Unknown BinanceAPIException:\n{binance_api_exception}") 
                 except (requests.exceptions.ConnectionError, requests.exceptions.ReadTimeout): 
                     continue 
         else: 
             raise TypeError(f"api_related_callable should match the following type: {Callable.__name__}. " 
                             f"{type(api_related_callable).__name__} given instead.") 
  
     @staticmethod 
     def wait_till_the_next_minute() -> None: 
  
         """ 
         Suspends execution until the next minute begins. 
  
         Used when the Binance API weight limit is exceeded. It suspends the program to avoid IP ban 
         and waits until the next minute (when the weight limit resets). 
         """ 
  
         while datetime.datetime.now().second not in range(1, 5): 
             continue 
         else: 
             return 
  
  
 class BinanceData: 
  
     """ 
     Class for retrieving market data from Binance. 
  
     This class defines methods to interact with Binance market data using the Binance API. It requires API key and 
     secret key for initialization and provides methods to retrieve current positions, symbols and klines data. 
  
     Methods: 
         client(self) -> binance.client.Client: Getter for the client attribute. 
         current_positions_symbols(self) -> list[str]: Gets the symbols of currently open positions. 
         download_klines(self, symbol: str, interval: str = '1m', start_str: str = None, end_str: str = None, 
                         klines_type: binance.enums.HistoricalKlinesType = binance.enums.HistoricalKlinesType.FUTURES) 
                         -> list[list[int | str]]: Downloads the klines data for a given symbol. 
  
     Attributes: 
         API_KEY (str): default API_KEY when no key is passed 
         SECRET_KEY (str): default API_SECRET when no key is passed 
  
     Constructor Args: 
         api_key (str): The api_key of the account. 
         secret_key (str): The secret_key of the account. 
  
     Exception classes: 
         NoUserDefinedError: raised if the call to the API callable has been made but no correct user credentials were 
         given. 
     """ 
  
     API_KEY: Final[str] = '<api_key>' 
     SECRET_KEY: Final[str] = '<secret_key>' 
  
     class NoUserDefinedError(Exception): 
  
         """ 
         Custom exception raised if the call to the API callable has been made but no correct user credentials were 
         given. 
  
         Attributes: 
             MESSAGE (str): The message shown when no other message is specified. Clarifies what the cause of the 
             exception is. 
  
         Methods: 
             message -> str: The getter for the __message attribute. 
         """ 
  
         MESSAGE: Final[str] = "There is no user defined with the following keys. The default keys were passed." 
  
         def __init__(self, message: str = MESSAGE) -> None: 
             self.__message: Final[str] = message 
             super().__init__(self.message) 
  
         @property 
         def message(self) -> str: 
  
             """ 
             Getter for the self.__message attribute 
  
             Returns: 
                 str: the self.__message attribute value 
             """ 
  
             return self.__message 
  
     def __init__(self, api_key: str = API_KEY, secret_key: str = SECRET_KEY) -> None: 
  
         """ 
         Constructor used for downloading the market data for the given client based on the passed API Key and 
         Secret Key. 
  
         Args: 
             api_key (str): the api_key of the given account. '<api_key>' by default. 
             secret_key (str): the secret_key of the given account. '<secret_key>' by default. 
  
         Raises: 
             TypeError: If the type of at least one of the given keys is not a string. 
  
         Notes: 
             This method uses ExceptionHandling.general_exception class method for handling the API endpoints. 
         """ 
  
         if isinstance(api_key, str): 
             pass 
         else: 
             raise TypeError(f"api_key type should match {str.__name__}. {type(api_key).__name__} given instead.") 
  
         if isinstance(secret_key, str): 
             self.__client: Final[binance.client.Client] = ExceptionHandling.general_exception( 
                 binance.client.Client, 
                 api_key=api_key, 
                 api_secret=secret_key 
             ) 
         else: 
             raise TypeError(f"secret_key type should match {str.__name__}. {type(secret_key).__name__} given instead.") 
  
     @property 
     def client(self) -> binance.client.Client: 
  
         """ 
         Getter for the self.__client attribute 
  
         Returns: 
             self.__client (binance.client.Client): the client 
         """ 
  
         return self.__client 
  
     def current_positions_symbols(self) -> list[str]: 
  
         """ 
         Method used for getting the symbols of the currently open positions. 
  
         Returns: 
             list[str]: Returns the list of the symbols represented as strings 
  
         Raises: 
             self.NoUserDefinedError: if the given key(s) match the default one(s), not the user one(s). 
  
         Notes: 
             This method uses ExceptionHandling.general_exception class method for handling the API endpoints. 
         """ 
  
         if self.client.API_KEY == self.API_KEY or self.client.API_SECRET == self.SECRET_KEY: 
             raise self.NoUserDefinedError() 
  
         return [ 
             position['symbol'] for position in ExceptionHandling.general_exception( 
                 self.client.futures_position_information 
             ) if float(position['positionAmt']) 
         ] 
  
     def download_klines(self, symbol: str, interval: str = '1m', start_str: str = None, end_str: str = None, 
                         klines_type: binance.enums.HistoricalKlinesType = binance.enums.HistoricalKlinesType.FUTURES 
                         ) -> list[list[int | str]]: 
  
         """ 
         Method used for downloading the klines data for the given symbols. It downloads all the klines information about 
         the given symbol from the Binance Futures market. 
  
         Args: 
             symbol (str): symbol for which the data is about to be downloaded 
             interval (str): the interval of the downloaded klines. 1-minute by default 
             start_str (str): the start date for the data download expressed as a string. Latest downloaded by default. 
             end_str (str): the end date for the data download expressed as a string. Latest downloaded by default. 
             klines_type (binance.enums.HistoricalKlinesType): the market of the downloaded klines. Futures chosen by 
             default. 
  
         Returns: 
             list[list[int | str]]: The data downloaded from the market containing the information about all the 
             downloaded klines. The structure of the downloaded data: 
             [[open_time, open, high, low, close, ...], ...] 
  
         Raises: 
             TypeError: If the type of at least one of the given arguments does not match the correct one 
  
         Notes: 
             This method uses ExceptionHandling.general_exception class method for handling the API endpoints. 
         """ 
  
         if isinstance(symbol, str): 
             pass 
         else: 
             raise TypeError(f"symbol type should match {str.__name__}. {type(symbol).__name__} given instead.") 
  
         if isinstance(interval, str): 
             pass 
         else: 
             raise TypeError(f"interval type should match {str.__name__}. {type(interval).__name__} given instead.") 
  
         if isinstance(start_str, str) or start_str is None: 
             pass 
         else: 
             raise TypeError(f"start_str type should match {str.__name__} or be None." 
                             f"{type(start_str).__name__} given instead.") 
  
         if isinstance(end_str, str) or end_str is None: 
             pass 
         else: 
             raise TypeError(f"end_str type should match {str.__name__} or be None." 
                             f"{type(end_str).__name__} given instead.") 
  
         if isinstance(klines_type, binance.enums.HistoricalKlinesType): 
             return ExceptionHandling.general_exception( 
                 self.client.get_historical_klines, 
                 symbol=symbol, 
                 interval=interval, 
                 start_str=start_str, 
                 end_str=end_str, 
                 klines_type=klines_type 
             ) 
         else: 
             raise TypeError(f"klines_type type should match {binance.enums.HistoricalKlinesType.__name__}. " 
                             f"{type(klines_type).__name__} given instead.") 
  
     @staticmethod 
     def get_prices_of_klines_data(klines_data: list[list[int | str]], position_of_price_in_kline: int = 4 
                                   ) -> list[float]: 
  
         """ 
         Static method used for preprocessing of the downloaded data to transform it to analyzable set of data. 
  
         Args: 
             klines_data (list[list[int | str]]): downloaded klines for the specified symbol 
             position_of_price_in_kline (int): specifies which price is taken to the return list. The following formats 
             are accepted: 1, 2, 3, 4, where: 1 - open, 2 - high, 3 - low, 4 - close price. 4 by default (close price). 
  
         Returns: 
             list[float]: returns the list of the (close) prices expressed as float values 
  
         """ 
  
         return [float(kline[position_of_price_in_kline]) for kline in klines_data] 
  
  
 class LinearRegression: 
  
     """ 
     Class used for linear regression calculations. 
     """ 
  
     def __init__(self, data_dict: dict[numbers.Real, numbers.Real]) -> None: 
  
         """ 
         Constructor for LinearRegression. 
  
         Args: 
             data_dict (dict[numbers.Real, numbers.Real]): A dictionary with keys as arguments and values as values of 
             the function. 
  
         Raises: 
             TypeError: If the argument is not a proper dictionary or contains invalid types. 
         """ 
  
         if isinstance(data_dict, dict): 
             pass 
         else: 
             raise TypeError(f"data_dict type should be {dict.__name__}. {type(data_dict).__name__} given instead.") 
  
         if all(isinstance(argument, numbers.Real) for argument in data_dict.keys()): 
             pass 
         else: 
             for argument in data_dict.keys(): 
                 if not isinstance(argument, numbers.Real): 
                     raise TypeError(f"Each argument of the function should be of type {numbers.Real.__name__}. " 
                                     f"At least one element's type is {type(argument).__name__}.") 
  
         if all(isinstance(value, numbers.Real) for value in data_dict.values()): 
             pass 
         else: 
             for value in data_dict.values(): 
                 if not isinstance(value, numbers.Real): 
                     raise TypeError(f"Each value of the function should be of type {numbers.Real.__name__}. " 
                                     f"At least one element's type is {type(value).__name__}.") 
  
         self.__x: Final[np.ndarray[numbers.Real]] = np.array(list(data_dict.keys())) 
         self.__y: Final[np.ndarray[numbers.Real]] = np.array(list(data_dict.values())) 
  
         self.__n: Final[int] = np.size(self.x) 
  
         self.__mean_x: Final[np.float64] = np.mean(self.x) 
         self.__mean_y: Final[np.float64] = np.mean(self.y) 
  
         self.__a: Final[float] = self.coefficient('a') 
  
     @property 
     def x(self) -> np.ndarray[numbers.Real]: 
  
         """ 
         Getter for the self.__x attribute 
  
         Returns: 
             np.ndarray[numbers.Real]: value of the self.__x attribute 
         """ 
  
         return self.__x 
  
     @property 
     def y(self) -> np.ndarray[numbers.Real]: 
  
         """ 
         Getter for the self.__y attribute 
  
         Returns: 
             np.ndarray[numbers.Real]: value of the self.__y attribute 
         """ 
  
         return self.__y 
  
     @property 
     def n(self) -> int: 
  
         """ 
         Getter for the self.__n attribute 
  
         Returns: 
             int: value of the self.__n attribute 
         """ 
  
         return self.__n 
  
     @property 
     def mean_x(self) -> np.float64: 
  
         """ 
         Getter for the self.__mean_x attribute 
  
         Returns: 
             np.float64: value of the self.__mean_x attribute 
         """ 
  
         return self.__mean_x 
  
     @property 
     def mean_y(self) -> np.float64: 
  
         """ 
         Getter for the self.__mean_y attribute 
  
         Returns: 
             np.float64: value of the self.__mean_y attribute 
         """ 
  
         return self.__mean_y 
  
     @property 
     def a(self) -> float: 
  
         """ 
         Getter for the self.__a attribute 
  
         Returns: 
             float: value of the self.__a attribute 
         """ 
  
         return self.__a 
  
     def coefficient(self, coefficient: str | None = None) -> float | dict[str, float]: 
  
         """ 
         Method for getting the coefficients. 
  
         Args: 
             coefficient (str | None): The coefficient to return. If not specified, both 'a' and 'b' are returned. 
  
         Returns: 
             float | dict[str, float]: Single coefficient value or a dictionary of coefficients based on the given 
             argument. 
  
         Raises: 
             ValueError: If an incorrect coefficient is passed as an argument. 
         """ 
  
         if coefficient is None: 
             return {'a': self.__coefficient('a'), 'b': self.__coefficient('b')} 
         elif coefficient.lower() in ('a', 'b'): 
             return self.__coefficient(coefficient.lower()) 
         elif coefficient.lower() == 'ab': 
             return self.__coefficient('a') + self.__coefficient('b') 
         else: 
             raise ValueError("Unsupported coefficient. Either 'a' (or 'A') or 'b' (or 'B') should be passed.") 
  
     @functools.singledispatchmethod 
     def __coefficient(self, coefficient: str | None = None) -> NoReturn: 
  
         """ 
         Generic method called when an inappropriate argument is passed to the private __coefficient method. 
  
         Args: 
             coefficient (str | None): The coefficient to be returned. None by default (both are returned). 
  
         Raises: 
             NotImplementedError: If the given coefficient does not match one of the following: 'a' or 'b'. 
         """ 
  
         raise NotImplementedError(f"Unsupported coefficient. Either 'a' or 'b' should be passed. " 
                                   f"{coefficient} given instead.") 
  
     @__coefficient.register(str) 
     def _(self, coefficient: str) -> float: 
  
         """ 
         Method that returns the 'a' or 'b' coefficient of the linear regression equation. 
  
         Args: 
             coefficient (str): The coefficient to be returned ('a' or 'b'). 
  
         Returns: 
             float: The value of the specified coefficient. 
  
         Raises: 
             ValueError: If an incorrect coefficient is passed as an argument. 
         """ 
  
         match coefficient: 
             case 'a': 
                 return ( 
                     np.sum(self.y * self.x) - self.n * self.mean_y * self.mean_x 
                 ) / ( 
                     np.sum(self.x * self.x) - self.n * self.mean_x * self.mean_x 
                 ) 
             case 'b': 
                 return self.mean_y - self.a * self.mean_x 
             case _: 
                 raise ValueError("Unsupported coefficient. Either 'a' or 'b' should be passed.") 
  
  
 class ValuesPlotter: 
  
     """ 
     Class used to create a plot using given list of real values. 
  
     This class defines a constructor to create a plot using the list or tuple of real numbers passed as argument. 
     Plotly is used to plot these values, and an HTML file is created for the plot. 
  
     Constructor Args: 
         values (list[numbers.Real] | tuple[numbers.Real, ...]): A list or tuple of real numbers for plotting. 
         title (str): Title for the plot. Default is 'Plot'. 
     """ 
  
     def __new__(cls, values: list[numbers.Real] | tuple[numbers.Real, ...], title: str = 'Plot') -> None: 
  
         """ 
         The constructor creating a plot of the values given as an argument. 
  
         Args: 
             values: A list or a tuple of real values that are going to be plotted. 
  
         Raises: 
             TypeError: If values is not a list or tuple or if any elements it contains is not a real number 
         """ 
  
         if isinstance(values, (list, tuple)): 
             pass 
         else: 
             raise TypeError(f"values is supposed to match the following type: {list.__name__} or " 
                             f"{tuple.__name__}. {type(values).__name__} given instead.") 
  
         if all((isinstance(element, numbers.Real) for element in values)): 
             pass 
         else: 
             for element in values: 
                 if not type(element, numbers.Real): 
                     raise TypeError(f"Every element in the given values should match {numbers.Real.__name__}. " 
                                     f"{type(element).__name__} detected.") 
  
         fig: go.Figure = go.Figure( 
             data=go.Scatter(y=values), 
         ) 
         fig.update_layout( 
             title=title 
         ) 
         fig.write_html( 
             f"{title}.html", 
             auto_open=True 
         ) 
  
  
 class RandomWalk: 
  
     """ 
     Class used for the creation of the random walk data. 
     """ 
  
     def __init__(self) -> None: 
  
         """ 
         Constructor for the RandomWalk class. 
         """ 
  
         self.__values: list[float] = list() 
  
     @property 
     def values(self) -> list[float]: 
  
         """ 
         Getter for the self.__values attribute 
  
         Returns: 
             list[float]: value of the self.__values attribute 
         """ 
  
         return self.__values 
  
     @staticmethod 
     def __create_rand_list(number: int) -> tuple[float]: 
  
         """ 
         Private static method for the creation of the tuple of random values within -1 to 1 range. 
  
         Args: 
             number (int): number of random values to be created 
  
         Returns: 
             tuple[float]: list of the random floating-point numbers from the -1 to 1 range 
         """ 
  
         rand_floats: list[float] = list() 
  
         with concurrent.futures.ThreadPoolExecutor() as executor: 
             futures: list[concurrent.futures.Future[float]] = [ 
                 executor.submit(random.uniform, -1, 1) for _ in range(number) 
             ] 
  
             for future in concurrent.futures.as_completed(futures): 
                 rand_floats.append(future.result()) 
  
         return tuple(rand_floats) 
  
     def create_sequence(self, number: int) -> tuple[float]: 
  
         """ 
         Method used for the creation of the random walk sequence. 
  
         Args: 
             number (int): number of values in the sequence. 
  
         Returns: 
             tuple[float]: list of the values of the random walk. 
         """ 
  
         value: float = 1 
  
         for rand_float in self.__create_rand_list(number): 
             self.values.append(value) 
             value += rand_float 
  
         return tuple(self.values) 
  
  
 class PeaceDisarray: 
  
     """ 
     Class used for testing the peace-disarray trading strategy. 
     """ 
  
     def __init__(self, single_symbol_prices: list[float] | tuple[float], values_to_linear_regression: int) -> None: 
  
         """ 
         Constructor for the PeaceDisarray class. 
  
         Args: 
             single_symbol_prices (list[float] | tuple[float]): a list or a tuple of prices of a single symbol 
  
         Raises: 
             TypeError: If the given single_symbol_prices object is not a list of floating-point values nor a tuple of 
             floating-point values. Also raised if the values_to_linear_regression type is not int. 
             ValueError: If the values_to_linear_regression value is lower or equal to 1 or higher or equal to the number 
              of elements in the single_symbol_prices. 
         """ 
  
         if isinstance(single_symbol_prices, (list, tuple)): 
             pass 
         else: 
             raise TypeError(f"single_symbol_prices type should match either {list.__name__} or {tuple.__name__}. " 
                             f"{type(single_symbol_prices).__name__} given instead.") 
  
         if all({isinstance(element, numbers.Real) for element in single_symbol_prices}): 
             pass 
         else: 
             for element in single_symbol_prices: 
                 if isinstance(element, numbers.Real): 
                     pass 
                 else: 
                     raise TypeError(f"Every element in the single_symbol_prices should be either {int.__name__} or " 
                                     f"{float.__name__}. At least one element is of type {type(element).__name__}.") 
  
         if isinstance(values_to_linear_regression, int): 
             pass 
         else: 
             raise TypeError(f"values_to_linear_regression type should match {int.__name__}. " 
                             f"{type(values_to_linear_regression).__name__} given instead.") 
  
         if values_to_linear_regression > 1: 
             pass 
         else: 
             raise ValueError(f"values_to_linear_regression value should be higher than 1. " 
                              f"{values_to_linear_regression} given.") 
  
         if values_to_linear_regression < len(single_symbol_prices): 
             pass 
         else: 
             raise ValueError(f"values_to_linear_regression value mustn't exceed or be equal to the size of " 
                              f"single_symbol_prices. single_symbol_prices size: {len(single_symbol_prices)}\n" 
                              f"values_to_linear_regression value: {values_to_linear_regression}") 
  
         self.__prices: Final[tuple[float, ...]] = tuple(single_symbol_prices) 
         self.__values_to_linear_regression: Final[int] = values_to_linear_regression 
  
     @property 
     def prices(self) -> tuple[float, ...]: 
  
         """ 
         Getter for the self.__prices attribute 
  
         Returns: 
             tuple[float, ...]: value of the self.__prices attribute 
         """ 
  
         return self.__prices 
  
     @property 
     def values_to_linear_regression(self) -> int: 
  
         """ 
         Getter for the self.__values_to_linear_regression attribute 
  
         Returns: 
             int: value of the self.__values_to_linear_regression attribute 
         """ 
  
         return self.__values_to_linear_regression 
  
     def _calculate_linear_regression_coefficient(self, index: int) -> tuple[int, float]: 
  
         """ 
         Private method for linear regression 'a' coefficient calculation due to errors in pickling process. 
  
         Args: 
             index: index of value in the self.__prices object 
  
         Returns: 
             tuple[int, float]: tuple of the given index and the 'a' linear regression coefficient 
         """ 
  
         return index, LinearRegression( 
                                 { 
                                     _: self.prices[index - self.values_to_linear_regression + _] for _ in range( 
                                         self.values_to_linear_regression 
                                     ) 
                                 } 
                             ).coefficient('a') 
  
     def test(self): 
  
         """ 
         Method used for testing the peace-disarray trading strategy. 
         """ 
  
         linear_regression_coefficients: list[float] = list() 
         for index in range(self.values_to_linear_regression, len(self.prices)): 
             linear_regression_coefficients.append(LinearRegression( 
                             { 
                                 _: self.prices[index - self.values_to_linear_regression + _] for _ in range( 
                                     self.values_to_linear_regression 
                                 ) 
                             } 
                         ).coefficient('ab')) 
  
         return linear_regression_coefficients 
  
  
 @final 
 class Main: 
  
     """ 
     The main class for the whole program execution. 
     """ 
  
     @classmethod 
     def main(cls) -> None: 
  
         """ 
         The main method for the whole program execution. 
         """ 
  
         """ 
         binance_data: Final[BinanceData] = BinanceData() 
         prices: Final[list[float]] = binance_data.get_prices_of_klines_data( 
             klines_data=binance_data.download_klines( 
                 symbol='PNTUSDT', 
                 start_str='1 Jan 2023', 
                 end_str='1 Feb 2023', 
                 klines_type=binance.enums.HistoricalKlinesType.SPOT 
             ) 
         ) 
         """ 
  
         prices: Final[tuple[float]] = RandomWalk().create_sequence( 
             number=1000 
         ) 
  
         shift: Final[int] = 50 
         ValuesPlotter( 
             values=prices[shift:], 
             title='PNTUSDT' 
         ) 
  
         start_time: float = time.perf_counter() 
         ValuesPlotter( 
             values=PeaceDisarray( 
                 single_symbol_prices=prices, 
                 values_to_linear_regression=shift 
             ).test(), 
             title='PNTUSDTLinearReg' 
         ) 
  
         print(f"Linear regressions took to compute: {time.perf_counter() - start_time}") 
  
  
 if __name__ == '__main__': 
     Main.main()

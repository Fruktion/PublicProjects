from __future__ import annotations

import os
import concurrent.futures
import json
import multiprocessing.managers
import numbers
import types
import tqdm
from typing import Self, Callable, Any


class ProgressBar:

    """
    Progress bar class showing the progress bar in the console.
    """

    def __init__(self, total: numbers.Real = 100, description: str | None = None) -> None:

        """
        Constructor for the ProgressBar class.

        Args:
            total (numbers.Real): The total value to be achieved by the progress bar. 100 by default.
            description (str): Description to the progress bar shown on the left. None by default.

        Raises:
            AssertionError: If the type of any argument does not match the correct one.
        """

        assert isinstance(description, str) or description is None, f"description type should match either " \
                                                                    f"{str.__name__} or {types.NoneType.__name__}. " \
                                                                    f"{type(description).__name__} given instead."

        assert isinstance(total, numbers.Real), f"total type should match {numbers.Real.__name__}. " \
                                                f"{type(total).__name__} given instead."

        self._progress_bar: tqdm.tqdm = tqdm.tqdm(total=total, desc=description)

    @property
    def progress_bar(self) -> tqdm.tqdm:

        """
        Getter for the self._progress_bar attribute.

        Returns:
            tqdm.tqdm: The value of the self._progress_bar attribute.
        """

        return self._progress_bar

    def increase(self, value: numbers.Real = 1) -> None:

        """
        Method used for increasing the value of the progress bar.

        Args:
            value (numbers.Real): The value to be added to the current progress value. 1 by default.

        Raises:
            AssertionError: If the value argument is not int or float.
        """

        assert isinstance(value, numbers.Real), f"value type should match {numbers.Real.__name__}. " \
                                                f"{type(value).__name__} given instead."

        self.progress_bar.update(value)

    def __add__(self, other: numbers.Real) -> Self:

        """
        Overriden special method that makes possible increasing the progress bar value using the "+" operator.

        Args:
            other (numbers.Real): A value to be added to current progress on the progress bar. Must be positive.

        Examples:
            "bar + 5" = "bar.increase(5)"
        """

        self.increase(value=other)

        return self

    def __del__(self) -> None:

        """
        Overriden __del__ special method used for object deletion. Automatically called by the garbage collector.
        In here closes the progress bar by calling the self.progress_bar.close() method.
        """

        self.progress_bar.close()


class ShareManager(multiprocessing.managers.BaseManager):

    """
    ShareManager class for managing the data sharing between multiple processes.

    Examples:

        The example for the intended use:
            "
            ShareManager.register('MyCustomClass', MyCustomClass)
            with ShareManager() as manager:
                # Equivalent to "manager.MyCustomClass(10)" except the fact that the equivalent notation (the one in
                # double quotes) raises a warning:
                shared_custom = getattr(manager, manager.MyCustomClass.__name__)(10)
                        with concurrent.futures.ProcessPoolExecutor() as executor:
                            futures = [
                                executor.submit(
                                    shared_custom.get_storage,  # Run some method on the called object
                                    shared_custom  # Pass the object to some method if necessary
                                )
                                for _ in range(4)
                            ]

                            for future in concurrent.futures.as_completed(futures):
                                future.result()
    """

    registered_classes: dict[str, Callable[..., object]] = dict()

    def __init__(self) -> None:
        super().__init__()

    @classmethod
    def custom_register(cls, typeid: str, fn: Callable[..., object | Any]) -> None:

        """
        Method used as a register for the ShareManager class.

        Args:
            typeid (str): The name for the type.
            fn (Callable[..., object | Any]: Callable for the type.

        Raises:
            TypeError: If any of the arguments' types does not match the correct ones.
        """

        if isinstance(typeid, str):
            pass
        else:
            raise TypeError(f"typeid should be of type {str.__name__}. {type(typeid).__name__} given instead.")

        if isinstance(fn, Callable):
            pass
        else:
            raise TypeError(f"fn should be of type {Callable.__name__}. {type(fn).__name__} given instead.")

        setattr(cls, typeid, fn)
        cls.registered_classes[typeid]: Callable[..., object | Any] = fn
        cls.register(typeid, fn)


def create_string(values: list[float], pb: multiprocessing.managers.ValueProxy[ProgressBar], index: int) -> tuple[int, str]:
    return_str: str = str()
    for value in values:
        return_str += str(value) + " "
        pb.increase()

    return index, return_str


class Main:

    @classmethod
    def main(cls) -> None:
        with open("prices_1_Jan_2020_1_Aug_2023", 'r') as file:
            prices: list[float] = json.loads(file.read())
        new_prices = [[]]
        prices_per_thread = len(prices) // os.cpu_count()
        undistributed_price_index = None
        for index, price in enumerate(prices):
            if len(new_prices[-1]) < prices_per_thread:
                new_prices[-1].append(price)
            elif len(new_prices) < os.cpu_count():
                new_prices.append([price])
            else:
                undistributed_price_index = index
        if undistributed_price_index is not None:
            for index, price in enumerate(prices[undistributed_price_index:]):
                new_prices[index % os.cpu_count()].append(price)

        ShareManager.custom_register('ProgressBar', ProgressBar)
        results = [None for _ in range(os.cpu_count())]
        with ShareManager() as manager:
            progress_bar: multiprocessing.managers.ValueProxy[
                ProgressBar] = getattr(manager, manager.ProgressBar.__name__)(len(prices), "String creation")

            with concurrent.futures.ProcessPoolExecutor() as executor:
                futures = [
                    executor.submit(create_string, values, progress_bar, index)
                    for index, values in enumerate(new_prices)
                ]

                for future in concurrent.futures.as_completed(futures):
                    future_result = future.result()
                    results[future_result[0]] = future_result[1]

        saved_str: str = str()
        for result in results:
            saved_str += result

        print(saved_str)
        with open('values.txt', 'w') as file:
            file.write(saved_str)

if __name__ == '__main__':
    Main.main()

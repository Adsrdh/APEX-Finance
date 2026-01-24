import matplotlib.pyplot as plt


class PortfolioVisuals:

    def __init__(self, data):
        self.data = data

    def create_pie_chart(self):  # data is dictionary
        labels = list(self.data.keys())
        values = list(self.data.values())

        fig, ax = plt.subplots()
        ax.pie(values, labels=labels)
        plt.show()


class StockVisuals:
    def __init__(self, data):
        self.data = data

    def create_line_graph(self):  # data is Pandas dataframe
        fig, ax = plt.subplots(figsize=(10, 6))
        self.data.plot(ax=ax)

        ax.set_title("Stock Closing Prices")
        ax.set_xlabel("Date")
        ax.set_ylabel("Price (USD)")
        plt.show()

import sys
from stockportfolio import StockPortfolio
from visuals import PortfolioVisuals, StockVisuals


def print_menu():
    print("\n" + "=" * 60)
    print("📈 STOCK PORTFOLIO MANAGER")
    print("=" * 60)
    print("1. Add Stock")
    print("2. Sell Stock")
    print("3. Remove Stock")
    print("4. View Portfolio Summary")
    print("5. View Detailed Stock Info")
    print("6. Refresh All Data")
    print("7. View Total Portfolio Value")
    print("8. View Sector Pie Chart")
    print("9. View 1-Year Price Chart")
    print("10. View 1-Year Price Chart")
    print("11. Exit")
    print("=" * 60)


def main():
    portfolio_name = input("Enter your portfolio name: ") or "My Portfolio"
    portfolio = StockPortfolio(portfolio_name)

    while True:
        print_menu()
        choice = input("Select an option (1-10): ").strip()

        try:
            if choice == "1":
                ticker = input("Enter stock ticker symbol: ").strip().upper()
                quantity = int(input("Enter quantity to add: "))
                portfolio.add_stock(ticker, quantity)
                print(f"✅ Added {quantity} shares of {ticker} to portfolio.")

            elif choice == "2":
                ticker = input("Enter stock ticker symbol: ").strip().upper()
                quantity = int(input("Enter quantity to sell: "))
                portfolio.sell_stock(ticker, quantity)
                print(f"💸 Sold {quantity} shares of {ticker}.")

            elif choice == "3":
                ticker = input("Enter stock ticker symbol to remove completely: ").strip().upper()
                portfolio.remove_stock(ticker)
                print(f"🗑️ Removed {ticker} from portfolio.")

            elif choice == "4":
                print(portfolio.detailed_summary())

            elif choice == "5":
                ticker = input("Enter ticker symbol to view details: ").strip().upper()
                stock = portfolio.get_stock(ticker)
                if stock:
                    print(stock)
                else:
                    print(f"⚠️ {ticker} not found in portfolio.")

            elif choice == "6":
                print("🔄 Refreshing all stock data...")
                portfolio.refresh_all_data()
                print("✅ All stock data refreshed successfully!")

            elif choice == "7":
                total_value = portfolio.get_portfolio_value()
                print(f"💰 Total Portfolio Value: ${total_value:,.2f}")

            # NEW — PIE CHART
            elif choice == "8":
                data = portfolio.holding_by_sector()
                if not data:
                    print("⚠️ Portfolio is empty — nothing to visualize.")
                else:
                    print("📊 Opening pie chart...")
                    PortfolioVisuals(data).create_pie_chart()

            # NEW — LINE CHART
            elif choice == "9":
                ticker = input("Enter ticker symbol: ").strip().upper()
                stock = portfolio.get_stock(ticker)

                if not stock:
                    print(f"⚠️ {ticker} not found in portfolio.")
                else:
                    print("📈 Fetching 1-year history...")
                    df = stock.history.df_1_year()
                    StockVisuals(df).create_line_graph()

            elif choice == "10":
                ticker = input("Enter ticker symbol: ").strip().upper()
                stock = portfolio.get_stock(ticker)

                if not stock:
                    print(f"⚠️ {ticker} not found in portfolio.")
                else:
                    print("📈 Fetching 1-month history...")
                    df = stock.history.df_1_month()
                    StockVisuals(df).create_line_graph()

            elif choice == "11":
                print(f"👋 Exiting Portfolio Manager. Goodbye, {portfolio.name} owner!")
                sys.exit(0)

            else:
                print("❌ Invalid choice. Please select a valid option.")

        except ValueError:
            print("⚠️ Invalid input. Please enter valid numbers or tickers.")
        except KeyError as e:
            print(f"⚠️ {e}")
        except Exception as e:
            print(f"❌ Unexpected error: {e}")


if __name__ == "__main__":
    main()
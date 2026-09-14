# Binance Automated Grid Trading Bot

An automated cryptocurrency grid trading bot built in Python, designed to operate on the Binance exchange. The bot establishes a localized grid of limit orders and captures market volatility, featuring persistent state recovery, dynamic precision handling, and robust API error management.

## Key Features

*   **Persistent State Recovery:** Maintains a localized JSON state (`orders.json`) using atomic temporary file replacements (`orders_temp.json`) to prevent data corruption during unexpected crashes or power losses.
*   **Dynamic Precision & `MIN_NOTIONAL` Protection:** Automatically fetches Binance's symbol filters and utilizes Python's `Decimal` module to ensure all orders respect Binance's strict rounding rules and minimum trade sizes, preventing rejection errors.
*   **Virtual Order Queueing:** Intelligently monitors for expired or manually cancelled limit orders, placing them in a virtual queue and only deploying them back to the exchange when the live ticker price makes it safe to do so.
*   **Partial Fill Sweeping:** Detects edge cases where orders that are only partially filled get cancelled, automatically dispatching a market sweep order to clear leftover balance and calculating the net slippage/profit impact.
*   **Error Handling:** Built-in armor against network instability and Binance API strictness. Includes specific backoff timers for rate limits, timestamp desyncs, and maintenance windows, alongside a strike system that safely terminates the bot if consecutive errors exceed a safe threshold.

---

## Prerequisites

*   A **Binance Testnet Account** (By default, the script points to `testnet=True`).
*   Your Testnet API Key and Secret.

## Installation & Setup

1. **Clone or Download the Repository:**
   Save the Python script to your local project directory (e.g., `grid_bot.py`).

2. **Install Required Dependencies:**
   Run the following command in your terminal to install the necessary Python packages:
   ```bash
   pip install python-binance python-dotenv requests
   ```

3. **Configure Environment Variables:**
   Create a file named `.env` in the same directory as your script and add your Binance Testnet credentials as follows:
   ```env
   API_KEY=your_binance_testnet_api_key_here
   API_SECRET=your_binance_testnet_api_secret_here
   ```

## Configuration Parameters

You can customize the bot's trading behavior by modifying the variables at the top of the script. 

| Parameter | Default Value | Description |
| :--- | :--- | :--- |
| `trading_symbol` | `"BTCUSDT"` | The specific trading pair you want the grid to operate on. |
| `n` | `30` | The number of initial grid levels (limit buy orders) to place below the current market price. |
| `grid_step` | `0.01` | The percentage distance between each grid level (e.g., `0.01` = 1%). |
| `usdt_per_order` | `1000` | The exact amount of quote currency (USDT) to spend on each grid level. |

*Note: The bot will automatically check your `usdt_balance` upon startup. If you do not have at least `n * usdt_per_order` in free USDT, the bot will safely exit before placing any orders.*

## Usage

To start the bot, run the script via your terminal:

```bash
python grid_bot.py
```

**Startup Sequence:**
1. The bot authenticates and prints your current free/locked balances.
2. It checks for an existing `orders.json` file.
    * **If found:** It resumes the previous session, tracking cumulative profit and monitoring existing active orders.
    * **If not found:** It cancels any preexisting open orders on that symbol, calculates the grid array based on the live price, validates `MIN_NOTIONAL` rules, and dispatches the initial `n` buy limit orders.
3. The infinite loop begins, checking order statuses every 1 second.

## Architecture & Logic Flow

*   **Order Tracking:** Active limit orders are stored in a dictionary mapped as `{orderId: price}`. Buy prices are stored as negative floats, while sell prices are stored as positive floats.
*   **Grid Execution:** When the bot detects a missing `orderId` from the active exchange orders, it queries Binance. If the order was `FILLED`, the bot calculates the executed quantity, deducts the 0.1% Binance trading fee, calculates net profit, and places the opposing counter-order (a sell above the original level, or a buy at the original level).
*   **State Saving:** On every state change (order execution, cancellation, or requeuing), the bot dumps a master dictionary containing `profit`, `active`, and `queue` to JSON.

## ⚠️ Disclaimer

This software is provided for educational and experimental purposes only. Cryptocurrency trading carries a high level of risk, and automated grid bots can result in significant financial loss, especially in trending or highly volatile markets. Always thoroughly test your configurations on the **Binance Testnet** before deploying real capital. The creator of this script assumes no liability for any financial losses incurred.

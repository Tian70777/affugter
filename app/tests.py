import asyncio
import sys
import httpx

'''
Test index for debug commands 
High price: sends a false value of 2 DKKR/kWh to simulate excessive electricity price
Low price: sends a false value of 0.01 DKKR/kWh to simulate excessively cheap electricity price
High humidity: sends a false value of 100% humidity
Low humidity: sends a false value of 0% humidity
Real: resets all values to latest stored real values in the database
On: force switches on the Shelly plug
Off: force switches off the Shelly plug
Humidity: sends a custom value ('humidity 70') to test specific cutoffs
Price: sends a custom value ('price 5.00') to test specific cutoffs
Custom: sends two custom values (humidity, price: 'custom 70, 5.00')
'''

BASE_URL = "http://localhost:8000"

tests = {
    "high_price": lambda: "high_price",
    "low_price": lambda: "low_price",
    "high_humidity": lambda: "high_humidity",
    "low_humidity": lambda: "low_humidity",
    "real": lambda: "real",
    "on": lambda: "on",
    "off": lambda: "off",
    "humidity": lambda val: f"humidity/{val}",
    "price": lambda val: f"price/{val}",
    "custom": lambda hum, price: f"custom/{hum}/{float(price):.3f}",
    "server_based": lambda: "server_based",
    "server_based_stop": lambda: "server_based/stop",
}

async def main():
    import sys
    import httpx

    if len(sys.argv) < 2 or sys.argv[1] not in tests:
        print("Unknown test")
        sys.exit(1)

    test = sys.argv[1]

    if test == "humidity":
        if len(sys.argv) != 3:
            print("Usage: python -m app.tests humidity <value>")
            sys.exit(1)

        endpoint = tests[test](sys.argv[2])

    elif test == "price":
        if len(sys.argv) != 3:
            print("Usage: python -m app.tests price <value>")
            sys.exit(1)

        endpoint = tests[test](sys.argv[2])         

    elif test == "custom":
        if len(sys.argv) != 4:
            print("Usage: python -m app.tests custom <humidity> <price>")
            sys.exit(1)

        endpoint = tests[test](sys.argv[2], sys.argv[3])

    else:
        endpoint = tests[test]()

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"http://localhost:8000/debug/test/{endpoint}"
        )

        try: 
            print(response.json())
        except ValueError:
            print(response.text or "<empty response body>")

if __name__ == "__main__":
    asyncio.run(main())
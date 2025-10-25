
from utils import *
from ticket_searcher import TicketSearcher

if __name__ == "__main__":
    SEARCH_PARAMS = config['search_params']
    AMADEUS_API_KEY = config['amadeus']['api_key']
    AMADEUS_API_SECRET = config['amadeus']['api_secret']
    searcher = TicketSearcher(
        SEARCH_PARAMS['originLocationCode'],
        SEARCH_PARAMS['destinationLocationCode'],
        SEARCH_PARAMS['departureDate'],
        SEARCH_PARAMS['returnDate']
    )
    
    if AMADEUS_API_KEY == "YOUR_CLIENT_ID" or AMADEUS_API_SECRET == "YOUR_CLIENT_SECRET":
        print("❌ 請先在 config.yaml 填入你的 Amadeus API Key 和 Secret！")
        exit(1)
    else:
        success = searcher.run()
        # exit(0 if success else 1)

    print(success)
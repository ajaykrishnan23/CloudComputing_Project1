import argparse
import requests
import csv
from urllib.parse import quote

class YelpScraper:
    def __init__(self):
        self.api_key = '#########'
        self.api_host = 'https://api.yelp.com'
        self.search_path = '/v3/businesses/search'
        self.business_path = '/v3/businesses/'
        self.search_limit = 50

    def make_request(self, host, path, params=None):
        params = params or {}
        url = f'{host}{quote(path.encode("utf8"))}'
        headers = {'Authorization': f'Bearer {self.api_key}'}
        print(f'Requesting {url}')
        response = requests.get(url, headers=headers, params=params)
        return response.json()

    def search_businesses(self, term, location, offset):
        print(f'Offset in search {offset}')
        params = {
            'term': term.replace(' ', '+'),
            'location': location.replace(' ', '+'),
            'offset': offset,
            'limit': self.search_limit        
        }
        return self.make_request(self.api_host, self.search_path, params)

    def get_total_results(self, term, location):
        params = {
            'term': term.replace(' ', '+'),
            'location': location.replace(' ', '+'),
            'limit': self.search_limit        
        }
        return self.make_request(self.api_host, self.search_path, params).get('total')

    def get_business_details(self, business_id):
        business_path = self.business_path + business_id
        return self.make_request(self.api_host, business_path)

    def perform_search(self, term, location):
        query = ["bID", "name", "address", "cord", "numOfReview", "rating", "zipcode", "cuisine"]
        filename = "yelpScrape.csv"
        with open(filename, "a", newline='', encoding = 'utf-8') as fp:
            writer = csv.writer(fp, dialect='excel')
            writer.writerow(query)

        cuisines = ['chinese', 'indian', 'italian']
        for cuisine in cuisines:
            new_term = f'{cuisine} restaurants'
            total = self.get_total_results(new_term, location)
            print(total, cuisine)
            run = 0
            max_offset = int(total / 50)
            businesses = []
            for offset in range(0,1):
                if run == 25:
                    break
                response = self.search_businesses(new_term, location, offset+50)
                if response.get('businesses') is None:
                    break
                businesses.append(response.get('businesses'))
                run += 1

            print_var = []
            for buis in businesses:
                for b in buis:
                    print_var.append(b)

            if not businesses:
                return

            for b in print_var:
                bID = b['id']
                name = b['name']
                add = ', '.join(b['location']['display_address'])
                numOfReview = int(b['review_count'])
                rating = float(b['rating'])

                if (b['coordinates'] and b['coordinates']['latitude'] and b['coordinates']['longitude']):
                    cord = f"{b['coordinates']['latitude']}, {b['coordinates']['longitude']}"
                else:
                    cord = None

                if (b['location']['zip_code']):
                    zipcode = b['location']['zip_code']
                else:
                    zipcode = None

                temp = [bID, name, add, cord, numOfReview, rating, zipcode, cuisine]

                with open(filename, "a", newline='', encoding = 'utf-8') as fp:
                    writer = csv.writer(fp, dialect='excel')
                    writer.writerow(temp)

            print(f"Added {cuisine} restaurants")

def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('-q', '--term', dest='term', default=YelpScraper().default_term,
                        type=str, help='Search term (default: %(default)s)')
    parser.add_argument('-l', '--location', dest='location',
                        default=YelpScraper().default_location, type=str,
                        help='Search location (default: %(default)s)')

    input_values = parser.parse_args()
    YelpScraper().perform_search(input_values.term, input_values.location)

if __name__ == '__main__':
    main()

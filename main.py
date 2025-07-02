from extractors.parser import search_category
from utils.helpers import search_official_website, is_valid_url

def main():
    """Main function to search for the official website of a company."""

    input_text = input("Enter the Brand Name or URL: ").strip()

    # Check if the input is a valid URL
    if is_valid_url(input_text):
        site_url = input_text
    else:
        print("Searching for official website of company:", input_text)
        site_url = search_official_website(input_text)
        print("Official website found:", site_url)

    # If a valid URL is found, proceed to search for categories
    if site_url:
        print("Searching Categories...")
        categories = search_category(site_url)

        if categories:
            print("Number of categories found:", len(categories))
            for category in categories:
                print(f"- {category['name']}: {category['url']}")
    else:
        print("No website found for the given input.")

if __name__ == "__main__":
    main()

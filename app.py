import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import os

# Set up the Streamlit app
st.title("Dynamic Book Scraper with Real-Time Updates")
st.write("Scrape book data from any user-provided book website with real-time updates.")

# User input for the base URL of the website
user_url = st.text_input("Enter the base URL of the book website (e.g., `https://books.toscrape.com/catalogue/`):")

# User input for the number of pages to scrape
num_pages = st.number_input("Enter the number of pages to scrape (1-50):", min_value=1, max_value=50, value=10)

# Button to start scraping
if st.button("Start Scraping"):
    if not user_url:
        st.error("Please enter a valid base URL!")
    else:
        # Adjust base URLs
        base_url = user_url + "page-{}.html"
        book_base_url = user_url

        # Create directories if they don't exist
        os.makedirs('data_sheet', exist_ok=True)
        os.makedirs('images', exist_ok=True)

        # List to store book details
        books = []

        # Function to extract data from a single page
        def extract_data_from_page(soup, page, real_time_display):
            for book in soup.find_all('article', class_='product_pod'):
                title = book.h3.a['title']
                price = book.find('p', class_='price_color').text
                availability = book.find('p', class_='instock availability').text.strip()
                rating_text = book.p['class'][1]
                rating = convert_rating_to_number(rating_text)
                link = book_base_url + book.h3.a['href']
                thumbnail_url = book_base_url + book.find('img', class_='thumbnail')['src'].lstrip('/')
                thumbnail_file_name = save_thumbnail_image(thumbnail_url, title)

                book_data = {
                    'Title': title,
                    'Price': price,
                    'Availability': availability,
                    'Rating': rating,
                    'Link': link,
                    'Thumbnail URL': thumbnail_url,
                    'Thumbnail File Name': thumbnail_file_name
                }

                books.append(book_data)
                real_time_display.text(f"Scraped: {title} | Price: {price} | Availability: {availability}")

        # Function to convert rating text to a number
        def convert_rating_to_number(rating_text):
            rating_dict = {
                'One': 1,
                'Two': 2,
                'Three': 3,
                'Four': 4,
                'Five': 5
            }
            return rating_dict.get(rating_text, 0)

        # Function to save thumbnail image
        def save_thumbnail_image(url, title):
            response = requests.get(url)
            sanitized_title = "".join([c if c.isalnum() else "_" for c in title])
            image_path = os.path.join('images', f"{sanitized_title}.jpg")
            with open(image_path, 'wb') as file:
                file.write(response.content)
            return image_path

        # Scrape the specified number of pages
        st.write(f"Scraping data from the first {num_pages} pages at {user_url}...")
        real_time_display = st.empty()  # Placeholder for real-time updates
        for page in range(1, num_pages + 1):
            url = base_url.format(page)
            response = requests.get(url)
            if response.status_code != 200:
                st.error(f"Failed to fetch data from page {page}. Please check the URL and try again.")
                break
            soup = BeautifulSoup(response.content, 'html.parser')
            extract_data_from_page(soup, page, real_time_display)
            st.write(f"Extracted data from page {page}")

        # Save the data to a CSV file
        if books:
            df = pd.DataFrame(books)
            csv_path = 'data_sheet/books_data.csv'
            df.to_csv(csv_path, index=False)
            st.write("Scraping completed! Here is a preview of the data:")
            st.dataframe(df)

            # Provide download option for the CSV
            st.download_button(
                label="Download CSV",
                data=df.to_csv(index=False).encode('utf-8'),
                file_name='books_data.csv',
                mime='text/csv'
            )
        else:
            st.warning("No data scraped. Please verify the website and try again.")

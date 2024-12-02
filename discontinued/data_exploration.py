
import pandas as pd
import numpy as np

# Evaluate threaded scraper logic
df = pd.DataFrame(np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]]),
                   columns=['a', 'b', 'c'])
num_threads = 2
chunk_size = len(df) // num_threads
df_chunks = [df[i:i + chunk_size] for i in range(0, len(df), chunk_size)]
if len(df_chunks) > num_threads:
    df_chunks[-2] = pd.concat([df_chunks[-2], df_chunks[-1]])
    df_chunks.pop()

for chunk in df_chunks:
    print("Chunk")
    print(chunk)

# Evaluate export scraper missing data
data = pd.read_csv('esg_app/api/data/SP500.csv')
output_data = pd.read_csv('esg_app/api/data/SP500_esg_scores.csv')
output_data['SnP_ESG_Ticker'] = output_data['SnP_ESG_Ticker'].str.split(' ').str[1]
missing_rows = data[~data['Symbol'].isin(output_data['SnP_ESG_Ticker'])]

print("Length:", len(data))
print("Unique symbols:", data['Symbol'].nunique())
print(f"Number of missing rows: {len(missing_rows)}")
print("\nMissing symbols:")
print(missing_rows[16:31])

# # Alternative versions of functions in threaded_scraper
# def wait_element_to_load(self, xpath: str):
#     logging.debug("Waiting for element to load: %s", xpath)
#     delay = 10  # seconds
#     ignored_exceptions = (NoSuchElementException,
#                           StaleElementReferenceException,)
#     try:
#         sleep(0.5)
#         WebDriverWait(self.driver, delay,
#                       ignored_exceptions=ignored_exceptions).until(
#             EC.presence_of_element_located((By.XPATH, xpath)))
#         logging.debug("Element loaded successfully: %s", xpath)
#         return True
#     except TimeoutException:
#         logging.error("Timeout while waiting for element: %s", xpath)
#         return False

# def locate_element(self, xpath: str = None, class_name: str = None,
#                  multiple: bool = False) -> WebElement:
#     if xpath:
#         if not WebScraper.wait_element_to_load(self, xpath):
#             logging.error(f"Failed to locate element with xpath: {xpath}")
#             return None
#         try:
#             return self.driver.find_element(By.XPATH, xpath)
#         except NoSuchElementException as e:
#             logging.error(f"Element not found after wait - xpath: {xpath}. Error: {str(e)}")
#             return None
#     elif class_name:
#         try:
#             return self.driver.find_element(By.CLASS_NAME, class_name)
#         except NoSuchElementException as e:
#             logging.error(f"Element not found - class: {class_name}. Error: {str(e)}")
#             return None
#     return None

    # def is_subscription_form_present(self, xpath: str = None, 
    #                                  class_name: str = None, 
    #                                  id_name: str = None) -> bool:
    #     '''Check if the subscription form is present.
    #     Args:
    #         xpath (str) : The xpath of the web element.
    #         class_name (str) : The class name of the web element.
    #         id_name (str) : The id name of the web element.

    #     Returns:
    #         (bool) : True if located; False otherwise.
    #     '''
    #     try:
    #         self.wait_element_to_load(xpath, class_name, id_name)
    #         form = self.locate_element(xpath, class_name, id_name)
    #         if form:
    #             logging.info("Subscription form appeared.")
    #             return True
    #     except:
    #         return False
    # def fill_field(self, entry: str,
    #                     xpath: str = None, 
    #                     class_name: str = None, 
    #                     id_name: str = None):
    #     """Fill out the subscription form."""
    #     try:
    #         field = self.locate_element(xpath, class_name, id_name)
    #         field.clear()
    #         field.send_keys(entry)
    #     except Exception as e:
    #         logging.warning("Error while filling in field: %s", e)

    # def select_dropdown(self, selection,
    #                     xpath: str = None, 
    #                     class_name: str = None, 
    #                     id_name: str = None):
    #     try:
    #         segment_dropdown = Select(self.locate_element(xpath, class_name, id_name))
    #         segment_dropdown.select_by_value(selection)
    #     except Exception as e:
    #         logging.warning("Error while selecting from dropdown: %s", e)

# Dockerfile
    # py3-setuptools \
    # py3-pip \
    # py3-wheel
    # RUN pip install --upgrade pip setuptools wheel

# requirements.txt
# censusname==0.2.2

lol = data.iloc[[4]]
print("Data:", lol)
print("Length", len(lol))
lmao = np.array_split(lol, 1)
print("Chunk:", lmao)
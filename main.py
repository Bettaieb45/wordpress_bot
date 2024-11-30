from utils.login import login_to_wordpress
from utils.csv_to_dict import process_csv_to_dict
from wordpress.update_links import update_links
from config import username, password,driver,output_csv_path,input_csv_path

if __name__ == "__main__":
    login_to_wordpress(username, password)
    posts_dict = process_csv_to_dict(input_csv_path)
    update_links(posts_dict, output_csv_path)
    driver.quit()
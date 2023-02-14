# CV_Bank_Scraping

### Introduction
This code uses Selenium library to scrape www.cvbankas.lt. User inputs job title, programming language in 
the terminal which is passed to the page. The script is opening every job add and extracts Title, Company,
City, Salary, View Count, Applicant count, Add expiration, URL and saves it to csv file. if there is more
than one page the code is navigating to next page and scrapes data as well until all the search result are 
scraped and saved to the file.  

### Launch procedure

- Launch command line 
- Issue the command: git clone https://github.com/Andriusma1989/WebscrapingCvBank.git
- Open is favorite editor / IDE and configure the environment 
- Install the necessary libraries: pip install -r requirements.txt

import re
import os
import nltk
import joblib
import requests
import numpy as np
from bs4 import BeautifulSoup
import urllib.request as urllib
import matplotlib.pyplot as plt
from nltk.corpus import stopwords
from wordcloud import WordCloud,STOPWORDS
from flask import Flask,render_template,request,redirect,session
from models import db, User

nltk.download('stopwords')

app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///user.db'
app.secret_key = "secret_key"
db.init_app(app)

# word_2_int = joblib.load('word2int.sav')
# model = joblib.load('sentiment.sav')
stop_words = set(stopwords.words('english'))

def clean(x):
    x = re.sub(r'[^a-zA-Z ]', ' ', x) # replace evrything thats not an alphabet with a space
    x = re.sub(r'\s+', ' ', x) #replace multiple spaces with one space
    x = re.sub(r'READ MORE', '', x) # remove READ MORE
    x = x.lower()
    x = x.split()
    y = []
    for i in x:
        if len(i) >= 3:
            if i == 'osm':
                y.append('awesome')
            elif i == 'nyc':
                y.append('nice')
            elif i == 'thanku':
                y.append('thanks')
            elif i == 'superb':
                y.append('super')
            else:
                y.append(i)
    return ' '.join(y)

def extract_amazon_reviews(url, clean_reviews, org_reviews, customernames, commentheads, ratings):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    }


def extract_all_reviews(url, clean_reviews, org_reviews,customernames,commentheads,ratings):
    try:
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
        }

        response = requests.get(url, headers=headers)
        print(url)
        response.raise_for_status()  # Raise an exception for HTTP errors (4xx and 5xx)
        print(response.raise_for_status())
        page_html = BeautifulSoup(response.text, "html.parser")

        if "amazon" in url:
            extract_amazon_reviews(url, clean_reviews, org_reviews, customernames, commentheads, ratings)
        else:
            reviews = page_html.find_all('div', {'class': 'ZmyHeo'})
            commentheads_ = page_html.find_all('p', {'class': 'z9E0IG'})
            customernames_ = page_html.find_all('p', {'class': '_2NsDsF AwS1CA'}) 
            ratings_ = page_html.find_all('div', {'class': ['XQDdHH Js30Fc Ga3i8K','XQDdHH Czs3gR Ga3i8K','XQDdHH Ga3i8K']})
                
            for review in reviews:
                x = review.get_text()
                org_reviews.append(re.sub(r'READ MORE', '', x))
                clean_reviews.append(clean(x))
            
            for cn in customernames_:
                customernames.append('~' + cn.get_text())
            
            for ch in commentheads_:
                commentheads.append(ch.get_text())

            ra = []
            for r in ratings_:
                try:
                    if int(r.get_text()) in [1, 2, 3, 4, 5]:
                        ra.append(int(r.get_text()))
                    else:
                        ra.append(0)
                except:
                    ra.append(r.get_text())

            ratings += ra
            print(ratings)
            

    except requests.RequestException as e:
        print(f"An error occurred while fetching data from {url}: {e}")

def tokenizer(s):
    s = s.lower()      # convert the string to lower case
    tokens = nltk.tokenize.word_tokenize(s) # make tokens ['dogs', 'the', 'plural', 'for', 'dog']
    tokens = [t for t in tokens if len(t) > 2] # remove words having length less than 2
    tokens = [t for t in tokens if t not in stop_words] # remove stop words like is,and,this,that etc.
    return tokens


@app.route("/")
def main():
    return render_template("index.html")

@app.route("/sign", methods=["GET", 'POST'])
def sign():
    if request.method == "POST":
        name = request.form["username"]
        email = request.form["email"]
        password = request.form["pass"]

        new_user = User(name=name, email=email, password=password)
        db.session.add(new_user)
        db.session.commit()
        return redirect("/login")
    return render_template("sign.html")

@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            session["email"] = user.email
            return redirect("/home")
        else:
            return render_template("login.html", error="Invalid user or password")
    else:
        return render_template("login.html")
        
@app.route("/home")
def home():
    return render_template("home.html")

@app.route('/results',methods=['GET'])
def result():    
    url = request.args.get('url')

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    }

    response = requests.get(url, headers=headers)

    nreviews = int(request.args.get('num'))
    clean_reviews = []
    org_reviews = []
    customernames = []
    commentheads = []
    ratings = []

    if response.status_code == 200:
        page_html = BeautifulSoup(response.text, "html.parser")

        proname_elements = page_html.find_all('span', {'class': 'VU-ZEz'})
        price_elements = page_html.find_all('div', {'class': 'Nx9bqj CxhGGd'})
        print(price_elements)
        # Check if the elements are not empty before accessing index 0
        proname = proname_elements[0].get_text() if proname_elements else 'Product Name Not Found'
        price = price_elements[0].get_text() if price_elements else 'Price Not Found'
        
        # getting the link of see all reviews button
        all_reviews_elements = page_html.find_all('div', {'class': 'col pPAw9M'})

            # Check if the elements are not empty before accessing index 0
        if all_reviews_elements:
            all_reviews_url = all_reviews_elements[0]
            all_reviews_url = all_reviews_url.find_all('a')[-1]
            all_reviews_url = 'https://www.flipkart.com' + all_reviews_url.get('href')
            url2 = all_reviews_url + '&page=1'
        else:
                # Handle the case when 'all_reviews_elements' is empty
            print("No review elements found")
            url2 = ''
    
            # start reading reviews and go to next page after all reviews are read 
        while url2 and len(clean_reviews) < nreviews:
            x = len(clean_reviews)
            
            # extracting the reviews
            extract_all_reviews(url2, clean_reviews, org_reviews, customernames, commentheads, ratings)

            # For Flipkart
            if "flipkart" in url2:
                url2 = url2[:-1] + str(int(url2[-1]) + 1)

            # For Amazon
            elif "amazon" in url2:
                extract_amazon_reviews(url2, clean_reviews, org_reviews, customernames, commentheads, ratings)

                current_page_number = int(re.search(r'pageNumber=(\d+)', url2).group(1))
                next_page_number = current_page_number + 1
                url2 = re.sub(r'pageNumber=\d+', f'pageNumber={next_page_number}', url2)

            if x == len(clean_reviews):
                break

        org_reviews = org_reviews[:nreviews]
        clean_reviews = clean_reviews[:nreviews]
        customernames = customernames[:nreviews]
        commentheads = commentheads[:nreviews]
        ratings = ratings[:nreviews]


        # building our wordcloud and saving it
        if clean_reviews:
                for_wc = ' '.join(clean_reviews)
                wcstops = set(STOPWORDS)
                wc = WordCloud(width=1400, height=800, stopwords=wcstops, background_color='white').generate(for_wc)
                plt.figure(figsize=(20, 10), facecolor='k', edgecolor='k')
                plt.imshow(wc, interpolation='bicubic') 
                plt.axis('off')
                plt.tight_layout()
                CleanCache(directory='static/images')
                plt.savefig('static/images/woc.png')
                plt.close()
        else:
            print("No reviews available for WordCloud.")
            
        d = []
        remain = len(org_reviews)-len(ratings)
        ratings = ratings + [3]*remain
        for i in range(len(org_reviews)):
            x = {}
            x['review'] = org_reviews[i]
            # x['sent'] = predictions[i]
            x['cn'] = customernames[i]
            x['ch'] = commentheads[i]
            x['stars'] = ratings[i]
            d.append(x)
        

        for i in d:
            if i['stars']!=0:
                if i['stars'] in [1,2]:
                    i['sent'] = 'NEGATIVE'
                else:
                    i['sent'] = 'POSITIVE'
        

        np, nn = 0, 0
        for i in d:
            if i['sent'] == 'NEGATIVE':
                nn += 1
            else:
                np += 1

        return render_template('result.html',dic=d,n=len(clean_reviews),nn=nn,np=np,proname=proname,price=price)
        
    
@app.route('/wc')
def wc():
    return render_template('wc.html')


class CleanCache:
	def __init__(self, directory=None):
		self.clean_path = directory
		# only proceed if directory is not empty
		if os.listdir(self.clean_path) != list():
			# iterate over the files and remove each file
			files = os.listdir(self.clean_path)
			for fileName in files:
				print(fileName)
				os.remove(os.path.join(self.clean_path,fileName))
		print("cleaned!")


@app.route("/reviews")
def review():
    return render_template("elements.html")

@app.route("/generic")
def generic():
    return render_template("generic.html")

if __name__ == '__main__':
    app.run(debug=True, threaded=False)

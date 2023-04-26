import requests
from selenium.common import NoSuchElementException
from selenium.webdriver.chrome.options import Options

ANSAN_NEWS_URL="http://www.ansannews.co.kr/"

from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from flask_sqlalchemy import SQLAlchemy
from flask import Flask, jsonify, render_template, request, send_file, make_response
import os
import psycopg2
from flask_cors import CORS, cross_origin
from io import BytesIO
from urllib.parse import unquote

conn = psycopg2.connect("postgres://vtqrqerl:NIvz9MlhFQPKRzt0Hx8-ElEwGevtXehs@floppy.db.elephantsql.com/vtqrqerl")
app = Flask(__name__)
CORS(app, resources={r"*": {"origins": "*"}})
app.config['CORS_HEADERS'] = 'Content-Type'


app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'

##CONNECT TO DB
app.config['SQLALCHEMY_DATABASE_URI'] = "postgres://vtqrqerl:NIvz9MlhFQPKRzt0Hx8-ElEwGevtXehs@floppy.db.elephantsql.com/vtqrqerl"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

## Create DB
class AnsanNewsReact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    img_src = db.Column(db.String, nullable=True, default=None)
    link = db.Column(db.String, nullable=False)
    title = db.Column(db.String, nullable=False)
    desc = db.Column(db.String, nullable=False)


with app.app_context():
    db.create_all()

## Scrapping news
chrome_options = Options()
chrome_options.binary_location = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
service = ChromeService(executable_path=ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)
driver.get(ANSAN_NEWS_URL)

@app.route('/image-proxy', methods=['GET'])
def proxy_image():
    image_url = request.args.get('url')
    if not image_url:
        return 'No URL provided', 400

    decoded_image_url = unquote(image_url)
    response = requests.get(decoded_image_url)
    if response.status_code != 200:
        return f'Error fetching image: {response.status_code}', response.status_code

    return send_file(BytesIO(response.content), mimetype=response.headers['content-type'])

def fetch_articles():
    articles = []

    for i in range(1, 4):
        article_img = driver.find_element(By.XPATH, f"/html/body/div[1]/div/div[2]/div/section/div[3]/div[2]/div/div[1]/div[1]/article/section/div/ul/li[{i}]/a/div[1]")
        article_img_src = f"http://www.ansannews.co.kr{article_img.get_attribute('style').split('(')[1].split(')')[0]}".replace('"', '')

        article_anchor_tag = driver.find_element(By.XPATH, f"/html/body/div[1]/div/div[2]/div/section/div[3]/div[2]/div/div[1]/div[1]/article/section/div/ul/li[{i}]/a")
        article_href = article_anchor_tag.get_attribute('href')

        article_title = driver.find_element(By.XPATH, f"/html/body/div[1]/div/div[2]/div/section/div[3]/div[2]/div/div[1]/div[1]/article/section/div/ul/li[{i}]/a/div[1]/span").text
        article_desc = driver.find_element(By.XPATH, f"/html/body/div[1]/div/div[2]/div/section/div[3]/div[2]/div/div[1]/div[1]/article/section/div/ul/li[{i}]/a/div[2]/p").text

        articles.append({
            'img_src': article_img_src,
            'link': article_href,
            'title': article_title,
            'desc': article_desc
        })

    return articles

def fetch_sub_articles():
    sub_articles = []
    for k in range(1,4):
        for j in range(1, 7):
            try:
                sub_article_title = driver.find_element(By.XPATH, f"/html/body/div[1]/div/div[2]/div/section/div[3]/div[2]/div/div[1]/div[3]/article[{k}]/section/div/ul/li[{j}]/div[1]/a/strong").text
                sub_article_img_src = f"http://www.ansannews.co.kr{driver.find_element(By.XPATH, f'/html/body/div[1]/div/div[2]/div/section/div[3]/div[2]/div/div[1]/div[3]/article[{k}]/section/div/ul/li[{j}]/a').get_attribute('style').split('(')[1].split(')')[0]}".replace('"', '')
                sub_article_desc = driver.find_element(By.XPATH, f"/html/body/div[1]/div/div[2]/div/section/div[3]/div[2]/div/div[1]/div[3]/article[{k}]/section/div/ul/li[{j}]/p/a").text
                sub_article_href = driver.find_element(By.XPATH, f"/html/body/div[1]/div/div[2]/div/section/div[3]/div[2]/div/div[1]/div[3]/article[{k}]/section/div/ul/li[{j}]/p/a").get_attribute('href')
                sub_articles.append({
                    'img_src': sub_article_img_src,
                    'title': sub_article_title,
                    'desc': sub_article_desc,
                    'link': sub_article_href,
                })
            except NoSuchElementException:
                try:
                    sub_article_title = driver.find_element(By.XPATH,
                                                            f"/html/body/div[1]/div/div[2]/div/section/div[3]/div[2]/div/div[1]/div[3]/article[{k}]/section/div/ul/li[{j}]/div[1]/a/strong").text
                    sub_article_desc = driver.find_element(By.XPATH,
                                                           f"/html/body/div[1]/div/div[2]/div/section/div[3]/div[2]/div/div[1]/div[3]/article[{k}]/section/div/ul/li[{j}]/p/a").text
                    sub_article_href = driver.find_element(By.XPATH,
                                                           f"/html/body/div[1]/div/div[2]/div/section/div[3]/div[2]/div/div[1]/div[3]/article[{k}]/section/div/ul/li[{j}]/p/a").get_attribute(
                        'href')

                    sub_articles.append({

                        'title': sub_article_title,
                        'desc': sub_article_desc,
                        'link': sub_article_href,
                    })
                except NoSuchElementException:
                    continue
    return sub_articles

def save_articles(articles):
    db.session.query(AnsanNewsReact).delete()
    db.session.commit()

    for article in articles:
        try:
            news = AnsanNewsReact(
                img_src=article['img_src'],
                link=article['link'],
                title=article['title'],
                desc=article['desc']
            )
        except KeyError:
            news = AnsanNewsReact(
                link=article['link'],
                title=article['title'],
                desc=article['desc']
            )
            db.session.add(news)
        else:
            db.session.add(news)

    db.session.commit()


with app.app_context():
    articles = fetch_articles() + fetch_sub_articles()
    driver.close()
    save_articles(articles)


@app.route("/")
def home():
    return render_template("index.html")

@app.route("/all", methods=['GET'])
@cross_origin(origins="*", allow_headers=["Content-Type", "Authorization", "Access-Control-Allow-Credentials"],
              supports_credentials=True)
def all_news():
    all_news = db.session.query(AnsanNewsReact).all()
    news_dict = {"news": []}

    for news in all_news:
        news_data = {
            'img_src': news.img_src,
            'link': news.link,
            'title': news.title,
            'desc': news.desc
        }
        news_dict["news"].append(news_data)

    response = make_response(jsonify(news_dict))
    response.headers['Content-Type'] = 'application/json'
    response.headers['Access-Control-Allow-Origin'] = '*'

    return response

if __name__ == '__main__':
    app.run(debug=True)

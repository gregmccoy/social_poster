import sys
import sqlite3
import datetime
from termcolor import colored
from social.poster import Post, Poster
from social.utils import format_date, get_ampm, read_conf

class PostManager(object):
    def __init__(self, email, folder):
        self.poster = Poster(email, folder)
        self.social = ["tw1", "tw2", "tw3", "fb1", "dptw1", "gplus"]
        self.ca_worksheet = self.poster.get_sheets(read_conf("sheet_write"), read_conf("write_name"))
        self.us_worksheet = self.poster.get_sheets(read_conf("sheet_read"), read_conf("read_name"))
        self.ca_posts = []
        self.us_posts = []
        self.current_posts = []
        self.conn = sqlite3.connect('social.db')
        self.blanks = {
                "C": 4,
                "D": 4,
                "F": 4,
            }


    def init_database(self):
        c = self.conn.cursor()
        try:
            c.execute("DROP TABLE us_posts")
            c.execute("DROP TABLE ca_posts")
        except:
            pass
        c.execute("CREATE TABLE us_posts (date text, text text, service text, profile text, image text)")
        c.execute("CREATE TABLE ca_posts (date text, text text, service text, profile text, image text)")
        self.conn.commit()


    def image_match(self):
        self.poster.set_images(self.us_posts)


    def get_current_posts(self, datestart, dateend):
        for post in self.us_posts:
            dateobj = format_date(post.date, "%m-%d-%y")
            dateobjstart = format_date(datestart, "%Y-%m-%d")
            dateobjend = format_date(dateend, "%Y-%m-%d")
            if dateobj >= dateobjstart and dateobj <= dateobjend:
                self.current_posts.append(post)


    def post_current(self):
        for post in self.current_posts:
            if post.image == None:
                post.image = []
            if isinstance(post.image, list) and len(post.image) > 1:
                print(colored("Skipping mutli image post - " + str(post.image), "red"))
            else:
                print("******************************************")
                print(colored("Date: ", "green") + post.date + post.ampm)
                print(colored("Text: ", "green") + post.text)
                print(colored("Image: ", "green") + str(post.image))
                print(colored("Service: ", "green") + post.service)
                if post.profile:
                    print(colored("Profile: ", "green") + post.profile)
                if post.warning:
                    print(colored("WARNING! ", "yellow") + post.warning)
                print("---")
                answer = input(colored("Is this post ok? (y/n):", "cyan"))
                if answer == "y":
                    answer = input(colored("Post Now? (y/n):", "cyan"))
                    if answer == "y":
                        self.poster.queue_post(post)
                        self.write_changes(post)
                else:
                    print("Ignoring")
                print("\n")
                print("******************************************")


    def load_database(self):
        c = self.conn.cursor()
        for table, media in { "ca_posts": self.ca_posts, "us_posts": self.us_posts }.items():
            c.execute("SELECT * FROM {}".format(table))
            rows = c.fetchall()
            for row in rows:
                p = Post(date=row[0], text=row[1], service=row[2], profile=row[3], image=row[4])
                if p:
                    media.append(p)


    def sync_database(self):
        ca_all = self.poster.get_all_social(self.ca_worksheet, "ca")
        us_all = self.poster.get_all_social(self.us_worksheet, "us")
        c = self.conn.cursor()
        for table, media in { "ca_posts": ca_all, "us_posts": us_all }.items():
            for social, value in media.items():
                for post in value:
                    if "<IG Link>" in post.text:
                        continue
                    date = ""
                    if table == "ca_posts":
                        date = datetime.datetime.strptime(post.date, '%d/%m/%Y').strftime('%m-%d-%y')
                    else:
                        date = datetime.datetime.strptime(post.date, '%m/%d/%Y').strftime('%m-%d-%y')
                    date += get_ampm(social)
                    sql = "INSERT INTO {} (date, text, service, profile, image) values (?, ?, ?, ?, ?)".format(table)
                    c.execute(sql, (date, post.text, post.service, post.profile, post.image))
        self.conn.commit()


    def write_changes(self, post):
        print(colored("Writing changes to Google Sheet...", "yellow"))
        result = " "
        done = False
        if post.service == "twitter":
            columns = ["C{}", "D{}"]
        elif post.service == "facebook":
            columns = ["F{}"]
        else:
            print("Not Support server")
            return

        while not done:
            for value in columns:
                count = self.blanks[value.format("")]
                # Hacky workaround so that extra output doesn't print out
                oldstdout = sys.stdout
                sys.stdout = open('tmp', 'w')
                date = self.ca_worksheet.acell("A{}".format(count)).value
                result = self.ca_worksheet.acell(value.format(count)).value
                sys.stdout = oldstdout
                if result == "":
                    if post.service == "twitter":
                        # write to Google Sheets
                        print(colored("Cell: {}".format(value.format(count)), "yellow"))
                        print(colored("Date: {}".format(date), "yellow"))
                        #self.ca_worksheet.update_acell(value.format(count), post.text)
                        done = True
                    elif post.service == "facebook":
                        # write to Google Sheets
                        print(colored("Cell: {}".format(value.format(count)), "yellow"))
                        print(colored("Date: {}".format(date), "yellow"))
                        #self.ca_worksheet.update_acell(value.format(count), post.text)
                        done = True
                self.blanks[value.format("")] += 1
                if done == True:
                    break


    def report(self):
        facebook_count = 0
        fbimg_count = 0
        twitter_count = 0
        twitterimg_count = 0
        else_count = 0
        for item in self.current_posts:
            if item.service == "facebook":
                facebook_count += 1
                if item.image:
                    fbimg_count += 1
            elif item.service == "twitter":
                twitter_count += 1
                if item.image:
                    twitterimg_count += 1
            else:
                else_count += 1
        print("Facebooks Posts: " + str(facebook_count))
        print("Facebook Posts with images {}".format(str(fbimg_count)))
        print("Twitter Posts: " + str(twitter_count))
        print("Twitter Posts with images {}".format(str(twitterimg_count)))
        print("Other Posts: " + str(else_count))

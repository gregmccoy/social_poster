from os import listdir
import smtplib
from termcolor import colored
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from oauth2client.service_account import ServiceAccountCredentials
from apiclient import discovery
import httplib2
import gspread
from social.utils import get_ampm, read_conf

import docx
import re


class Post(object):

    def __init__(self, date=None, text=None, image=[], service=None, profile=None):
        self.date = ""
        self.ampm = ""
        text = text.replace("“", '"')
        text = text.replace("”", '"')
        text = text.replace("…", '...')
        text = text.split("COMMENT")[0]

        self.warning = None
        try:
            self.warning = re.search("\[.*?\].*", text).group(0)
            text = text.replace(self.warning, "")
        except:
            pass

        self.text = text
        self.image = image
        self.approved = False
        self.profile = profile
        self.service = service
        self.ampm = re.search("[APap][mM][0-9]?", date).group(0)
        self.date = re.search("\d{1,4}[/-]\d{1,2}([/-]\d{1,4})?", date).group(0)

        if not service and not profile:
            length = len(self.text)
            if self.image:
                length += 24
            if length > 140:
                self.service = "facebook"
            else:
                self.service = "twitter"
                self.profile = "gfaca"

    def __str__(self):
        return  str(self.date) + "\n" + str(self.text) + "\n" + str(self.image) + "\n"



class Poster(object):
    def __init__(self, email, folder):
        self.posts = []
        self.us_sheets = []
        self.ca_sheets = []
        self.workdir = read_conf("workdir") + folder + "/"
        #self.file = self.get_docx()
        self.email = email
        self.worksheet = None
        self.media = {
            "tw1": "C{}",
            "tw2": "D{}",
            "tw3": "E{}",
            "fb1": "F{}",
            "dptw1": "G{}",
            "gplus": "H{}",
        }
        self.us_media = {
            "tw1": "C{}",
            "tw2": "E{}",
            "fb1": "D{}",
        }


    def get_document(self):
        regex = "\d{1,2}\/\d{1,2}\/[APap][mM][0-9]?"
        document = docx.Document(self.file)
        doctext = ""
        for para in document.paragraphs:
            if not "SM Posts" in para.text:
                doctext += para.text
        pattern = re.split(regex, doctext)
        dates = re.findall(regex, doctext)
        count = 0
        for item in pattern:
            if item != "":
                try:
                    dates[count]
                except Exception as e:
                    break
                post = Post(text=item, date=dates[count], image=None)
                self.posts.append(post)
                count += 1
        print("Found {} Posts".format(len(self.posts)))


    def get_docx(self):
        filename = ""
        ls = listdir(self.workdir)
        for file in ls:
            if ".docx" in file and not "~$" in file and not ".~lock" in file:
                filename = file
        f = open(self.workdir + filename, 'rb')
        return f


    def set_images(self, posts):
        ls = listdir(self.workdir)
        for post in posts:
            images = []
            date = post.date.replace("/", "-")
            if date[-1:] == "-":
                date = date[:-1]

            regex = date + post.ampm + "[^0-9]"
            image = self.search_filename(regex, ls)

            if image:
                post.image = image
                #ls.remove(image)
            else:
                regex = date + "-\d{1,2}"
                image = self.search_filename(regex, ls)
                post.image = image


    def search_filename(self, regex, files):
        pattern = re.compile(regex)
        images = []
        for file in files:
            if file.find(".jpg") != -1 and pattern.search(file):
                images.append(file)
        if len(images) == 1:
            return images[0]
        elif len(images) == 0:
            return None
        else:
            return images




    def queue_post(self, post):
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.ehlo()
        server.starttls()
        server.login(read_conf("username"), read_conf("password"))

        msg = MIMEMultipart()
        msg['From'] = read_conf("from_email")
        msg['To'] = self.email
        msg['Subject'] = post.text

        if post.profile:
            text = "@s {}\n@p {}".format(post.service, post.profile)
        else:
            text = "@s {}".format(post.service, post.profile)
        msg.attach(MIMEText(text))

        if post.image:
            with open(self.workdir + post.image, 'rb') as f:
                part = MIMEApplication(f.read(), Name=post.image)
                part['Content-Disposition'] = 'attachment; filename="{}"'.format(post.image)
                msg.attach(part)
        #server.sendmail(read_conf("from_email"), [self.email], msg.as_string())
        #print("---")
        print(colored("Message sent to ", "magenta") + str(self.email))
        #print(colored("From: ", "magenta") + msg['From'])
        #print(colored("To: ", "magenta") + msg['To'])
        #print(colored("Subject: \n", "magenta") + msg['Subject'])
        #print(colored("Image: ", "magenta") + str(post.image))
        #print(colored("Body: \n", "magenta") + text)


    def get_sheets(self, sheetid, worksheet_name):
        scope = ['https://spreadsheets.google.com/feeds']
        credentials = ServiceAccountCredentials.from_json_keyfile_name(read_conf("google_key"), scope)
        gc = gspread.authorize(credentials)
        sheet = gc.open_by_key(sheetid)
        worksheet = sheet.worksheet(worksheet_name)
        return worksheet


    def get_all_social(self, worksheet, country):
        posts = {}
        if country == "ca":
            media = self.media.items()
            start = 4
        elif country == "us":
            media = self.us_media.items()
            start = 6
        for social, value in media:
            posts[social] = self.get_column(worksheet, value, get_ampm(social), start)
        return posts


    def get_column(self, worksheet, column, ampm, start):
        result = " "
        count = start
        posts = []
        while result != "":
            date = worksheet.acell("A{}".format(count)).value
            # This is currently printing out a lot of things, ignoring it for now
            result = worksheet.acell(column.format(count)).value
            date += ampm
            count += 1
            if result != "":
                p = Post(date=date, text=result)
                posts.append(p)
        print("\n")
        return posts

    def write_posts(self, posts):
        dates = self.worksheet
        pass




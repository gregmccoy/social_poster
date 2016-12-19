import datetime
import configparser

config = configparser.ConfigParser()

def read_conf(option):
    config.read("/home/gregmccoy/Programming/social/social/social.conf")
    value = config['DEFAULT'][option]
    return(value)

def format_date(date, dateformat):
    date = datetime.datetime.strptime(date, dateformat)
    return date

def get_ampm(media):
    return {
        "tw1": "am",
        "tw2": "pm",
        "tw3": "pm",
        "fb1": "am",
        "dptw1": "am",
        "gplus": "am",
    }[media]

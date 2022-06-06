import re
import scrapy
import smtplib
import ssl
import datetime as dt

from email.message import EmailMessage


class VikPlovdivSpider(scrapy.Spider):
    name = "vik_plovdiv"
    start_urls = ["https://vik.bg/maintenance/"]

    month_names_dict = {
        "January": "Януари",
        "February": "Февруари",
        "March": "Март",
        "April": "Април",
        "May": "Май",
        "June": "Юни",
        "July": "Юли",
        "August": "Август",
        "September": "Септември",
        "October": "Октомври",
        "November": "Ноември",
        "December": "Декември",
    }
    today_date = dt.datetime.today().strftime("%d-%B-%Y")
    today_date_list = today_date.split("-")
    today_date_string_bg = (
        f"{today_date_list[0]}"
        f"-{month_names_dict[today_date_list[1]]}"
        f"-{today_date_list[2]}"
    )

    def parse(self, response, **kwargs):
        all_publications = response.xpath(
            '//li[contains(text(), "убликувано на")]'
        )
        if not all_publications or len(all_publications) != 5:
            raise Exception(
                "Error getting publications. Either no "
                "publications found or publications are more or "
                "less than 5. Check the website for changes and "
                "adjust the xpath."
            )
        date_regex = re.compile(r"(?i)Публикувано на:?\s?(\d{1,2}\w+-\d{2,4})")
        date_check_regex = [
            re.search(date_regex, x.get()) for x in all_publications
        ]
        if not date_check_regex:
            raise Exception("Date formatting issue. Check the regex.")
        articles_h3_check = response.xpath(
            '//section[@id="contentMain"]//h3//a'
        )
        if not articles_h3_check:
            raise Exception(
                "No h3/a elements found in the articles section. "
                "Check the website for changes."
            )
        alerts = []
        for i in range(len(all_publications)):
            current_publication = all_publications[i]
            if self.today_date_string_bg in current_publication.get():
                text = current_publication.xpath(
                    f".//parent::ul/preceding-sibling::*"
                    f"[count(preceding-sibling::h3)={i+1}]"
                    f"/text()[normalize-space()]"
                ).getall()
                text = ". ".join(text).replace("\xa0", " ").replace("  ", " ")
                alerts.append(text)
                if i + 1 == len(all_publications):
                    next_page = response.xpath('//a[text()="›"]/@href').get()
                    if not next_page:
                        raise Exception(
                            "Next page button not found. Check the xpath."
                        )
                    yield response.follow(url=next_page)
        if alerts:
            self.send_email_with_alerts(alerts)

    def send_email_with_alerts(self, alerts):
        msg = EmailMessage()
        msg.set_content("\n\n".join(alerts))
        msg["Subject"] = "New ViK Plovdiv Alerts"
        msg["From"] = "python_auto@abv.bg"
        msg["To"] = "nikolay_skomorohov@protonmail.com"
        context = ssl.create_default_context()
        server = smtplib.SMTP_SSL("smtp.abv.bg", 465, context=context)
        server.set_debuglevel(2)
        server.login("python_auto@abv.bg", "huskarl2006")
        server.send_message(msg)
        server.quit()

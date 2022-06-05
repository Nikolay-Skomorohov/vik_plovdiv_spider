import re
import viberbot.api
import scrapy
import datetime as dt


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
    # today_date_string_bg = "30-Май-2022"

    bot_configuration = viberbot.BotConfiguration(
        name="vikplovdivbot",
        avatar="https://vik.bg/data/images/vik.png",
        auth_token="4f4cfec6d3e7dd66-38be5214efbf8b77-6db059f03ed8b3fa",
    )
    viber = viberbot.Api(bot_configuration=bot_configuration)

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
        for i in range(len(all_publications)):
            current_publication = all_publications[i]
            if self.today_date_string_bg in current_publication.get():
                text = current_publication.xpath(
                    f".//parent::ul/preceding-sibling::*"
                    f"[count(preceding-sibling::h3)={i+1}]"
                    f"/text()[normalize-space()]"
                ).getall()
                text = ". ".join(text).replace("\xa0", " ").replace("  ", " ")
                print(text)
                if i + 1 == len(all_publications):
                    next_page = response.xpath('//a[text()="›"]/@href').get()
                    if not next_page:
                        raise Exception(
                            "Next page button not found. Check the xpath."
                        )
                    yield response.follow(url=next_page)
